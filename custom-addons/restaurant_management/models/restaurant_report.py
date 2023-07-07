import json
from calendar import monthrange
from datetime import date

import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

from .queries import (
    restaurant_rating_by_audit_type_query,
    restaurant_rating_within_network_query,
)

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


def _compute_date_start_end(report_year, report_month):
    year=int(report_year)
    month=int(report_month)
    date_start = date(year=year, month=month, day=1)
    date_end = date(year=year, month=month, day=monthrange(year, month)[1])

    return date_start, date_end

def _get_restaurant_rating(fault_counts_to_restaurants, restaurant_id):
    """
    fault_counts_to_restaurants:
    [
        (15, [16, 36], ['АП26', 'ЛП18']), 
        (16, [5], ['АП11']), 
        (17, [1], ['АП1']), 
        (18, [4, 19], ['АП9', 'АП30']), 
        (22, [6], ['АП12']), 
        (25, [31], ['ЛП11'])
    ]
    """
    rating = 0
    for fault_count_to_restaurants in fault_counts_to_restaurants:
        rating += 1
        if restaurant_id in fault_count_to_restaurants[1]:
            break
    return rating


class RestaurantReport(models.Model):
    _name = "restaurant_management.restaurant_report"
    _description = "Restaurant Report"
    

    @api.depends("restaurant_id", "report_year", "report_month")
    def _compute_name(self):
        for record in self:
            if record.restaurant_id and record.report_year and record.report_month:
                record.name = f"{record.restaurant_id.name}-{record.report_year}-{record.report_month}"
            else:
                record.name = ""

    name = fields.Char(
        compute="_compute_name"
    )

    restaurant_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant",
        string="Restaurant"
    )

    report_year = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        string="Year of Report",
        default=lambda self: str(date.today().year)
    )
    report_month = fields.Selection(
        selection=MONTHS,
        string="Report Month",
        default=lambda self: str(
            (date.today() + relativedelta(months=-1)).month),
        readonly=False
    )

    responsible_id = fields.Many2one(
        comodel_name="res.users",
        default=lambda self: self.env.user.id,
        string="Composed by"
    )

    logo = fields.Image(related='restaurant_id.restaurant_network_id.logo', readonly=True)

    restaurant_rating_within_network = fields.Char(
        compute="_compute_restaurant_rating_within_network",
        store=True
    )

    restaurant_rating_by_audit_type_data = fields.Text(
        compute="_compute_restaurant_rating_by_audit_type_data",
        store=True
    )

    restaurant_rating_within_department_data = fields.Text(
        compute="_compute_restaurant_rating_within_department_data",
        store=True
    )

    restaurant_directors = fields.Many2many(related="restaurant_id.director_ids")

    audit_count_by_audit_type = fields.Text(
        compute="_compute_audit_count_by_audit_type",
        store=True
    )

    fault_count_per_audit = fields.Integer(
        compute="_compute_fault_count_per_audit",
        store=True
    )
    

    fault_count_monthly_data = fields.Text(
        compute="_compute_fault_count_monthly_data",
        store=True
    )
    fault_count_monthly_chart = fields.Text(
        compute="_compute_fault_count_monthly_chart",
        store=True
    )
    fault_count = fields.Integer(
        compute="_compute_fault_count",
        string="Fault Count",
        store=True
    )
    fault_count_comment = fields.Text(
        compute="_compute_fault_count_comment",
        store=True
    )


    severe_fault_count = fields.Integer(
        compute="_compute_fault_count",
        string="Fault Count",
        store=True
    )
    sever_fault_count_comment = fields.Text(
        compute="_compute_fault_count_comment",
        store=True
    )
    severe_fault_count_monthly_data = fields.Text(
        compute="_compute_fault_count_monthly_data",
        store=True
    )
    severe_fault_count_monthly_chart = fields.Text(
        compute="_compute_fault_count_monthly_chart",
        store=True
    )


    top_violations_data = fields.Text(
        string="Top Violations",
        compute="_compute_top_violations",
        store=True
    )

    taken_measures = fields.Text(string="Taken Measures")
    summary = fields.Text(string="Summary")


    @api.depends("report_year", "report_month", "restaurant_id")
    def _compute_restaurant_rating_within_network(self):
        for record in self:
            if not record.report_month or not record.report_year or not record.restaurant_id:
                record.restaurant_rating_within_network = 0
                continue
            
            date_start, date_end = _compute_date_start_end(record.report_year, record.report_month)
            self.env.cr.execute(
                restaurant_rating_within_network_query, 
                [date_start.isoformat(), date_end.isoformat()]
            )
            result = self.env.cr.fetchall()
            record.restaurant_rating_within_network = _get_restaurant_rating(
                result, record.restaurant_id.id
            )

    @api.depends("report_year", "report_month", "restaurant_id")
    def _compute_restaurant_rating_by_audit_type_data(self):
        for record in self:
            if not record.report_month or not record.report_year or not record.restaurant_id:
                record.restaurant_rating_by_audit_type_data = "{}"
                continue

            date_start, date_end = _compute_date_start_end(record.report_year, record.report_month)
            restaurant_rating_by_audit_type_data = []
            for check_list_type_id in self.env["restaurant_management.check_list_type"].search([]):
                self.env.cr.execute(
                    restaurant_rating_by_audit_type_query, 
                    [date_start.isoformat(), date_end.isoformat(), check_list_type_id.id]
                )
                result = self.env.cr.fetchall()
                restaurant_rating_by_audit_type_data.append([
                    check_list_type_id.id,
                    check_list_type_id.name,
                    _get_restaurant_rating(result, record.restaurant_id.id)
                ])
            record.restaurant_rating_by_audit_type_data = json.dumps(
                restaurant_rating_by_audit_type_data
            )
    
    @api.depends("report_year", "report_month", "restaurant_id")
    def _compute_restaurant_rating_within_department_data(self):
        for record in self:
            if not record.report_month or not record.report_year or not record.restaurant_id:
                record.restaurant_rating_within_department_data = "{}"
                continue

            date_start, date_end = _compute_date_start_end(record.report_year, record.report_month)
            restaurant_rating_within_department_data = []
            for check_list_category_id in self.env["restaurant_management.check_list_category"].search([]):
                # self.env.cr.execute(
                #     restaurant_rating_within_department_query, 
                #     [date_start.isoformat(), date_end.isoformat(), check_list_category_id.id]
                # )
                result = self.env.cr.fetchall()
                restaurant_rating_within_department_data.append([
                    check_list_category_id.id,
                    check_list_category_id.name,
                    _get_restaurant_rating(result, record.restaurant_id.id)
                ])
            record.restaurant_rating_within_department_data = json.dumps(
                restaurant_rating_within_department_data
            )

    @api.depends("report_year", "report_month", "restaurant_id")
    def _compute_audit_count_by_audit_type(self):
        for record in self:
            record.audit_count_by_audit_type = 0

    @api.depends("report_year", "report_month", "restaurant_id")
    def _compute_fault_count_per_audit(self):
        for record in self:
            record.fault_count_per_audit = 0

    @api.depends("report_year", "report_month", "restaurant_id")
    def _compute_fault_count(self):
        for record in self:
            record.fault_count = 0
            record.severe_fault_count = 0
    
    @api.depends("report_year", "report_month", "restaurant_id")
    def _compute_fault_count_comment(self):
        for record in self:
            record.fault_count_comment = "На половину меньше чем в прошлом месяце"
            record.sever_fault_count_comment = "Меньше на 1 чем в прошлом месяце"

    @api.depends("report_year", "report_month", "restaurant_id")
    def _compute_fault_count_monthly_data(self):
        for record in self:
            record.fault_count_monthly_data = "{}"
            record.severe_fault_count_monthly_data = "{}"

    @api.depends("report_year", "report_month", "restaurant_id")
    def _compute_fault_count_monthly_chart(self):
        for record in self:
            record.fault_count_monthly_data = "{}"
            record.severe_fault_count_monthly_chart = "{}"

    @api.depends("report_year", "report_month", "restaurant_id")
    def _compute_top_violations(self):
        for record in self:
            record.top_violations_data = "{}"