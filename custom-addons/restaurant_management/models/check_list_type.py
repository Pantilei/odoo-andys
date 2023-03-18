from odoo import api, fields, models


class CheckListType(models.Model):
    _name = "restaurant_management.check_list_type"
    _description = "Check List Type"

    name = fields.Char()

