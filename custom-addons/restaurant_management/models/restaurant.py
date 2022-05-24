# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Restaurant(models.Model):
    _name = 'restaurant_management.restaurant'
    _description = 'Restaurants'

    name = fields.Char()
    description = fields.Text()
