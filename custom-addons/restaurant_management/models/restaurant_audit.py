# -*- coding: utf-8 -*-

import enum
from odoo import models, fields, api, _, registry
from odoo.osv import expression

from datetime import datetime, timedelta, date
from dateutil.rrule import rrule, MONTHLY

import requests
import traceback
import logging
import threading

_logger = logging.getLogger(__name__)


class RestaurantAudit(models.Model):
    _name = 'restaurant_management.restaurant_audit'
    _description = 'Restaurant Audit'
    _order = "id desc"

    @api.depends("restaurant_id", "audit_date")
    def _compute_name(self):
        for record in self:
            record.name = f"{record.restaurant_id.name or _('New')}--{record.audit_date or ''}--{record.id or ''}"

    @api.depends("restaurant_id")
    def _compute_restaurant_directors(self):
        for record in self:
            if record.restaurant_id:
                record.restaurant_director_ids = record.restaurant_id.director_ids.ids
            else:
                record.restaurant_director_ids = False

    name = fields.Char(
        compute="_compute_name",
        store=True
    )
    restaurant_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant",
        string="Restaurant"
    )
    restaurant_network_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant_network",
        string="Restaurant Network",
        related="restaurant_id.restaurant_network_id",
        readonly=False,
        store=True
    )
    restaurant_director_ids = fields.Many2many(
        comodel_name="res.users",
        string="Restaurant Directors",
        compute="_compute_restaurant_directors"
    )

    responsible_id = fields.Many2one(
        comodel_name="res.users",
        default=lambda self: self.env.user.id,
        readonly=True,
        string="Expert DKK"
    )

    audit_date = fields.Date(
        default=lambda self: fields.Datetime.today(),
    )
    audit_start_time = fields.Float(
        string="From",
        group_operator=False
    )
    audit_end_time = fields.Float(
        string="To",
        group_operator=False
    )

    fault_registry_ids = fields.One2many(
        comodel_name="restaurant_management.fault_registry",
        inverse_name="restaurant_audit_id"
    )

    available_for_edit = fields.Boolean(
        compute="_compute_available_for_edit",
        string="Availabe for Change"
    )

    @api.depends("create_date")
    def _compute_available_for_edit(self):
        for record in self:
            if self.user_has_groups("restaurant_management.group_restaurant_management_dkk_manager,restaurant_management.group_restaurant_management_manager,restaurant_management.group_restaurant_management_dkk_manager"):
                record.available_for_edit = True
            elif record.create_date:
                create_date_week_day = record.create_date.weekday()
                delta = timedelta(hours=24)
                # Do not consider weekends if created in friday
                if create_date_week_day == 4:
                    delta = timedelta(hours=24*3)
                record.available_for_edit = (
                    record.create_date + delta) > datetime.now()
            else:
                record.available_for_edit = True

    def save_form_data(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Saved!",
                'type': 'info',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            },
        }

    def save_and_create_new(self):
        return self.sudo().env.ref("restaurant_management.restaurant_audit_inline_form_action").read()[0]

    @api.model_create_multi
    def create(self, values):
        recs = super().create(values)
        self._cr.commit()

        th = threading.Thread(
            target=self._send_telegram_message, args=(recs.ids,))
        th.daemon = True
        th.start()

        return recs

    def _send_telegram_message(self, rec_ids):
        cr = registry(self._cr.dbname).cursor()
        self = self.with_env(self.env(cr=cr))
        recs = self.env["restaurant_management.restaurant_audit"].search([
            ('id', 'in', rec_ids)
        ])
        if telegram_token := self.env["ir.config_parameter"].sudo().get_param("telegram_token"):
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            for rec in recs:
                check_list_category_ids = rec.fault_registry_ids.mapped(
                    "check_list_category_id")

                for check_list_category_id in check_list_category_ids:
                    if chat_id := check_list_category_id.telegram_chat_id:
                        fault_ids = rec.fault_registry_ids.filtered(
                            lambda r: r.check_list_category_id.id == check_list_category_id.id)
                        params = {
                            "chat_id": chat_id,
                            "text": self._construct_message(rec, fault_ids),
                            "parse_mode": "html"
                        }
                        try:
                            t_response = requests.get(
                                url=url, params=params, timeout=5)
                            _logger.info(
                                f"Telegram message sent: {t_response.json()}")
                        except Exception as ex:
                            _logger.error(traceback.format_exc())
                            _logger.warning(
                                "Telegram message couldn't be sent!")
        cr.commit()
        cr.close()

    def _construct_message(self, record, fault_ids):
        message = ""
        if record.responsible_id.name:
            message += f"<b>{record.responsible_id.name}</b> создал ошибку(и)."
        if record.restaurant_id.name:
            message += f"\n<b>Ресторан:</b> {record.restaurant_id.name}"
        if fault_ids[0].check_list_category_id.name:
            message += f"\n<b>Категория:</b> {fault_ids[0].check_list_category_id.name}. \n"
        for rec in fault_ids:
            if rec.check_list_id.description:
                base_url = self.env["ir.config_parameter"].sudo(
                ).get_param("web.base.url")
                menu_id = self.env.ref(
                    "restaurant_management.fault_registry").id
                action_id = self.env.ref(
                    "restaurant_management.fault_registry_action").id
                if base_url and menu_id and action_id:
                    url = f"{base_url}/web#id={rec.id}&menu_id={menu_id}&action={action_id}&model=restaurant_management.fault_registry&view_type=form"
                    message += f"\n<a href=\"{url}\"><b>Ошибка: </b>{rec.check_list_id.description}</a>"
                else:
                    message += f"\n<b>Ошибка: </b>{rec.check_list_id.description}"

            message += "\n"

        return message

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(RestaurantAudit, self).fields_view_get(
    #         view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

    #     if view_type == "form" and not self.available_for_change:
    #         doc = etree.XML(res['arch'])
    #         form = doc.xpath("//form")[0]
    #         form.attrib["edit"] = "0"

    #         xarch, xfields = self.env['ir.ui.view'].postprocess_and_fields(
    #             doc, model=self._name)

    #         res['arch'] = xarch
    #         res['fields'] = xfields
    #     return res

    @api.model
    def get_audit_counts_per_month(self, date_start, date_end,
                                   restaurant_id=None, restaurant_network_id=None):
        RestaurantAudit = self.env["restaurant_management.restaurant_audit"]
        domain = [
            ('audit_date', '>=', date_start),
            ('audit_date', '<=', date_end),
        ]
        if restaurant_id:
            domain = expression.AND([
                [("restaurant_id", "=", restaurant_id)],
                domain
            ])
        if restaurant_network_id:
            domain = expression.AND([
                [("restaurant_id.restaurant_network_id", "=", restaurant_network_id)],
                domain
            ])
        audit_count_per_month = RestaurantAudit.read_group(
            domain=domain,
            fields=['restaurant_id'],
            groupby=['audit_date:month'],
        )
        date_range_monthly = list(
            rrule(MONTHLY, dtstart=date_start, until=date_end))
        audit_counts = [0 for _ in range(len(date_range_monthly))]
        # months = []
        for index, d in enumerate(date_range_monthly):
            for row in audit_count_per_month:
                row_date = datetime.strptime(
                    row["__range"]["audit_date"]["from"], "%Y-%m-%d")
                if row_date.year == d.year and row_date.month == d.month:
                    audit_counts[index] = row["audit_date_count"]

        return {
            "actual": audit_counts,
            "planned": self.env["restaurant_management.planned_audits"].get_number_of_audits(
                date_start, date_end, restaurant_id=restaurant_id,
                restaurant_network_id=restaurant_network_id
            )
        }
