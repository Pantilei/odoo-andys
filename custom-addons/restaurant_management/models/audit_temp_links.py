import random
import string
from datetime import datetime

from odoo import api, fields, models


class AuditTempLinks(models.Model):
    _name = "restaurant_management.audit_temp_links"
    _description = "Audit Temporary links"
    _rec_name = "access_token"

    restaurant_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant",
        index=True
    )
    access_token = fields.Char(required=True, index=True)
    valid_until = fields.Datetime(required=True)
    is_active = fields.Boolean(
        compute="_compute_is_active"
    )

    link = fields.Char(
        compute="_compute_link"
    )

    @api.depends("valid_until")
    def _compute_is_active(self):
        for record in self:
            record.is_active = record.valid_until >= datetime.utcnow()

    @api.depends("access_token")
    def _compute_link(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for record in self:
            record.link = f"{base_url}/audits/{record.access_token}"

    def generate_access_token(self):
        return "".join(random.choices(string.ascii_letters + string.digits, k=12))
