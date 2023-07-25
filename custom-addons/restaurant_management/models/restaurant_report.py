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


class RestaurantReport(models.Model):
    _name = "restaurant_management.restaurant_report"
    _description = "Restaurant Report"
    _order = "create_date desc"
    
    @api.depends("restaurant_id", "report_year", "report_month")
    def _compute_name(self):
        for record in self:
            if record.restaurant_id and record.report_year and record.report_month:
                record.name = f"{record.restaurant_id.name}-{record.report_year}-{record.report_month}"
            else:
                record.name = ""

    @api.depends("restaurant_id")
    def _compute_restaurant_directors(self):
        for record in self:
            if record.restaurant_id:
                record.director_ids = record.restaurant_id.director_ids.ids
            else:
                record.director_ids = False

    @api.onchange("restaurant_id")
    def _set_restaurant_network(self):
        self.restaurant_network_ids = self.restaurant_id.restaurant_network_id.ids

    name = fields.Char(
        compute="_compute_name"
    )

    restaurant_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant",
        required=True,
        string="Restaurant"
    )

    restaurant_network_ids = fields.Many2many(
        comodel_name="restaurant_management.restaurant_network",
        relation="restaurant_management_res_nets_to_res_rep",
        required=True,
        string="Restaurant Networks"
    )

    department_ids = fields.Many2many(
        comodel_name="restaurant_management.check_list_category",
        relation="restaurant_management_department_to_res_rep",
        required=True,
        string="Departments"
    )
    
    director_ids = fields.Many2many(
        comodel_name="res.users",
        compute="_compute_restaurant_directors",
        store=True,
        string="Directors"
    )

    report_year = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        string="Year of Report",
        default=lambda self: str(date.today().year),
        required=True
    )
    report_month = fields.Selection(
        selection=MONTHS,
        string="Report Month",
        default=lambda self: str(
            (date.today() + relativedelta(months=-1)).month),
        readonly=False,
        required=True
    )

    responsible_id = fields.Many2one(
        comodel_name="res.users",
        default=lambda self: self.env.user.id,
        string="Composed by",
        required=True
    )

    relative_monthly_fault_counts = fields.Text()
    relative_monthly_fault_counts_chart = fields.Text(
        compute="_compute_relative_monthly_fault_counts_chart"
    )

    audits_info = fields.Text()
    audits_info_table = fields.Text(
        compute="_compute_audits_info_table"
    )

    indicators = fields.Text()
    indicators_html = fields.Text(
        compute="_compute_indicators_html"
    )

    faults_per_department = fields.Text()
    faults_per_department_html = fields.Text(
        compute="_compute_faults_per_department_html"
    )

    top_faults = fields.Text()
    top_faults_chart = fields.Text(
        compute="_compute_top_faults_chart"
    )

    taken_measures = fields.Text(string="Taken Measures")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            computed_values = self._get_computed_fields(
                int(vals["report_month"]), 
                int(vals["report_year"]), 
                vals["restaurant_id"],
                vals["restaurant_network_ids"][0][2],
                vals["department_ids"][0][2]
            )
            vals.update(computed_values)
        return super(RestaurantReport, self).create(vals_list)

    def write(self, vals):
        if "restaurant_network_ids" in vals:
            restaurant_network_ids = vals["restaurant_network_ids"][0][2]
        else:
            restaurant_network_ids = self.restaurant_network_ids.ids

        if "department_ids" in vals:
            department_ids = vals["department_ids"][0][2]
        else:
            department_ids = self.department_ids.ids

        computed_values = self._get_computed_fields(
            int(vals.get("report_month", self.report_month)), 
            int(vals.get("report_year", self.report_year)), 
            int(vals.get("restaurant_id", self.restaurant_id.id)), 
            restaurant_network_ids,
            department_ids
        )
        vals.update(computed_values)
        return super(RestaurantReport, self).write(vals)

    def _get_computed_fields(self, report_month, report_year, restaurant_id, restaurant_network_ids, department_ids):
        restaurant_ids = self.env["restaurant_management.restaurant"].search([
            ("restaurant_network_id", "in", restaurant_network_ids)
        ]).ids
        absolute_monthly_fault_counts = self._compute_absolute_monthly_fault_counts(
            report_year, restaurant_id, department_ids
        )
        relative_monthly_fault_counts = self._compute_relative_monthly_fault_counts(
            report_year, restaurant_id, absolute_monthly_fault_counts
        )

        audits_info = self._compute_audits_info(report_month, report_year, restaurant_id)
        indicators = self._compute_indicators(report_month, report_year, restaurant_id, restaurant_ids, department_ids)
        faults_per_department = self._compute_faults_per_department(
            report_month, report_year, restaurant_id, department_ids
        )
        top_faults = self._compute_top_faults(report_month, report_year, restaurant_id, department_ids)

        return {
            "relative_monthly_fault_counts": relative_monthly_fault_counts,
            "audits_info": audits_info,
            "indicators": indicators,
            "faults_per_department": faults_per_department,
            "top_faults": top_faults 
        }
    
    def _compute_absolute_monthly_fault_counts(self, report_year, restaurant_id, department_ids):
        date_start_this_year = date(year=report_year, month=1, day=1).isoformat()
        date_end_this_year = date(year=report_year, month=12, day=31).isoformat()
        self.env.cr.execute(
            queries.faults_by_months_in_restaurants_in_departments_query,
            [date_start_this_year, date_end_this_year, (restaurant_id, ), tuple(department_ids)]
        )
        this_year_month_to_fault_count = {
            row[0]: row[1] for row in self.env.cr.fetchall()
        }

        date_start_prev_year = date(year=report_year-1, month=1, day=1).isoformat()
        date_end_prev_year = date(year=report_year-1, month=12, day=31).isoformat()
        self.env.cr.execute(
            queries.faults_by_months_in_restaurants_in_departments_query,
            [date_start_prev_year, date_end_prev_year, (restaurant_id, ), tuple(department_ids)]
        )
        prev_year_month_to_fault_count = {
            row[0]: row[1] for row in self.env.cr.fetchall()
        }

        return json.dumps({
            report_year: [this_year_month_to_fault_count.get(int(month[0]), 0) for month in MONTHS], 
            report_year-1: [prev_year_month_to_fault_count.get(int(month[0]), 0) for month in MONTHS]
        })

    def _compute_relative_monthly_fault_counts(
            self, report_year, restaurant_id, absolute_monthly_fault_counts
        ):
        date_start = date(year=report_year, month=1, day=1).isoformat()
        date_end = date(year=report_year, month=12, day=31).isoformat()
        self.env.cr.execute(
            queries.actual_audit_count_by_year,
            [(restaurant_id, ), date_start, date_end]
        )

        month_to_audit_count = {
            row[0]: row[1]
            for row in self.env.cr.fetchall()
        }
        this_year_actual_audit_count = [
            month_to_audit_count.get(int(month[0]), 0) for month in MONTHS
        ]

        date_start = date(year=report_year-1, month=1, day=1).isoformat()
        date_end = date(year=report_year-1, month=12, day=31).isoformat()
        self.env.cr.execute(
            queries.actual_audit_count_by_year,
            [(restaurant_id, ), date_start, date_end]
        )

        month_to_audit_count = {
            row[0]: row[1]
            for row in self.env.cr.fetchall()
        }
        prev_year_actual_audit_count = [
            month_to_audit_count.get(int(month[0]), 0) for month in MONTHS
        ]

        absolute_fault_counts = json.loads(absolute_monthly_fault_counts)
        return json.dumps({
            report_year-1: [
                round(fault_count/(audit_count or 1), 2) 
                for fault_count, audit_count in zip(absolute_fault_counts[str(report_year-1)], prev_year_actual_audit_count)
            ], 
            report_year: [
                round(fault_count/(audit_count or 1), 2) 
                for fault_count, audit_count in zip(absolute_fault_counts[str(report_year)], this_year_actual_audit_count)
            ]
        })
    
    def _compute_audits_info(self, report_month, report_year, restaurant_id):
        date_start, date_end = compute_date_start_end(report_year, report_month)
        audit_week_days = self.env['restaurant_management.restaurant_audit']._fields['audit_week_day']._description_selection(self.env)
        day_times = self.env['restaurant_management.restaurant_audit']._fields['day_time']._description_selection(self.env)
        result = []
        for audit in self.env["restaurant_management.restaurant_audit"].search([
            ("state", "=", "confirm"),
            ("restaurant_id", "=", restaurant_id),
            ("audit_date", ">=", date_start),
            ("audit_date", "<=", date_end),
        ]):
            audit_week_day_name = [r[1] for r in audit_week_days if r[0] == audit.audit_week_day]
            day_time_name = [r[1] for r in day_times if r[0] == audit.day_time]
            result.append({
                "id": audit.id,
                "audit_date": audit.audit_date.isoformat(),
                "week_day": audit.audit_week_day,
                "week_day_str": audit_week_day_name[0] if audit_week_day_name else '',
                "day_time": audit.day_time,
                "day_time_str": day_time_name[0] if day_time_name else '',
            })
        return json.dumps(result)

    def _compute_indicators(self, report_month, report_year, restaurant_id, restaurant_ids, department_ids):
        date_start, date_end = compute_date_start_end(report_year, report_month)
        sever_fault_count = self.env["restaurant_management.fault_registry"].search_count([
            ("restaurant_id", "=", restaurant_id),
            ("check_list_category_id", "in", department_ids),
            ("severe", "=", True),
            ("fault_date", ">=", date_start),
            ("fault_date", "<=", date_end),
        ])
        result = {
            "restaurant_rating": 0,
            "fault_count": 0,
            "fault_count_per_audit": 0,
            "sever_fault_count": sever_fault_count,
        }
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
        for restaurant_to_fault_count in faults_per_restaurant:
            if restaurant_to_fault_count[0] == restaurant_id:
                result["fault_count"] = restaurant_to_fault_count[2]

        self.env.cr.execute(
            queries.restaurant_audit_count_query,
            [
                date_start.isoformat(), 
                date_end.isoformat(),
                tuple(restaurant_ids)
            ]
        )
        audits_per_restaurant = self.env.cr.fetchall()
        for restaurant_to_audit_count in audits_per_restaurant:
            if restaurant_to_audit_count[0] == restaurant_id:
                result["fault_count_per_audit"] = round(
                    result["fault_count"]/restaurant_to_audit_count[1], 2
                )

        restaurant_ratings = compute_restaurant_ratings(faults_per_restaurant, audits_per_restaurant)
        for restaurant_rating in restaurant_ratings:
            if restaurant_id in restaurant_rating["restaurant_ids"]:
                result["restaurant_rating"] = f"{restaurant_rating['rating']} / {len(restaurant_ratings)}"

        return json.dumps(result)
    
    def _compute_faults_per_department(self, report_month, report_year, restaurant_id, department_ids):
        date_start, date_end = compute_date_start_end(report_year, report_month)
        check_list_category_ids = self.env["restaurant_management.check_list_category"].browse(department_ids)
        self.env.cr.execute(
            queries.fault_count_by_department_query,
            [
                date_start.isoformat(), 
                date_end.isoformat(),
                (restaurant_id, ),
                tuple(check_list_category_ids.ids)
            ]
        )

        check_list_category_to_fault_count = {
            check_list_category[0]: check_list_category[1]
        for check_list_category in self.env.cr.fetchall()}

        result = [{
                "check_list_category_id": check_list_category_id.id,
                "check_list_category_name": check_list_category_id.name,
                "fault_count": check_list_category_to_fault_count.get(check_list_category_id.id, 0),
            } for check_list_category_id in check_list_category_ids
        ]
        result.sort(key=lambda r: r["fault_count"], reverse=True)
        return json.dumps(result)

    def _compute_top_faults(self, report_month, report_year, restaurant_id, department_ids):
        start_date, end_date = compute_date_start_end(report_year, report_month)
        self.env.cr.execute(
            queries.top_violations_in_restaurant_query,
            [start_date.isoformat(), end_date.isoformat(), (restaurant_id, ), tuple(department_ids)]
        )
        return json.dumps([{
                "check_list_id": row[0],
                "check_list_name": row[1],
                "fault_count": row[2]
            } for row in reversed(self.env.cr.fetchall())
        ])
    
    @api.depends("write_date")
    def _compute_relative_monthly_fault_counts_chart(self):
        for record in self:
            data = json.loads(record.relative_monthly_fault_counts)
            label1 = record.report_year
            label2 = str(int(record.report_year) - 1)
            y1 = data[label1]
            y2 = data[label2]
            max_value = max(max(y1), max(y2))
            upper_limit = round(max_value*1.2, ndigits=2)
            months = [m[1] for m in self._fields['report_month']._description_selection(self.env)]            
            record.relative_monthly_fault_counts_chart = ChartBuilder(height=250).build_year_to_year_line_chart(
                months, y1, y2, label1, label2, upper_limit
            ) 

    @api.depends("write_date")
    def _compute_audits_info_table(self):
        for record in self:
            template = self.env.ref("restaurant_management.restaurant_report_audit_info_table")
            audits_info = json.loads(record.audits_info)
            record.audits_info_table = template._render({"audits": audits_info})
    
    @api.depends("write_date")
    def _compute_indicators_html(self):
        for record in self:
            template = self.env.ref("restaurant_management.restaurant_report_indicators")
            indicators = json.loads(record.indicators)
            record.indicators_html = template._render(indicators)

    @api.depends("write_date")
    def _compute_faults_per_department_html(self):
        for record in self:
            template = self.env.ref("restaurant_management.restaurant_report_faults_per_department")
            faults_per_department = json.loads(record.faults_per_department)
            for fault_per_department in faults_per_department:
                fault_per_department["width"] = round(
                    (fault_per_department["fault_count"] / (faults_per_department[0]["fault_count"] or 1))*100, 2
                )
            record.faults_per_department_html = template._render({
                "faults_per_department": faults_per_department
            })

    @api.depends("write_date")
    def _compute_top_faults_chart(self):
        for record in self:
            top_faults = json.loads(record.top_faults)
            x, y = [], []
            for fault in top_faults:
                if not fault["fault_count"]:
                    continue
                x.append(fault["fault_count"])
                y.append(fault["check_list_name"])
            record.top_faults_chart = ChartBuilder(height=(len(y) or 1)*40).build_horizontal_bar_chart(x, y)