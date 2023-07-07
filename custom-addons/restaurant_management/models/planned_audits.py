from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression

from . import queries

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

    @api.constrains('jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sept', 'oct', 'nov', 'dec')
    def _check_max_min_values(self):
        for record in self:
            if not all([getattr(record, f) >= 0 and getattr(record, f) <= 10 for f in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sept', 'oct', 'nov', 'dec']]):
                raise ValidationError(
                    _('Max and min values for audit counts are 0 and 10 correspondingly!'))

    def get_number_of_audits(self, date_start, date_end,
                             restaurant_id=None, restaurant_network_id=None,
                             restaurant_ids=None, restaurant_network_ids=None):
        if restaurant_ids is None:
            restaurant_ids = []
        if restaurant_network_ids is None:
            restaurant_network_ids = []

        PlannedAudits = self.env["restaurant_management.planned_audits"]
        year_start = date_start.year
        month_start = date_start.month
        year_end = date_end.year
        month_end = date_end.month

        domain = []
        if restaurant_id:
            domain = expression.AND([
                [('restaurant_id', '=', restaurant_id)],
                domain
            ])
        if restaurant_network_id:
            domain = expression.AND([
                [("restaurant_id.restaurant_network_id", "=", restaurant_network_id)],
                domain
            ])

        if len(restaurant_ids):
            domain = expression.AND([
                [('restaurant_id', 'in', restaurant_ids)],
                domain
            ])
        if len(restaurant_network_ids):
            domain = expression.AND([
                [("restaurant_id.restaurant_network_id", "in", restaurant_network_ids)],
                domain
            ])

        year_list = list(range(year_start, year_end+1))
        counts = []
        for y_i, y in enumerate(year_list):
            planned_audit_ids = PlannedAudits.search(expression.AND([
                [("year", "=", y)],
                domain
            ]))
            if y_i == 0 and year_start == year_end:
                a = [sum(planned_audit_ids.mapped(month))
                     for month in MONTHS[month_start-1:month_end]]
            elif y_i == 0:
                a = [sum(planned_audit_ids.mapped(month))
                     for month in MONTHS[month_start-1:]]
            elif y_i == len(year_list)-1:
                a = [sum(planned_audit_ids.mapped(month))
                     for month in MONTHS[:month_end]]
            else:
                a = [sum(planned_audit_ids.mapped(month)) for month in MONTHS]
            counts += a
        return counts

    def get_monthly_planned_audit_count(self, year, restaurant_ids):
        self.env.cr.execute(
            queries.planned_audit_count_by_year,
            [tuple(restaurant_ids), year]
        )
        planned_audits = self.env.cr.fetchall()
        return planned_audits and planned_audits[0][1:]
        

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
