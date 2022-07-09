# -*- coding: utf-8 -*-

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
