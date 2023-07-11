import json
from calendar import monthrange
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

from . import queries
from .chart_builder import ChartBuilder

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


class RestaurantNetworkReport(models.Model):
    _name = "restaurant_management.restaurant_network_report"
    _description = "Restaurant Network Report"
    _order = "create_date desc"

    @api.depends("restaurant_network_id", "report_year", "report_month")
    def _compute_name(self):
        for record in self:
            if record.restaurant_network_id and record.report_year and record.report_month:
                record.name = f"{record.restaurant_network_id.name}-{record.report_year}-{record.report_month}"
            else:
                record.name = ""

    name = fields.Char(
        compute="_compute_name"
    )

    restaurant_network_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant_network",
        string="Restaurant Network"
    )

    report_year = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        string="Year of Report",
        default=lambda self: str(date.today().year)
    )

    previous_report_year = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        compute="_compute_previous_report_year",
        string="Previous Year of Report"
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

    logo = fields.Image(related='restaurant_network_id.logo', readonly=True)

    actual_audit_count = fields.Integer()
    planned_audit_count = fields.Integer()

    monthly_fault_count_per_audit = fields.Text()
    monthly_fault_count_per_audit_chart = fields.Text(
        compute="_compute_monthly_fault_count_per_audit_chart"
    )

    yearly_fault_count_per_audit_by_check_list_category = fields.Text()
    yearly_fault_count_per_audit_by_check_list_category_chart = fields.Text(
        compute="_compute_yearly_fault_count_per_audit_by_check_list_category_chart"
    )

    restaurant_rating_within_department = fields.Text()
    restaurant_rating_within_department_table = fields.Text(
        compute="_compute_restaurant_rating_within_department_table"
    )

    top_rating = fields.Text()
    top_rating_table = fields.Text(
        compute="top_rating_table"
    )

    anti_top_rating = fields.Text()
    anti_top_rating_table = fields.Text(
        compute="_compute_anti_top_rating_table"
    )

    top_faults_within_department = fields.Text()
    top_faults_within_department_charts = fields.Text(
        compute="_compute_top_faults_within_department_charts"
    )

    top_faults = fields.Text()
    top_faults_table = fields.Text(
        compute="_compute_top_faults_table"
    )
    
    summary = fields.Text(string="Summary")


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            print("Create Vals: ", vals)
            computed_values = self._get_computed_fields(
                vals["report_month"], 
                vals["report_year"], 
                vals["restaurant_network_id"],
            )
            vals.update(computed_values)
        return super(RestaurantNetworkReport, self).create(vals_list)

    def write(self, vals):
        computed_values = self._get_computed_fields(
            vals.get("report_month", self.report_month), 
            vals.get("report_year", self.report_year), 
            vals.get("restaurant_network_id", self.restaurant_network_id.id)
        )
        vals.update(computed_values)
        print("Vals: ", vals)
        return super(RestaurantNetworkReport, self).write(vals)

    def _get_computed_fields(self, report_month, report_year, restaurant_network_id):
        restaurant_ids = self.env["restaurant_management.restaurant"].search([
            ("restaurant_network_id", "=", restaurant_network_id)
        ])

        actual_audit_count = self._compute_actual_audit_count(report_month, report_year, restaurant_network_id)
        planned_audit_count = self._compute_planned_audit_count(report_month, report_year, restaurant_network_id)


        monthly_fault_count_per_audit = self._compute_monthly_fault_count_per_audit(
            report_year, restaurant_ids.ids
        )
        yearly_fault_count_per_audit_by_check_list_category = self._compute_yearly_fault_count_per_audit_by_check_list_category(
            report_year, restaurant_ids.ids
        )
        restaurant_rating_within_department = self._compute_restaurant_rating_within_department(report_month, report_year, restaurant_network_id)
        top_rating = self._compute_top_rating(report_month, report_year, restaurant_network_id)
        anti_top_rating = self._compute_anti_top_rating(report_month, report_year, restaurant_network_id)
        top_faults_within_department = self._compute_top_faults_within_department(
            report_month, report_year, restaurant_network_id
        )
        top_faults = self._compute_top_faults(report_month, report_year, restaurant_network_id)

        return {
            "actual_audit_count": actual_audit_count,
            "planned_audit_count": planned_audit_count,
            "monthly_fault_count_per_audit": monthly_fault_count_per_audit,
            "yearly_fault_count_per_audit_by_check_list_category": yearly_fault_count_per_audit_by_check_list_category,
            "restaurant_rating_within_department": restaurant_rating_within_department,
            "top_rating": top_rating,
            "anti_top_rating": anti_top_rating,
            "top_faults_within_department": top_faults_within_department,
            "top_faults": top_faults
        }
    
    def _compute_actual_audit_count(self, report_month, report_year, restaurant_network_id):
        date_start, date_end = _compute_date_start_end(report_year, report_month)
        return self.env["restaurant_management.restaurant_audit"].search_count([
            ("restaurant_id.restaurant_network_id", "=", restaurant_network_id),
            ("audit_date", ">=", date_start),
            ("audit_date", "<=", date_end),
        ])
    
    def _compute_planned_audit_count(self, report_month, report_year, restaurant_network_id):
        date_start, date_end = _compute_date_start_end(report_year, report_month)
        return self.env["restaurant_management.planned_audits"].get_number_of_audits(
            date_start, date_end, restaurant_network_id=restaurant_network_id
        )[0]
    
    def _compute_monthly_fault_count_per_audit(self, report_year, restaurant_ids):
        chart_date_start = date(year=int(report_year), month=1, day=1)
        chart_date_end = date(year=int(report_year), month=12, day=31)
        self.env.cr.execute(
            queries.faults_by_months_in_restaurant_network_query, 
            [chart_date_start.isoformat(), chart_date_end.isoformat(), tuple(restaurant_ids)]
        )
        faults_by_month_this_year = {d[0]: d[1] for d in self.env.cr.fetchall()}

        self.env.cr.execute(
            queries.audits_by_months_in_restaurant_network_query,
            [chart_date_start.isoformat(), chart_date_end.isoformat(), tuple(restaurant_ids)]
        )
        audits_by_month_this_year = {d[0]: d[1] for d in self.env.cr.fetchall()}

        year_this = [
            round(faults_by_month_this_year.get(int(month_data[0]), 0) / audits_by_month_this_year.get(int(month_data[0]), 1), ndigits=2)
            for month_data in MONTHS
        ]

        chart_date_start = date(year=int(report_year) - 1, month=1, day=1)
        chart_date_end = date(year=int(report_year) - 1, month=12, day=31)
        self.env.cr.execute(
            queries.faults_by_months_in_restaurant_network_query, 
            [chart_date_start.isoformat(), chart_date_end.isoformat(), tuple(restaurant_ids)]
        )
        faults_by_month_year_before = {d[0]: d[1] for d in self.env.cr.fetchall()}

        self.env.cr.execute(
            queries.audits_by_months_in_restaurant_network_query,
            [chart_date_start.isoformat(), chart_date_end.isoformat(), tuple(restaurant_ids)]
        )
        audits_by_month_year_before = {d[0]: d[1] for d in self.env.cr.fetchall()}
        year_before = [
            round(faults_by_month_year_before.get(int(month_data[0]), 0) / audits_by_month_year_before.get(int(month_data[0]), 1), ndigits=2)
            for month_data in MONTHS
        ]
        return json.dumps({
            int(report_year): year_this,
            int(report_year)-1: year_before,
        })
    
    def _compute_yearly_fault_count_per_audit_by_check_list_category(
            self, report_year, restaurant_ids
        ):
        chart_date_start = date(year=int(report_year), month=1, day=1)
        chart_date_end = date(year=int(report_year), month=12, day=31)
        audit_count = self.env["restaurant_management.restaurant_audit"].search_count([
            ("state", "=", 'confirm'),
            ("audit_date", ">=", chart_date_start),
            ("audit_date", "<=", chart_date_end),
            ("restaurant_id", "in", restaurant_ids)
        ])
        self.env.cr.execute(
            queries.yearly_faults_by_check_list_category, 
            [chart_date_start.isoformat(), chart_date_end.isoformat(), tuple(restaurant_ids)]
        )
        faults_by_check_list_category_this_year = {
            "check_list_category_ids": [],
            "check_list_category_names": [],
            "check_list_category_fault_counts": [],
        }
        for d in self.env.cr.fetchall():
            faults_by_check_list_category_this_year["check_list_category_ids"].append(d[0])
            faults_by_check_list_category_this_year["check_list_category_names"].append(d[1])
            faults_by_check_list_category_this_year["check_list_category_fault_counts"].append(
                round(d[2]/(audit_count or 1), 2)
            )

        chart_date_start = date(year=int(report_year) - 1, month=1, day=1)
        chart_date_end = date(year=int(report_year) - 1, month=12, day=31)
        audit_count = self.env["restaurant_management.restaurant_audit"].search_count([
            ("audit_date", ">=", chart_date_start),
            ("audit_date", "<=", chart_date_end),
            ("restaurant_id", "in", restaurant_ids)
        ])
        faults_by_check_list_category_year_before = {
            "check_list_category_ids": [],
            "check_list_category_names": [],
            "check_list_category_fault_counts": [],
        }
        self.env.cr.execute(
            queries.yearly_faults_by_check_list_category, 
            [chart_date_start.isoformat(), chart_date_end.isoformat(), tuple(restaurant_ids)]
        )
        for d in self.env.cr.fetchall():
            faults_by_check_list_category_year_before["check_list_category_ids"].append(d[0])
            faults_by_check_list_category_year_before["check_list_category_names"].append(d[1])
            faults_by_check_list_category_year_before["check_list_category_fault_counts"].append(
                round(d[2]/(audit_count or 1), 2)
            )
        
        return json.dumps({
            int(report_year): faults_by_check_list_category_this_year,
            int(report_year)-1: faults_by_check_list_category_year_before,
        })
    
    def _compute_restaurant_rating_within_department(self, report_month, report_year, restaurant_network_id):
        return "{}"
    
    def _compute_top_rating(self, report_month, report_year, restaurant_network_id):
        return "{}"
    
    def _compute_anti_top_rating(self, report_month, report_year, restaurant_network_id):
        return ""
    
    def _compute_top_faults_within_department(self, report_month, report_year, restaurant_network_id):
        return "{}"

    def _compute_top_faults(self, report_month, report_year, restaurant_network_id):
        return "{}"

    @api.depends("report_year")
    def _compute_previous_report_year(self):
        for record in self:
            record.previous_report_year = record.report_year and str(int(record.report_year) - 1)

    @api.depends("write_date")
    def _compute_monthly_fault_count_per_audit_chart(self):
        for record in self:
            data = json.loads(record.monthly_fault_count_per_audit)
            label1 = record.report_year
            label2 = str(int(record.report_year) - 1)
            y1 = data[label1]
            y2 = data[label2]
            max_value = max(max(y1), max(y2))
            upper_limit = round( max_value*1.1)
            months = [m[1] for m in self._fields['report_month']._description_selection(self.env)]            
            record.monthly_fault_count_per_audit_chart = ChartBuilder(height=300).build_year_to_year_line_chart(
                months, y1, y2, label1, label2, upper_limit
            )

    @api.depends("write_date")
    def _compute_yearly_fault_count_per_audit_by_check_list_category_chart(self):
        for record in self:
            data = json.loads(record.yearly_fault_count_per_audit_by_check_list_category)
            label1, label2 = tuple(data.keys())
            x1 = data[label1]["check_list_category_fault_counts"]
            x2 = data[label2]["check_list_category_fault_counts"]
            
            record.yearly_fault_count_per_audit_by_check_list_category_chart = ChartBuilder(
                height=len(data[label1]["check_list_category_names"])*40
            ).build_grouped_horizontal_bar_chart(
                data[label1]["check_list_category_names"], x1, x2, label1, label2
            )

    @api.depends("write_date")
    def _compute_restaurant_rating_within_department_table(self):
        for record in self:
            record.restaurant_rating_within_department_table = ""

    @api.depends("write_date")
    def _compute_anti_top_rating_table(self):
        for record in self:
            record.anti_top_rating_table = ""

    @api.depends("write_date")
    def _compute_top_faults_within_department_charts(self):
        for record in self:
            record.top_faults_within_department_charts = ""
    
    @api.depends("write_date")
    def _compute_top_faults_table(self):
        for record in self:
            record.top_faults_table = ""