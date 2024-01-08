import json
from calendar import monthrange
from datetime import date

from dateutil.relativedelta import relativedelta
from dateutil.rrule import MONTHLY, rrule
from odoo import _, api, fields, models

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

    def _default_date_end(self):
        d = date.today() + relativedelta(months=-1)
        return date(year=d.year, month=d.month, day=monthrange(d.year, d.month)[1])

    def _default_date_start(self):
        d = date.today() + relativedelta(months=-1)
        return date(year=d.year, month=d.month, day=1)

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

    date_start = fields.Date(
        string="Date Start",
        default=_default_date_start
    )
    date_end = fields.Date(
        string="Date End",
        default=_default_date_end
    )

    @api.depends("restaurant_network_ids", "date_start", "date_end")
    def _compute_audits_table_json(self):
        RestaurantAudit = self.env["restaurant_management.restaurant_audit"]
        for record in self:
            audit_counts = RestaurantAudit.get_audit_counts_per_month(
                record.date_start, record.date_end, restaurant_network_ids=record.restaurant_network_ids.ids)
            month_range = record._get_month_range(record.date_start, record.date_end)
            record.audits_table_json = json.dumps(
                {"months": month_range, **audit_counts})

    def _get_month_range(self, date_start, date_end):
        return [short_date(r) for r in rrule(MONTHLY, dtstart=date_start.replace(day=1), until=date_end.replace(day=1))]
