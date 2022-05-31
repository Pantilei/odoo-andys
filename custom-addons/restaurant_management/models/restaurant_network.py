# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RestaurantNetwork(models.Model):
    _name = 'restaurant_management.restaurant_network'
    _description = 'Restaurant Network'

    name = fields.Char(required=True)
    description = fields.Text(
        string="Description"
    )
