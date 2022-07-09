from odoo import api, models, fields, _
from datetime import date


MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']


class PlannedAudits(models.Model):
    _name = "restaurant_management.planned_audits"
    _description = "Number of planned audits in restaurant per month"
    _sql_constraints = [
        ('restaurant_year_uniq', 'unique (restaurant_id,year)',
         'One year definition per restaurant is allowed!')
    ]

    def _get_default_current_year(self):
        return date.today().year

    year = fields.Integer(default=_get_default_current_year)
    restaurant_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant"
    )

    jan = fields.Integer(
        string="January",
        default=0,
    )
    feb = fields.Integer(
        string="February",
        default=0,
    )
    mar = fields.Integer(
        string="March",
        default=0,
    )
    apr = fields.Integer(
        string="April",
        default=0,
    )
    may = fields.Integer(
        string="May",
        default=0,
    )
    jun = fields.Integer(
        string="June",
        default=0
    )
    jul = fields.Integer(
        string="July",
        default=0
    )
    aug = fields.Integer(
        string="August",
        default=0,

    )
    sept = fields.Integer(
        string="September",
        default=0,
    )
    oct = fields.Integer(
        string="October",
        default=0,
    )
    nov = fields.Integer(
        string="November",
    )
    dec = fields.Integer(
        string="December",
        default=0,
    )

    def get_number_of_audits(self, restaurant_id, year=None):
        if not year:
            year = date.today().year
        planned_audit_id = self.env["restaurant_management.planned_audits"].search([
            ("restaurant_id", "=", restaurant_id),
            ("year", "=", year)
        ], limit=1)
        if not planned_audit_id:
            planned_audit_id = self.env["restaurant_management.planned_audits"].create({
                "restaurant_id": restaurant_id,
                "year": year
            })

        return [getattr(planned_audit_id, month) for month in MONTHS]
