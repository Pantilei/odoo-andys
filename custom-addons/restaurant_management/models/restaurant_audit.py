# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from datetime import datetime, timedelta
from lxml import etree


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
        string="From"
    )
    audit_end_time = fields.Float(
        string="To"
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
            if self.user_has_groups("restaurant_management.group_restaurant_management_dkk_manager,restaurant_management.group_restaurant_management_manager"):
                record.available_for_edit = True
            else:
                create_date_week_day = record.create_date.weekday()
                delta = timedelta(hours=24)
                # Do not consider weekends if created in friday
                if create_date_week_day == 4:
                    delta = timedelta(hours=24*3)
                record.available_for_edit = (
                    record.create_date + delta) > datetime.now()

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
