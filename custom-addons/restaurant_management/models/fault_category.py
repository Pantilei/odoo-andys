# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FaultCategory(models.Model):
    _name = 'restaurant_management.fault_category'
    _description = 'Fault Registry'

    name = fields.Char(required=True)
