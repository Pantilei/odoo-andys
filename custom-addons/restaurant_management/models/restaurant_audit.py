# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class RestaurantAudit(models.Model):
    _name = 'restaurant_management.restaurant_audit'
    _description = 'Restaurant Audit'
    _order = "id desc"

    @api.depends("restaurant_id", "audit_date")
    def _compute_name(self):
        for record in self:
            record.name = f"{record.restaurant_id.name or _('New')}--{record.audit_date or ''}--{record.id or ''}"

    name = fields.Char(
        compute="_compute_name",
        store=True
    )
    restaurant_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant",
        string="Restaurant"
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

    # def _compute_fault_registry_json(self):
    #     pass

    # def _inverse_fault_registry_json(self):
    #     pass

    # @api.onchange("fault_registry_json")
    # def on_change_of_fault_registry_json(self):
    #     print(self.fault_registry_ids, "\n", self.fault_registry_json)
