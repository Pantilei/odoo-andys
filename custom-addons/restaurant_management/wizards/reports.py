from odoo import models, fields, api, _
from datetime import date


MONTHS = [
    ("1", _("Jan")),
    ("2", _("Feb")),
    ("3", _("Mar")),
    ("4", _("Apr")),
    ("5", _("May")),
    ("6", _("Jun")),
    ("7", _("Jul")),
    ("8", _("Aug")),
    ("9", _("Sept")),
    ("10", _("Oct")),
    ("11", _("Nov")),
    ("12", _("Dec")),
]


class Reports(models.TransientModel):
    _name = "restaurant_management.reports_wizard"
    _description = "Wizard to print the reports"

    name = fields.Char(
        string="Name",
        default="Print PDF of report"
    )

    report = fields.Selection(selection=[
        ("restaurants", "Report of Restaurants"),
        ("departaments", "Report of Departaments"),
    ],
        default="restaurants",
        required=True
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
    month = fields.Selection(
        selection=MONTHS,
        default=lambda self: str(date.today().month),
        string="Month"
    )

    def print_report(self):
        if self.report == "restaurants":
            data = {
                "restaurant_network_id": self.restaurant_network_id.id,
                "year": self.year
            }
            return self.env.ref("restaurant_management.action_restaurants_report")\
                .report_action(self, data=data)

        if self.report == "departaments":
            data = {
                "restaurant_network_id": self.restaurant_network_id.id,
                "year": self.year,
                "month": self.month,
            }
            return self.env.ref("restaurant_management.action_departaments_report")\
                .report_action(self, data=data)
