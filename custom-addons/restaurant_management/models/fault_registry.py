# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import logging
import traceback


requests.packages.urllib3.util.connection.HAS_IPV6 = False

_logger = logging.getLogger(__name__)


class FaultRegistry(models.Model):
    _name = 'restaurant_management.fault_registry'
    _description = 'Fault Registry'
    _order = "id desc"
    _rec_name = "check_list_id"

    @api.depends('check_list_category_id')
    def _compute_no_fault_check_list_category(self):
        for record in self:
            if record.check_list_category_id:
                record.no_fault_check_list_category = record.check_list_category_id.no_fault_category
            else:
                record.no_fault_check_list_category = False

    state = fields.Selection(selection=[
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancel'),
    ], default="confirm")

    restaurant_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant",
        string="Restaurant",
        compute="_compute_restaurant",
        store=True
    )
    fault_date = fields.Date(
        compute="_compute_fault_date",
        store=True
    )
    restaurant_audit_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant_audit",
        ondelete="cascade"
    )
    check_list_category_id = fields.Many2one(
        comodel_name="restaurant_management.check_list_category",
        required=True
    )
    no_fault_check_list_category = fields.Boolean(
        compute="_compute_no_fault_check_list_category"
    )
    check_list_id = fields.Many2one(
        comodel_name="restaurant_management.check_list",
        string="Check List"
    )
    responsible_id = fields.Many2one(
        comodel_name="res.users",
        compute="_compute_responsible",
        store=True,
        string="Expert DKK"
    )

    comment = fields.Text(
        string="Expert DKK Comment"
    )

    director_comment = fields.Text(
        string="Restaurant Director Comment"
    )

    check_list_category_responsible_comment = fields.Text(
        string="Fault Category Responsible Comment"
    )

    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        string="Photos"
    )

    @api.onchange("check_list_category_id")
    def onchange_check_list_category(self):
        self.check_list_id = False

    @api.depends("restaurant_audit_id")
    def _compute_responsible(self):
        for record in self:
            if record.restaurant_audit_id:
                record.responsible_id = record.restaurant_audit_id.responsible_id.id

    @api.depends("restaurant_audit_id")
    def _compute_restaurant(self):
        for record in self:
            if record.restaurant_audit_id:
                record.restaurant_id = record.restaurant_audit_id.restaurant_id.id

    @api.depends("restaurant_audit_id")
    def _compute_fault_date(self):
        for record in self:
            if record.restaurant_audit_id:
                record.fault_date = record.restaurant_audit_id.audit_date

    def cancel(self):
        self.write({
            "state": "cancel"
        })

    def confirm(self):
        self.write({
            "state": "confirm"
        })

    @api.model_create_multi
    def create(self, values):
        recs = super().create(values)
        telegram_token = self.env["ir.config_parameter"].sudo(
        ).get_param("telegram_token")
        if telegram_token:
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            for rec in recs:
                chat_id = rec.check_list_category_id.telegram_chat_id
                if chat_id:
                    params = {
                        "chat_id": chat_id,
                        "text": self._construct_message(rec),
                        "parse_mode": "html"
                    }
                    try:
                        r = requests.get(url=url, params=params, timeout=5)
                        _logger.info(f"Telegram message sent: {r.json()}")
                        print(self._construct_message(rec))
                    except Exception as ex:
                        _logger.error(traceback.format_exc())
                        _logger.warning("Telegram message couldnt be sent!")
        return recs

    def _construct_message(self, rec):
        message = ""
        if rec.responsible_id.name:
            message += f"<b>{rec.responsible_id.name}</b> создал ошибку."
        if rec.check_list_category_id.name:
            message += f"\n\n<b>Категория:</b> {rec.check_list_category_id.name}. "
        if rec.check_list_id.description:
            message += f"\n\n<b>Ошибка:</b> {rec.check_list_id.description}"
        if rec.restaurant_id.name:
            message += f"\n\n<b>Ресторан:</b> {rec.restaurant_id.name}"

        base_url = self.env["ir.config_parameter"].sudo(
        ).get_param("web.base.url")
        menu_id = self.env.ref("restaurant_management.fault_registry").id
        action_id = self.env.ref(
            "restaurant_management.fault_registry_action").id
        if base_url and menu_id and action_id:
            url = f"{base_url}/web#id={rec.id}&menu_id={menu_id}&action={action_id}&model=restaurant_management.fault_registry&view_type=form"
            message += f"\n\n<a href=\"{url}\">Посмотреть!</a>"

        return message

    @api.model
    def _populate_data(self):
        print("Populate data", self)
        # self.create({

        # })
