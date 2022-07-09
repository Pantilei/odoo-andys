from odoo import api, models, fields, _
from datetime import date


MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
          'jul', 'aug', 'sept', 'oct', 'nov', 'dec']


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
        default=4,
    )
    feb = fields.Integer(
        string="February",
        default=4,
    )
    mar = fields.Integer(
        string="March",
        default=4,
    )
    apr = fields.Integer(
        string="April",
        default=4,
    )
    may = fields.Integer(
        string="May",
        default=4,
    )
    jun = fields.Integer(
        string="June",
        default=4
    )
    jul = fields.Integer(
        string="July",
        default=4
    )
    aug = fields.Integer(
        string="August",
        default=4,

    )
    sept = fields.Integer(
        string="September",
        default=4,
    )
    oct = fields.Integer(
        string="October",
        default=4,
    )
    nov = fields.Integer(
        string="November",
        default=4,
    )
    dec = fields.Integer(
        string="December",
        default=4,
    )

    def get_number_of_audits(self, year=None, restaurant_id=None, restaurant_network_id=None):
        if not year:
            year = date.today().year
        if restaurant_id:
            planned_audit_id = self.env["restaurant_management.planned_audits"].search([
                ("restaurant_id", "=", restaurant_id),
                ("year", "=", year)
            ], limit=1)
            return [getattr(planned_audit_id, month) for month in MONTHS]

        if restaurant_network_id:
            planned_audit_ids = self.env["restaurant_management.planned_audits"].search([
                ("restaurant_id.restaurant_network_id", "=", restaurant_network_id),
                ("year", "=", year)
            ])
            return [sum(planned_audit_ids.mapped(month)) for month in MONTHS]

        planned_audit_ids = self.env["restaurant_management.planned_audits"].search([
            ("year", "=", year)
        ])
        return [sum(planned_audit_ids.mapped(month)) for month in MONTHS]

    def create_yearly_planned_amount(self):
        year = date.today().year
        for restaurant_id in self.env["restaurant_management.restaurant"].search([]):
            planned_audit_id = self.env["restaurant_management.planned_audits"].search([
                ("restaurant_id", "=", restaurant_id.id),
                ("year", "=", year)
            ], limit=1)
            if not planned_audit_id:
                self.env["restaurant_management.planned_audits"].create({
                    "restaurant_id": restaurant_id.id,
                    "year": year,
                })
