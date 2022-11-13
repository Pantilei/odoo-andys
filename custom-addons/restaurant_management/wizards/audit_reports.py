from numpy import dstack
from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY
from calendar import monthrange

import json

from ..tools import short_date


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


class AuditReports(models.TransientModel):
    _name = "restaurant_management.audit_reports"
    _description = "Wizard tof audit reports"

    def _default_month_end(self):
        return str((date.today()).month)

    def _default_month_start(self):
        return str((date.today() + relativedelta(months=-5)).month)

    def _get_default_restaurant_networks(self):
        return self.env["restaurant_management.restaurant_network"].search([])

    name = fields.Char(
        string="Name",
        default="Print PDF of report"
    )

    audits_table_json = fields.Text(
        compute="_compute_audits_table_json"
    )

    restaurant_network_ids = fields.Many2many(
        comodel_name="restaurant_management.restaurant_network",
        relation="restaurant_management_audit_reports_rel",
        string="Restaurant Networks",
        default=_get_default_restaurant_networks,
        required=True
    )

    year_start = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        string="Year Start",
        default=lambda self: str(
            (date.today() + relativedelta(months=-5)).year)
    )

    month_start = fields.Selection(
        string="Month Start",
        selection=MONTHS,
        default=_default_month_start,
    )

    year_end = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        string="Date End",
        default=lambda self: str(date.today().year),
    )

    month_end = fields.Selection(
        selection=MONTHS,
        default=_default_month_end,
        string="Month End"
    )

    @api.depends("restaurant_network_ids", "year_start", "year_end", "month_start", "month_end")
    def _compute_audits_table_json(self):
        RestaurantAudit = self.env["restaurant_management.restaurant_audit"]
        for record in self:
            date_start = date(
                year=int(record.year_start),
                month=int(record.month_start),
                day=1
            )
            date_end = date(
                year=int(record.year_end),
                month=int(record.month_end),
                day=monthrange(year=int(record.year_end),
                               month=int(record.month_end))[1]
            )
            audit_counts = RestaurantAudit.get_audit_counts_per_month(
                date_start, date_end, restaurant_network_ids=record.restaurant_network_ids.ids)
            month_range = record._get_month_range(date_start, date_end)
            record.audits_table_json = json.dumps(
                {"months": month_range, **audit_counts})

    def _get_month_range(self, date_start, date_end):
        return [short_date(r) for r in rrule(MONTHLY, dtstart=date_start, until=date_end)]
