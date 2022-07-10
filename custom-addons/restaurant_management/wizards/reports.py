import re
from odoo import models, fields, api, _
from datetime import date


class Reports(models.TransientModel):
    _name = "restaurant_management.reports_wizard"
    _description = "Wizard to print the reports"

    name = fields.Char(
        string="Name",
        default="Print PDF of report"
    )
    restaurant_network_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant_network",
        string="Restaurant Network"
    )
    year = fields.Selection(selection=[
        (str(year), str(year)) for year in range(1999, 2049, 1)
    ],
        default=lambda self: str(date.today().year),
        string="Year",
        required=True
    )

    def print_report(self):
        data = {
            "restaurant_network_id": self.restaurant_network_id.id,
            "year": self.year
        }
        return self.env.ref("restaurant_management.action_general_report")\
            .report_action(self, data=data)
