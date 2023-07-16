import json
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

from . import queries
from .chart_builder import ChartBuilder
from .tools import compute_date_start_end, compute_restaurant_ratings

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
        string="Restaurant Network",
        required=True
    )

    report_year = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        string="Year of Report",
        default=lambda self: str(date.today().year),
        required=True
    )

    previous_report_year = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        compute="_compute_previous_report_year",
        string="Previous Year of Report",
        required=True
    )

    report_month = fields.Selection(
        selection=MONTHS,
        string="Report Month",
        default=lambda self: str(
            (date.today() + relativedelta(months=-1)).month),
        required=True
    )

    responsible_id = fields.Many2one(
        comodel_name="res.users",
        default=lambda self: self.env.user.id,
        string="Composed by",
        required=True
    )

    relative_fault_count_on_department_ids = fields.Many2many(
        comodel_name="restaurant_management.check_list_category",
        relation="restaurant_management_res_net_rep_check_l_categ_rel",
        required=True
    )

    restaurant_rating_within_department_ids = fields.Many2many(
        comodel_name="restaurant_management.check_list_category",
        relation="restaurant_management_res_net_rep_rating_in_deps_rel",
        required=True,
    )

    top_within_department_ids = fields.Many2many(
        comodel_name="restaurant_management.check_list_category",
        relation="restaurant_management_res_net_rep_top_deps_rel",
        required=True
    )

    logo = fields.Image(related='restaurant_network_id.logo', readonly=True)

    actual_audit_count = fields.Integer()
    planned_audit_count = fields.Integer()

    monthly_fault_count_per_audit = fields.Text()
    monthly_fault_count_per_audit_chart = fields.Text(
        compute="_compute_monthly_fault_count_per_audit_chart"
    )

    relative_fault_count_per_department = fields.Text()
    relative_fault_count_per_department_chart = fields.Text(
        compute="_compute_relative_fault_count_per_department_chart"
    )

    restaurant_rating_within_department = fields.Text()
    restaurant_rating_within_department_table = fields.Text(
        compute="_compute_restaurant_rating_within_department_table"
    )

    restaurants_rating = fields.Text()
    top_rating_table = fields.Text(
        compute="_compute_rating_tables_html"
    )
    anti_top_rating_table = fields.Text(
        compute="_compute_rating_tables_html"
    )

    top_faults = fields.Text()
    top_faults_table = fields.Text(
        compute="_compute_top_faults_table"
    )
    
    summary = fields.Text(string="Summary")


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            computed_values = self._get_computed_fields(
                vals["report_month"], 
                vals["report_year"], 
                vals["restaurant_network_id"],
                vals["relative_fault_count_on_department_ids"][0][2],
                vals["restaurant_rating_within_department_ids"][0][2],
                vals["top_within_department_ids"][0][2],
            )
            vals.update(computed_values)
        return super(RestaurantNetworkReport, self).create(vals_list)

    def write(self, vals):
        if "relative_fault_count_on_department_ids" in vals:
            relative_fault_count_on_department_ids = vals["relative_fault_count_on_department_ids"][0][2]
        else:
            relative_fault_count_on_department_ids = self.relative_fault_count_on_department_ids.ids

        if "restaurant_rating_within_department_ids" in vals:
            restaurant_rating_within_department_ids = vals["restaurant_rating_within_department_ids"][0][2]
        else:
            restaurant_rating_within_department_ids = self.restaurant_rating_within_department_ids.ids

        if "top_within_department_ids" in vals:
            top_within_department_ids = vals["top_within_department_ids"][0][2]
        else:
            top_within_department_ids = self.top_within_department_ids.ids

        computed_values = self._get_computed_fields(
            vals.get("report_month", self.report_month), 
            vals.get("report_year", self.report_year), 
            vals.get("restaurant_network_id", self.restaurant_network_id.id),
            relative_fault_count_on_department_ids,
            restaurant_rating_within_department_ids,
            top_within_department_ids,
        )
        vals.update(computed_values)
        return super(RestaurantNetworkReport, self).write(vals)

    def _get_computed_fields(
            self, 
            report_month, 
            report_year, 
            restaurant_network_id,
            relative_fault_count_on_department_ids, 
            restaurant_rating_within_department_ids,
            top_within_department_ids
        ):
        restaurant_ids = self.env["restaurant_management.restaurant"].search([
            ("restaurant_network_id", "=", restaurant_network_id)
        ])

        actual_audit_count = self._compute_actual_audit_count(report_month, report_year, restaurant_network_id)
        planned_audit_count = self._compute_planned_audit_count(report_month, report_year, restaurant_network_id)

        monthly_fault_count_per_audit = self._compute_monthly_fault_count_per_audit(
            report_year, restaurant_ids.ids
        )
        relative_fault_count_per_department = self._compute_relative_fault_count_per_department(
            report_month, report_year, restaurant_ids.ids, relative_fault_count_on_department_ids
        )
        restaurant_rating_within_department = self._compute_restaurant_rating_per_department(
            report_month, report_year, restaurant_ids.ids, restaurant_rating_within_department_ids
        )
        restaurants_rating = self._compute_restaurants_rating(
            report_month, report_year, restaurant_ids.ids, top_within_department_ids
        )
        top_faults = self._compute_top_faults(report_month, report_year, restaurant_ids.ids)

        return {
            "actual_audit_count": actual_audit_count,
            "planned_audit_count": planned_audit_count,
            "monthly_fault_count_per_audit": monthly_fault_count_per_audit,
            "relative_fault_count_per_department": relative_fault_count_per_department,
            "restaurant_rating_within_department": restaurant_rating_within_department,
            "restaurants_rating": restaurants_rating,
            "top_faults": top_faults
        }
    
    def _compute_actual_audit_count(self, report_month, report_year, restaurant_network_id):
        date_start, date_end = compute_date_start_end(report_year, report_month)
        return self.env["restaurant_management.restaurant_audit"].search_count([
            ("restaurant_id.restaurant_network_id", "=", restaurant_network_id),
            ("audit_date", ">=", date_start),
            ("audit_date", "<=", date_end),
        ])
    
    def _compute_planned_audit_count(self, report_month, report_year, restaurant_network_id):
        date_start, date_end = compute_date_start_end(report_year, report_month)
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
    
    def _compute_relative_fault_count_per_department(
            self, report_month, report_year, restaurant_ids, department_ids
        ):
        chart_date_start, chart_date_end = compute_date_start_end(report_year, report_month)
        audit_count = self.env["restaurant_management.restaurant_audit"].search_count([
            ("state", "=", 'confirm'),
            ("audit_date", ">=", chart_date_start),
            ("audit_date", "<=", chart_date_end),
            ("restaurant_id", "in", restaurant_ids)
        ])
        self.env.cr.execute(
            queries.yearly_faults_by_check_list_category, 
            [
                chart_date_start.isoformat(), 
                chart_date_end.isoformat(), 
                tuple(restaurant_ids),
                tuple(department_ids),
            ]
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

        chart_date_start, chart_date_end = compute_date_start_end(int(report_year) - 1, report_month)
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
            [
                chart_date_start.isoformat(), 
                chart_date_end.isoformat(), 
                tuple(restaurant_ids),
                tuple(department_ids),
            ]
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
    
    def _compute_restaurants_rating(self, report_month, report_year, restaurant_ids, department_ids):
        date_start, date_end = compute_date_start_end(report_year, report_month)
        self.env.cr.execute(
            queries.fault_counts_by_restaurants_in_departments_query,
            [
                date_start.isoformat(), 
                date_end.isoformat(),
                tuple(restaurant_ids),
                tuple(department_ids),
                tuple(restaurant_ids)
            ]
        )
        faults_per_restaurant = self.env.cr.fetchall()

        self.env.cr.execute(
            queries.restaurant_audit_count_query,
            [
                date_start.isoformat(), 
                date_end.isoformat(),
                tuple(restaurant_ids)
            ]
        )
        audits_per_restaurant = self.env.cr.fetchall()
        return json.dumps(compute_restaurant_ratings(faults_per_restaurant, audits_per_restaurant))

    def _compute_restaurant_rating_per_department(self, report_month, report_year, restaurant_ids, department_ids):
        result = []
        for department_id in self.env["restaurant_management.check_list_category"].browse(department_ids):
            result.append({
                "department_id": department_id.id,
                "department_name": department_id.name,
                "ratings": json.loads(self._compute_restaurants_rating(
                        report_month, report_year, restaurant_ids, department_id.ids
                    ))
                })
        return json.dumps(result)
    
    def _compute_top_faults(self, report_month, report_year, restaurant_ids):
        date_start, date_end = compute_date_start_end(report_year, report_month)
        self.env.cr.execute(
            queries.top_faults_by_restaurants_query,
            [date_start.isoformat(), date_end.isoformat(), tuple(restaurant_ids)]
        )
        return json.dumps([{
            "department_id": row[0],
            "department_name": row[1],
            "check_list_id": row[2],
            "check_list_name": row[3],
            "fault_count": row[4]
            } for row in self.env.cr.fetchall()
        ])

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
    def _compute_relative_fault_count_per_department_chart(self):
        for record in self:
            data = json.loads(record.relative_fault_count_per_department)
            label1, label2 = tuple(data.keys())
            x1 = data[label1]["check_list_category_fault_counts"]
            x2 = data[label2]["check_list_category_fault_counts"]
            
            record.relative_fault_count_per_department_chart = ChartBuilder(
                height=len(data[label1]["check_list_category_names"])*40
            ).build_grouped_horizontal_bar_chart(
                data[label1]["check_list_category_names"], x1, x2, label1, label2
            )

    @api.depends("write_date")
    def _compute_restaurant_rating_within_department_table(self):
        for record in self:
            restaurant_rating_within_department = json.loads(record.restaurant_rating_within_department)
            template = self.env.ref("restaurant_management.restaurant_network_report_restaurant_rating_per_department")
            record.restaurant_rating_within_department_table = template._render({
                "restaurant_rating_within_department": restaurant_rating_within_department
            })
    
    @api.depends("write_date")
    def _compute_rating_tables_html(self):
        for record in self:
            template = self.env.ref("restaurant_management.restaurant_network_report_restaurant_rating")
            restaurants_rating = json.loads(record.restaurants_rating)
            for restaurant_rating in restaurants_rating:
                restaurant_rating["restaurants"] = ", ".join(restaurant_rating["restaurant_names"])
            mean_index = round(len(restaurants_rating)/2)
            record.top_rating_table = template._render({
                "restaurant_ratings": restaurants_rating[:mean_index]
            })
            record.anti_top_rating_table = template._render({
                "restaurant_ratings": list(reversed(restaurants_rating[mean_index:]))
            })
    
    @api.depends("write_date")
    def _compute_top_faults_table(self):
        for record in self:
            top_faults = json.loads(record.top_faults)
            for top_fault in top_faults:
                top_fault["progress_bar"] = round(top_fault["fault_count"]/top_faults[0]["fault_count"], 4)*100
            template = self.env.ref("restaurant_management.report_top_faults_table")
            record.top_faults_table = template._render({"top_faults": top_faults})