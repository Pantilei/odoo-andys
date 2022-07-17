from odoo import models, fields, api, _
from datetime import date, datetime, timedelta


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

    # def _default_date_start(self):
    #     d = date.today() - timedelta(days=365)
    #     return date(year=d.year, month=d.month, day=1)

    # def _default_date_end(self):
    #     d = date.today()
    #     return date(year=d.year, month=d.month, day=1)

    name = fields.Char(
        string="Name",
        default="Print PDF of report"
    )

    report = fields.Selection(selection=[
        ("general_report_by_audit_of_restaurants",
         "General Report by Audit of Restaurants"),
        ("departaments", "Report of Departaments"),
    ],
        default="general_report_by_audit_of_restaurants",
        # required=True
    )

    year = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        string="Year of Report",
        default=lambda self: str(date.today().year)
    )

    month = fields.Selection(
        string="Month of Report",
        selection=MONTHS,
        default=lambda self: str(date.today().month - 1),
    )

    year_start = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        string="Year Start",
        default=lambda self: str(date.today().year - 1)
    )

    month_start = fields.Selection(
        string="Month Start",
        selection=MONTHS,
        default=lambda self: str(date.today().month - 1),
    )

    year_end = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        string="Date End",
        default=lambda self: str(date.today().year)
    )

    month_end = fields.Selection(
        selection=MONTHS,
        default=lambda self: str(date.today().month - 1),
        string="Month End"
    )

    # restaurant_network_id = fields.Many2one(
    #     comodel_name="restaurant_management.restaurant_network",
    #     string="Restaurant Network"
    # )

    def print_report(self):
        if self.report == "general_report_by_audit_of_restaurants":
            data = {
                # "restaurant_network_id": self.restaurant_network_id.id,
                "year": self.year,
                "month": self.month,
                "year_start": self.year_start,
                "year_end": self.year_end,
                "month_start": self.month_start,
                "month_end": self.month_end,
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
