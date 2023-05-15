import json
from datetime import date

import plotly
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

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

    report_year = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        string="Year of Report",
        default=lambda self: str(date.today().year)
    )
    report_month = fields.Selection(
        string="Report Month",
        selection=MONTHS,
        default=lambda self: str(
            (date.today() + relativedelta(months=-1)).month),
    )

    responsible_id = fields.Many2one(
        comodel_name="res.users",
        default=lambda self: self.env.user.id,
        string="Responsible"
    )

    total_departments_count = fields.Integer(
        compute="_compute_total_departments_count",
        store=True
    )

    department_rating = fields.Char(
        compute="_compute_department_rating"
    )

    relative_fault_count_comment = fields.Text()

    fault_count_chart = fields.Text(
        string='Plotly Chart',
        compute='_compute_fault_count_chart',
    )

    fault_count_chart_data = fields.Text(
        string="Chart Data",
        compute="_compute_faults_by_months",
        store=True
    )

    top_violations_chart = fields.Text(
        string="Top Violations Chart",
        compute="_compute_top_violations_chart"
    )

    @api.depends("report_year", "report_month", "department_id")
    def _compute_top_violations_chart(self):

        for rec in self:
            # Define the data for the bar chart
            data = [
                {'category': 'Category A', 'value': 20},
                {'category': 'Category B', 'value': 35},
                {'category': 'Category C', 'value': 10},
                {'category': 'Category D', 'value': 15},
                {'category': 'Category E', 'value': 15},
                {'category': 'Category F', 'value': 25},
                {'category': 'Category G', 'value': 35},
                {'category': 'Category K', 'value': 5},
                {'category': 'Category L', 'value': 18},
                {'category': 'Category M', 'value': 15},
            ]

            # Extract the category names and values from the data
            categories = [item['category'] for item in data]
            values = [item['value'] for item in data]
            layout = go.Layout(
                # title='Double Line Chart',
                xaxis=dict(
                    tickfont=dict(color='white'), 
                    titlefont=dict(color='white'), 
                    showgrid=True,
                ),
                yaxis=dict(
                    tickfont=dict(color='white'), 
                    titlefont=dict(color='white'),
                ),
                autosize=True,
                height=180,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=1, r=1, b=1, t=1, pad=1),
            )

            # Create the bar chart using plotly
            fig = go.Figure(data=go.Bar(
                x=values,  # Use values as the x-axis values
                y=categories,  # Use categories as the y-axis values
                orientation='h'  # Set the orientation to horizontal
            ), layout=layout)

            config = {'displayModeBar': False}
            rec.top_violations_chart = fig.to_html(config=config)



    @api.depends("report_year", "report_month", "department_id")
    def _compute_faults_by_months(self):
        query = """
            SELECT 
                EXTRACT(MONTH FROM faults_by_date.fault_month) AS month_of_faults, 
                faults_by_date.total_faults AS total_faults
            FROM
            (
                SELECT 
                    DATE_TRUNC('month', rmfr.fault_date) AS fault_month,
                    SUM(rmfr.fault_count) AS total_faults
                FROM restaurant_management_fault_registry rmfr 
                WHERE 
                    rmfr.state = 'confirm' AND 
                    rmfr.fault_date >= %s AND 
                    rmfr.fault_date <= %s AND
                    rmfr.check_list_category_id = %s
                GROUP BY fault_month
                ORDER BY fault_month DESC
            ) AS faults_by_date;
        """
        for record in self:
            chart_date_start = date(year=int(record.report_year), month=1, day=1)
            chart_date_end = date(year=int(record.report_year), month=12, day=31)
            self.env.cr.execute(
                query, 
                [chart_date_start.isoformat(), chart_date_end.isoformat(), record.department_id.id]
            )
            data = {d[0]: d[1] for d in self.env.cr.fetchall()}
            year_this = [data.get(int(month_data[0]), 0) for month_data in MONTHS]

            chart_date_start = date(year=int(record.report_year) - 1, month=1, day=1)
            chart_date_end = date(year=int(record.report_year) - 1, month=12, day=31)
            self.env.cr.execute(
                query, 
                [chart_date_start.isoformat(), chart_date_end.isoformat(), record.department_id.id]
            )
            data = {d[0]: d[1] for d in self.env.cr.fetchall()}
            year_before = [data.get(int(month_data[0]), 0) for month_data in MONTHS]
            record.fault_count_chart_data = json.dumps({
                int(record.report_year): year_this,
                int(record.report_year)-1: year_before,
            })


    @api.depends("fault_count_chart_data")
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
            months = [m[1] for m in MONTHS]

            # Create the first line chart trace
            trace1 = go.Scatter(
                x=months,
                y=y1,
                mode='lines',
                name=label1,
                line=dict(color="#46A1BF")
            )

            # Create the second line chart trace
            trace2 = go.Scatter(
                x=months,
                y=y2,
                mode='lines',
                name=label2,
                line=dict(color="#5cc4cc")
            )

            # Combine the traces into a data object
            data = [trace1, trace2]

            # Create the layout for the chart
            layout = go.Layout(
                # title='Double Line Chart',
                xaxis=dict(
                    tickfont=dict(color='white'), 
                    titlefont=dict(color='white'), 
                    showgrid=False,
                ),
                yaxis=dict(
                    tickfont=dict(color='white'), 
                    titlefont=dict(color='white'),
                    range=[0, upper_limit]
                ),
                autosize=True,
                height=180,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=True,
                legend=dict(x=0.5, y=1.1, orientation='h', yanchor='top', xanchor='center', font=dict(color="white")),
                margin=dict(l=1, r=1, b=1, t=1, pad=1),
            )

            # Create the chart object
            fig = go.Figure(data=data, layout=layout)
            config = {'displayModeBar': False}

            rec.fault_count_chart = fig.to_html(config=config)


    @api.depends("report_year", "report_month")
    def _compute_total_departments_count(self):
        total_departments_count = self.env["restaurant_management.check_list_category"].search_count([])
        for record in self:
            record.total_departments_count = total_departments_count

    @api.depends("report_year", "report_month", "department_id")
    def _compute_department_rating(self):
        
        query = """
            SELECT 
                ARRAY_AGG(department_faults.id) AS department_ids,
                ARRAY_AGG(department_faults.name) AS department_names, 
                fault_count
            FROM (
                SELECT 
                    rmclc.id,
                    rmclc.name,
                    COALESCE(department_fault_counts.total_faults, 0) as fault_count
                FROM 
                    restaurant_management_check_list_category rmclc 
                LEFT JOIN
                (
                    SELECT 
                        check_list_category_id,
                        SUM(fault_count) AS total_faults 
                        FROM restaurant_management_fault_registry 
                    WHERE
                        state = 'confirm' and fault_date >= %s and fault_date <= %s
                    GROUP BY check_list_category_id 
                ) AS department_fault_counts
                ON department_fault_counts.check_list_category_id = rmclc.id
                WHERE rmclc.active = true and rmclc.no_fault_category = false and rmclc.default_category = true
            ) AS department_faults
            GROUP BY fault_count
            ORDER BY fault_count ASC; 
        """
        for record in self:
            fault_date_start = date(year=int(record.report_year), month=int(record.report_month), day=1)
            fault_date_end = fault_date_start + relativedelta(months=1)
            self.env.cr.execute(query, [fault_date_start.isoformat(), fault_date_end.isoformat()])
            rating = 1
            data = self.env.cr.fetchall()
            print(data)
            record.department_rating = f"{rating}/{len(data)}"
            for r in data:
                if record.department_id.id in r[0]:
                    record.department_rating = f"{rating}/{len(data)}"
                    break
                rating += 1

        