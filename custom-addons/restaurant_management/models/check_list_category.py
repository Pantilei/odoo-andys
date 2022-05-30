# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CheckListCategory(models.Model):
    _name = 'restaurant_management.check_list_category'
    _description = 'Check List Category'

    name = fields.Char(required=True)
