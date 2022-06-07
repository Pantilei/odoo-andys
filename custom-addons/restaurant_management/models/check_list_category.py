# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CheckListCategory(models.Model):
    _name = 'restaurant_management.check_list_category'
    _description = 'Check List Category'

    name = fields.Char(required=True)

    telegram_chat_id = fields.Char(
        string="Telegram Chat Id",
        help="""
            To find the chat id make GET request to 
            https://api.telegram.org/bot{token}/getUpdates
            There you can find all chat_ids that this bot is currently used in.
        """
    )
