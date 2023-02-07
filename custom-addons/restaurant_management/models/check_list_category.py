# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CheckListCategory(models.Model):
    _name = 'restaurant_management.check_list_category'
    _description = 'Check List Category'
    _order = "sequence asc"

    name = fields.Char(required=True)

    sequence = fields.Integer(
        string="Sequence"
    )

    no_fault_category = fields.Boolean(
        string="No Fault Category",
        default=False
    )

    identificator = fields.Integer(
        string="Identificator"
    )

    telegram_chat_id = fields.Char(
        string="Telegram Chat Id",
        help="""
            To find the chat id make GET request to 
            https://api.telegram.org/bot{token}/getUpdates
            There you can find all chat_ids that this bot is currently used in.
        """
    )

    default_category = fields.Boolean(
        default=True,
        string="Is this category in default list?"
    )

    check_list_ids = fields.One2many(
        comodel_name="restaurant_management.check_list",
        inverse_name = "category_id",
        string="Check List"
    )
