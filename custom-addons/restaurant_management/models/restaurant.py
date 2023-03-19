# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import models, fields, api


class Restaurant(models.Model):
    _name = 'restaurant_management.restaurant'
    _description = 'Restaurants'

    name = fields.Char(
        required=True
    )
    restaurant_network_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant_network",
        string="Restaurant Network"
    )
    description = fields.Text()
    director_ids = fields.Many2many(
        comodel_name="res.users",
        string="Restaurant Directors"
    )

    country_id = fields.Many2one(
        comodel_name='res.country',
        string="Country"
    )
    city = fields.Char(
        string="City"
    )
    street = fields.Char(
        string="Street 1"
    )
    street2 = fields.Char(
        string="Street 2"
    )

    planned_audit_ids = fields.One2many(
        comodel_name="restaurant_management.planned_audits",
        inverse_name="restaurant_id",
        string="Planned Audits"
    )

    audit_temp_link_ids = fields.One2many(
        comodel_name="restaurant_management.audit_temp_links",
        inverse_name="restaurant_id",
        string="Links"
    )

    def generate_temp_audit_link(self):
        AuditTempLinks = self.env["restaurant_management.audit_temp_links"]
        AuditTempLinks.create({
            "restaurant_id": self.id,
            "access_token": AuditTempLinks.generate_access_token(),
            "valid_until": datetime.utcnow() + timedelta(hours=10)
        })