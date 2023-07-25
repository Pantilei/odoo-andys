import json
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

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


class CompanyReport(models.Model):
    _name = "restaurant_management.company_report"
    _description = "Company Report"
    _order = "create_date desc"
    

    @api.depends("report_year", "report_month")
    def _compute_name(self):
        for record in self:
            if record.report_year and record.report_month:
                record.name = f"{record.report_year}-{record.report_month}"
            else:
                record.name = ""

    @api.depends("report_year")
    def _compute_previous_report_year(self):
        for record in self:
            record.previous_report_year = record.report_year and str(int(record.report_year) - 1)

    name = fields.Char(
        compute="_compute_name"
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
        readonly=True
    )

    report_year = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        string="Year of Report",
        required=True,
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
        required=True,
        default=lambda self: str(
            (date.today() + relativedelta(months=-1)).month),
        readonly=False
    )

    responsible_id = fields.Many2one(
        comodel_name="res.users",
        required=True,
        default=lambda self: self.env.user.id,
        string="Composed by"
    )

    restaurant_network_ids = fields.Many2many(
        comodel_name="restaurant_management.restaurant_network",
        relation="restaurant_management_res_nets_to_comp_rep",
        default=lambda self: self.env["restaurant_management.restaurant_network"].search([]).ids,
        required=True,
        string="Restaurant Networks"
    )

    monthly_audit_counts = fields.Text()
    monthly_audit_counts_chart = fields.Text(
        compute="_compute_monthly_audit_counts_chart"
    )

    absolute_monthly_fault_counts = fields.Text()
    absolute_monthly_fault_counts_chart = fields.Text(
        compute="_compute_absolute_monthly_fault_counts_chart"
    )

    relative_monthly_fault_counts = fields.Text()
    relative_monthly_fault_counts_chart = fields.Text(
        compute="_compute_relative_monthly_fault_counts_chart"
    )

    top_faults = fields.Text()
    top_faults_table = fields.Text(
        compute="_compute_top_faults_table"
    )
    
    restaurant_rating = fields.Text()
    restaurant_rating_table = fields.Text(
        compute="_compute_restaurant_rating_table"
    )

    summary = fields.Text(string="Summary")


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            computed_values = self._get_computed_fields(
                int(vals["report_month"]), 
                int(vals["report_year"]), 
                vals["restaurant_network_ids"][0][2],
            )
            vals.update(computed_values)
        return super(CompanyReport, self).create(vals_list)

    def write(self, vals):
        if "restaurant_network_ids" in vals:
            restaurant_network_ids = vals["restaurant_network_ids"][0][2]
        else:
            restaurant_network_ids = self.restaurant_network_ids.ids
        computed_values = self._get_computed_fields(
            int(vals.get("report_month", self.report_month)), 
            int(vals.get("report_year", self.report_year)), 
            restaurant_network_ids
        )
        vals.update(computed_values)
        return super(CompanyReport, self).write(vals)

    def _get_computed_fields(self, report_month, report_year, restaurant_network_ids):
        restaurant_ids = self.env["restaurant_management.restaurant"].search([
            ("restaurant_network_id", "in", restaurant_network_ids)
        ]).ids

        monthly_audit_counts = self._compute_monthly_audit_counts(report_year, restaurant_ids)
        absolute_monthly_fault_counts = self._compute_absolute_monthly_fault_counts(report_year, restaurant_ids)
        relative_monthly_fault_counts = self._compute_relative_monthly_fault_counts(
            report_year, restaurant_ids, absolute_monthly_fault_counts
        )
        top_faults = self._compute_top_faults(report_month, report_year, restaurant_ids)
        restaurant_rating = self._compute_restaurant_ratings(report_month, report_year, restaurant_ids)

        return {
            "monthly_audit_counts": monthly_audit_counts,
            "absolute_monthly_fault_counts": absolute_monthly_fault_counts,
            "relative_monthly_fault_counts": relative_monthly_fault_counts,
            "top_faults": top_faults,
            "restaurant_rating": restaurant_rating,
        }
    
    def _compute_monthly_audit_counts(self, report_year, restaurant_ids):
        date_start = date(year=report_year, month=1, day=1).isoformat()
        date_end = date(year=report_year, month=12, day=31).isoformat()
        self.env.cr.execute(
            queries.actual_audit_count_by_year,
            [tuple(restaurant_ids), date_start, date_end]
        )

        month_to_audit_count = {
            row[0]: row[1]
            for row in self.env.cr.fetchall()
        }
        actual_audit_count = [
            month_to_audit_count.get(int(month[0]), 0) for month in MONTHS
        ]

        planned_audit_count = self.env["restaurant_management.planned_audits"].get_monthly_planned_audit_count(
            report_year, restaurant_ids
        )
        if not planned_audit_count:
            raise UserError(_("No planned audits for restaurants"))
        
        return json.dumps({
            "planned": list(planned_audit_count), 
            "actual": actual_audit_count
        })

    def _compute_absolute_monthly_fault_counts(self, report_year, restaurant_ids):
        date_start_this_year = date(year=report_year, month=1, day=1).isoformat()
        date_end_this_year = date(year=report_year, month=12, day=31).isoformat()
        self.env.cr.execute(
            queries.faults_by_months_in_restaurants_query,
            [date_start_this_year, date_end_this_year, tuple(restaurant_ids)]
        )
        this_year_month_to_fault_count = {
            row[0]: row[1] for row in self.env.cr.fetchall()
        }

        date_start_prev_year = date(year=report_year-1, month=1, day=1).isoformat()
        date_end_prev_year = date(year=report_year-1, month=12, day=31).isoformat()
        self.env.cr.execute(
            queries.faults_by_months_in_restaurants_query,
            [date_start_prev_year, date_end_prev_year, tuple(restaurant_ids)]
        )
        prev_year_month_to_fault_count = {
            row[0]: row[1] for row in self.env.cr.fetchall()
        }

        return json.dumps({
            report_year: [this_year_month_to_fault_count.get(int(month[0]), 0) for month in MONTHS], 
            report_year-1: [prev_year_month_to_fault_count.get(int(month[0]), 0) for month in MONTHS]
        })

    def _compute_relative_monthly_fault_counts(
            self, report_year, restaurant_ids, absolute_monthly_fault_counts
        ):
        date_start = date(year=report_year, month=1, day=1).isoformat()
        date_end = date(year=report_year, month=12, day=31).isoformat()
        self.env.cr.execute(
            queries.actual_audit_count_by_year,
            [tuple(restaurant_ids), date_start, date_end]
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
            [tuple(restaurant_ids), date_start, date_end]
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
    
    def _compute_restaurant_ratings(self, report_month, report_year, restaurant_ids):
        date_start, date_end = compute_date_start_end(report_year, report_month)
        self.env.cr.execute(
            queries.fault_counts_by_restaurants_query,
            [
                date_start.isoformat(), 
                date_end.isoformat(),
                tuple(restaurant_ids),
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
    
    @api.depends("write_date")
    def _compute_monthly_audit_counts_chart(self):
        for record in self:
            data = json.loads(record.monthly_audit_counts)
            y1 = data["actual"]
            y2 = data["planned"]
            max_value = max(max(y1), max(y2))
            upper_limit = round(max_value*1.2)
            months = [m[1] for m in self._fields['report_month']._description_selection(self.env)]            
            record.monthly_audit_counts_chart = ChartBuilder(height=250).build_year_to_year_line_chart(
                months, y1, y2, _("Actual"), _("Planned"), upper_limit
            )

    @api.depends("write_date")
    def _compute_absolute_monthly_fault_counts_chart(self):
        for record in self:
            data = json.loads(record.absolute_monthly_fault_counts)
            label1 = record.report_year
            label2 = str(int(record.report_year) - 1)
            y1 = data[label1]
            y2 = data[label2]
            max_value = max(max(y1), max(y2))
            upper_limit = round(max_value*1.2)
            months = [m[1] for m in self._fields['report_month']._description_selection(self.env)]            
            record.absolute_monthly_fault_counts_chart = ChartBuilder(height=250).build_year_to_year_line_chart(
                months, y1, y2, label1, label2, upper_limit
            )
    
    @api.depends("write_date")
    def _compute_relative_monthly_fault_counts_chart(self):
        for record in self:
            data = json.loads(record.relative_monthly_fault_counts)
            label1 = record.report_year
            label2 = str(int(record.report_year) - 1)
            y1 = data[label1]
            y2 = data[label2]
            max_value = max(max(y1), max(y2))
            upper_limit = round(max_value*1.2)
            months = [m[1] for m in self._fields['report_month']._description_selection(self.env)]            
            record.relative_monthly_fault_counts_chart = ChartBuilder(height=250).build_year_to_year_line_chart(
                months, y1, y2, label1, label2, upper_limit
            )
    
    @api.depends("write_date")
    def _compute_top_faults_table(self):
        for record in self:
            top_faults = json.loads(record.top_faults)
            for top_fault in top_faults:
                top_fault["progress_bar"] = round(top_fault["fault_count"]/top_faults[0]["fault_count"], 4)*100
            template = self.env.ref("restaurant_management.report_top_faults_table")
            record.top_faults_table = template._render({"top_faults": top_faults})

    
    @api.depends("write_date")
    def _compute_restaurant_rating_table(self):
        for record in self:
            ratings = json.loads(record.restaurant_rating)
            for rating in ratings:
                rating["restaurants"] = ", ".join(rating["restaurant_names"])
            template = self.env.ref("restaurant_management.company_report_restaurant_rating")
            record.restaurant_rating_table = template._render({
                "restaurant_ratings": ratings
            })
