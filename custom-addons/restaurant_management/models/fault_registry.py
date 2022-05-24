# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FaultRegistry(models.Model):
    _name = 'restaurant_management.fault_registry'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Fault Registry'
    _order = "id desc"

    name = fields.Char(
        compute="_compute_name"
    )
    state = fields.Selection(selection=[
        ('new', 'New'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancel'),
    ], default="new", tracking=True)

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
        comodel_name="restaurant_management.restaurant_audit"
    )
    fault_category_id = fields.Many2one(
        comodel_name="restaurant_management.fault_category",
        required=True
    )
    fault_id = fields.Many2one(
        comodel_name="restaurant_management.fault",
        required=True,
        string="Fault"
    )
    responsible_id = fields.Many2one(
        comodel_name="res.users",
        compute="_compute_responsible",
        store=True,
        string="Responsible"
    )

    comment = fields.Text(
        string="Comment"
    )

    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        string="Photos"
    )

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

    @api.depends('create_date')
    def _compute_name(self):
        for record in self:
            record.name = f"Fault {record.id}" if record.id else "New Fault"

    def confirm(self):
        self.write({
            "state": "confirm",
        })

    def cancel(self):
        self.write({
            "state": "cancel"
        })

    @api.model
    def _populate_data(self):
        print("Populate data", self)
        self.create({

        })
