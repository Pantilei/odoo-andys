# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CheckListCategory(models.Model):
    _name = 'restaurant_management.check_list_category'
    _description = 'Check List Category'
    _order = "sequence asc"

    name = fields.Char(required=True)

    sequence = fields.Integer(
        string="Sequence"
    )

    active = fields.Boolean(
        string="Archived",
        default=True
    )

    check_list_type_id = fields.Many2one(
        comodel_name="restaurant_management.check_list_type",
        # default=lambda self: self.env.ref("restaurant_management.qcd_check_list_type").id,
        string="Check List Type"
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

    response_type = fields.Selection(
        selection=[
            ("yes_no", "Yes/No"),
            ("notes", "Notes")
        ],
        default="yes_no",
        string="Response Type"
    )

    is_secret_guest_type = fields.Boolean(
        compute="_compute_is_secret_guest_type"
    )

    @api.depends("check_list_type_id")
    def _compute_is_secret_guest_type(self):
        for record in self:
            record.is_secret_guest_type = record.check_list_type_id == self.env.ref("restaurant_management.secret_guest_check_list_type")

    def archive_record(self):
        for record in self:
            record.active = False
    
    def unarchive_record(self):
        for record in self:
            record.active = True
