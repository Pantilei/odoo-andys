import json
from calendar import monthrange
from datetime import date, timedelta

import plotly.graph_objects as go
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

class DepartmentReport(models.Model):
    _name = "restaurant_management.department_report"
    _description = "Department Report"
    

    @api.depends("department_id", "report_year", "report_month")
    def _compute_name(self):
        for record in self:
            if record.department_id and record.report_year and record.report_month:
                record.name = f"{record.department_id.name}-{record.report_year}-{record.report_month}"
            else:
                record.name = ""

    name = fields.Char(
        compute="_compute_name"
    )

    department_id = fields.Many2one(
        comodel_name="restaurant_management.check_list_category",
        domain=[("no_fault_category", "=", False), ("default_category", "=", True)]
    )

    restaurant_network_ids = fields.Many2many(
        comodel_name="restaurant_management.restaurant_network",
        relation='restaurant_management_dep_report_res_network_rel',
        string="Restaurant Networks"
    )

    report_year = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        string="Year of Report",
        default=lambda self: str(date.today().year)
    )
    report_month = fields.Selection(
        string="Report Month",
        selection=MONTHS,
        default=lambda self: str((date.today() + relativedelta(months=-1)).month),
    )

    report_previous_month = fields.Selection(
        selection=MONTHS,
        string="Report Previous Month",
        readonly=True
    )

    responsible_id = fields.Many2one(
        comodel_name="res.users",
        default=lambda self: self.env.user.id,
        string="Responsible"
    )

    department_rating = fields.Char(readonly=True)
    relative_fault_count_comment = fields.Text(readonly=True)

    fault_count = fields.Integer(string="Fault Count", readonly=True)
    fault_count_percentage = fields.Float(string="Fault Count Percentage", readonly=True)
    relative_by_month_fault_count = fields.Integer(readonly=True)

    fault_count_chart_data = fields.Text(string="Chart Data", readonly=True)
    fault_count_chart = fields.Text(
        string='Fault Count Chart',
        compute='_compute_fault_count_chart',
        readonly=True
    )

    top_violations_data = fields.Text(
        string="Top Violations", 
        default="[]",
        readonly=True
    )
    top_violations_chart = fields.Text(
        string="Top Violations Chart",
        compute="_compute_top_violations_chart",
        readonly=True
    )

    restaurant_rating_within_department_data = fields.Text(
        readonly=True,
        default="[]"
    )
    mean_fault_count_per_restaurant = fields.Float(readonly=True)
    mean_fault_count_per_audit = fields.Float(readonly=True)

    taken_measures = fields.Text(string="Taken Measures")
    summary = fields.Text(string="Summary")


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            computed_values = self._get_computed_fields(
                vals["report_month"], 
                vals["report_year"], 
                vals["department_id"],
                vals["restaurant_network_ids"][0][2],
            )
            vals.update(computed_values)
        return super(DepartmentReport, self).create(vals_list)

    def write(self, vals):
        restaurant_network_ids = vals.get("restaurant_network_ids")
        computed_values = self._get_computed_fields(
            vals.get("report_month", self.report_month), 
            vals.get("report_year", self.report_year), 
            vals.get("department_id", self.department_id.id),
            restaurant_network_ids and restaurant_network_ids[0][2] or self.restaurant_network_ids.ids
        )
        vals.update(computed_values)
        return super(DepartmentReport, self).write(vals)

    def _get_computed_fields(
            self, report_month, report_year, department_id, restaurant_network_ids
        ):
        restaurant_ids = self.env["restaurant_management.restaurant"].search([
            ("restaurant_network_id", "in", restaurant_network_ids)
        ])

        report_previous_month = self._compute_report_previous_month(report_month)
        fault_count, fault_count_percentage = self._compute_fault_count(
            report_year, report_month, department_id, restaurant_ids.ids
        )
        mean_fault_count_per_restaurant, mean_fault_count_per_audit = self._compute_mean_fault_count(
            report_year, report_month, fault_count, restaurant_ids.ids
        )
        relative_by_month_fault_count = self._compute_relative_by_month_fault_count(
            report_year, report_month, department_id, restaurant_ids.ids
        )
        restaurant_rating_within_department_data = self._compute_restaurant_rating_within_department(
            report_year, report_month, department_id, restaurant_ids.ids
        )

        top_violations_data = self._compute_top_violations(
            report_year, report_month, department_id, restaurant_ids.ids
        )

        fault_count_chart_data = self._compute_faults_by_months(
            report_year, department_id, restaurant_ids.ids
        )

        department_rating = self._compute_department_rating(
            report_year, report_month, department_id, restaurant_ids.ids
        )

        return {
            "report_previous_month": report_previous_month,
            "fault_count": fault_count,
            "fault_count_percentage": fault_count_percentage,
            "mean_fault_count_per_restaurant": mean_fault_count_per_restaurant,
            "mean_fault_count_per_audit": mean_fault_count_per_audit,
            "relative_by_month_fault_count": relative_by_month_fault_count,
            "restaurant_rating_within_department_data": restaurant_rating_within_department_data,
            "top_violations_data": top_violations_data,
            "fault_count_chart_data": fault_count_chart_data,
            "department_rating": department_rating,
        }

    def _compute_report_previous_month(self, report_month):
        index = 0
        for month in MONTHS:
            if month[0] == report_month:
                break
            index += 1
        return MONTHS[index-1][0]

    def _compute_fault_count(self, report_year, report_month, department_id, restaurant_ids):
        date_start, date_end = _compute_date_start_end(report_year, report_month)
        check_list_category_ids = self.env["restaurant_management.check_list_category"].search([])
        self.env.cr.execute(
            queries.fault_count_by_department_query, 
            [
                date_start.isoformat(), 
                date_end.isoformat(), 
                tuple(restaurant_ids),
                tuple(check_list_category_ids.ids)
            ]
        )
        result = self.env.cr.fetchall()
        department_fault_count = [res[1] for res in result if int(res[0]) == department_id]
        fault_count = department_fault_count[0] if department_fault_count else 0
        fault_count_percentage = round((fault_count/(sum(r[1] for r in result) or 1))*100, 2)
        
        return fault_count, fault_count_percentage

    def _compute_mean_fault_count(self, report_year, report_month, fault_count, restaurant_ids):
        date_start, date_end = _compute_date_start_end(report_year, report_month)

        audit_count = self.env["restaurant_management.restaurant_audit"].search_count([
            ("audit_date", ">=", date_start),
            ("audit_date", "<=", date_end),
            ("restaurant_id", "in", restaurant_ids)
        ])
        mean_fault_count_per_restaurant = round(fault_count/len(restaurant_ids), 2) if len(restaurant_ids) else 0
        mean_fault_count_per_audit = round(fault_count/audit_count, 2) if audit_count else 0
        return mean_fault_count_per_restaurant, mean_fault_count_per_audit

    def _compute_relative_by_month_fault_count(
            self, report_year, report_month, department_id, restaurant_ids
        ):
        date_start, date_end = _compute_date_start_end(report_year, report_month)
        date_start = (date_start - timedelta(days=1)).replace(day=1)

        self.env.cr.execute(
            queries.relative_by_month_fault_count_query, 
            [date_start.isoformat(), date_end.isoformat(), department_id, tuple(restaurant_ids)]
        )
        data = self.env.cr.fetchall()
        return data[0][0] if data else 0

    def _compute_restaurant_rating_within_department(
        self, report_year, report_month, department_id, restaurant_ids
    ):
        date_start, date_end = _compute_date_start_end(report_year, report_month)
        self.env.cr.execute(
            queries.restaurant_rating_within_department_query, 
            [
                date_start.isoformat(), 
                date_end.isoformat(), 
                department_id, 
                tuple(restaurant_ids),
                tuple(restaurant_ids)
            ]
        )
        data = self.env.cr.fetchall()
        return json.dumps([{
                "rating": index,
                "faults": row[0],
                "restaurants": ", ".join(row[1]),
                "restaurant_ids": row[2],
            } for index, row in enumerate(data)
        ])

    def _compute_top_violations(self, report_year, report_month, department_id, restaurant_ids):
        date_start, date_end = _compute_date_start_end(report_year, report_month)
        self.env.cr.execute(
            queries.top_violations_by_department_query, 
            [date_start.isoformat(), date_end.isoformat(), department_id, tuple(restaurant_ids)]
        )
        return json.dumps([{
                "id": row[0],
                "name": row[1],
                "total_faults": row[2],
            } for row in self.env.cr.fetchall()
        ])

    def _compute_faults_by_months(self, report_year, department_id, restaurant_ids):
        chart_date_start = date(year=int(report_year), month=1, day=1)
        chart_date_end = date(year=int(report_year), month=12, day=31)
        self.env.cr.execute(
            queries.faults_by_months_query, 
            [chart_date_start.isoformat(), chart_date_end.isoformat(), department_id, tuple(restaurant_ids)]
        )
        data = {d[0]: d[1] for d in self.env.cr.fetchall()}
        year_this = [data.get(int(month_data[0]), 0) for month_data in MONTHS]

        chart_date_start = date(year=int(report_year) - 1, month=1, day=1)
        chart_date_end = date(year=int(report_year) - 1, month=12, day=31)
        self.env.cr.execute(
            queries.faults_by_months_query, 
            [chart_date_start.isoformat(), chart_date_end.isoformat(), department_id, tuple(restaurant_ids)]
        )
        data = {d[0]: d[1] for d in self.env.cr.fetchall()}
        year_before = [data.get(int(month_data[0]), 0) for month_data in MONTHS]
        return json.dumps({
            int(report_year): year_this,
            int(report_year)-1: year_before,
        })

    def _compute_department_rating(self, report_year, report_month, department_id, restaurant_ids): 
        date_start, date_end = _compute_date_start_end(report_year, report_month)
        self.env.cr.execute(
            queries.department_rating_query, 
            [date_start.isoformat(), date_end.isoformat(), tuple(restaurant_ids)]
        )
        rating = 1
        data = self.env.cr.fetchall()
        department_rating = f"{rating}/{len(data)}"
        for r in data:
            if department_id in r[0]:
                department_rating = f"{rating}/{len(data)}"
                break
            rating += 1

        return department_rating

    @api.depends("write_date")
    def _compute_top_violations_chart(self):
        for rec in self:
            # Define the data for the bar chart
            data = json.loads(rec.top_violations_data)

            # Extract the category names and values from the data
            max_len = max(len(item["name"]) for item in reversed(data)) if data else 10
            step = round(max_len/2)
            y = []
            for item in reversed(data):
                new_name = ""
                for chunk in range(0, len(item["name"]), step):
                    new_name += item["name"][chunk:chunk+step]
                    new_name += "<br>"
                y.append(new_name)
            
            x = [item['total_faults'] for item in reversed(data)]
            rec.top_violations_chart = ChartBuilder().build_horizontal_bar_chart(x, y)
    
    @api.depends("write_date")
    def _compute_fault_count_chart(self):
        for rec in self:
            # Create the data for the first line chart
            data = json.loads(rec.fault_count_chart_data)
            label1 = rec.report_year
            label2 = str(int(rec.report_year) - 1)
            y1 = data[label1]
            y2 = data[label2]
            max_value = max(max(y1), max(y2))
            upper_limit = round( max_value*1.1)
            months = [m[1] for m in self._fields['report_month']._description_selection(self.env)]

            rec.fault_count_chart = ChartBuilder().build_year_to_year_line_chart(
                months, y1, y2, label1, label2, upper_limit
            )
 