import json
from calendar import monthrange
from datetime import date

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

    report_previous_month = fields.Selection(
        selection=MONTHS,
        string="Report Previous Month",
        compute="_compute_report_previous_month",
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

    fault_count = fields.Integer(
        compute="_compute_fault_count",
        string="Fault Count",
        store=True
    )

    fault_count_percentage = fields.Float(
        compute="_compute_fault_count",
        string="Fault Count Percentage",
        store=True
    )

    relative_by_month_fault_count = fields.Integer(
        compute="_compute_relative_by_month_fault_count",
        store=True
    )

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

    top_violations_data = fields.Text(
        string="Top Violations",
        compute="_compute_top_violations",
        store=True
    )

    restaurant_rating_within_department_data = fields.Text(
        compute="_compute_restaurant_rating_within_department",
        store=True
    )

    mean_fault_count_per_restaurant = fields.Float(
        compute="_compute_mean_fault_count",
        store=True
    )
    mean_fault_count_per_audit = fields.Float(
        compute="_compute_mean_fault_count",
        store=True
    )

    taken_measures = fields.Text(string="Taken Measures")
    summary = fields.Text(string="Summary")

    @api.depends("report_month")
    def _compute_report_previous_month(self):
        for record in self:
            if not record.report_month or not record.report_year or not record.department_id:
                record.report_previous_month = MONTHS[0][0]
                continue
            index = 0
            for month in MONTHS:
                if month[0] == record.report_month:
                    break
                index += 1
            record.report_previous_month = MONTHS[index-1][0]

    @api.depends("report_year", "report_month", "department_id")
    def _compute_mean_fault_count(self):
        for record in self:
            if not record.report_month or not record.report_year or not record.department_id:
                record.mean_fault_count_per_restaurant = 0
                record.mean_fault_count_per_audit = 0
                continue

            date_start, date_end = _compute_date_start_end(record.report_year, record.report_month)
            restaurant_count = self.env["restaurant_management.restaurant"].search_count([])
            audit_count = self.env["restaurant_management.restaurant_audit"].search_count([
                ("audit_date", ">=", date_start),
                ("audit_date", "<=", date_end),
            ])
            record.mean_fault_count_per_restaurant = round(record.fault_count/restaurant_count, 2) if restaurant_count else 0
            record.mean_fault_count_per_audit = round(record.fault_count/audit_count, 2) if audit_count else 0

    @api.depends("report_year", "report_month", "department_id")
    def _compute_relative_by_month_fault_count(self):
        query = """
            select 
                faults_by_month_table.faults_count - lag(faults_by_month_table.faults_count) 
                over 
                (order by faults_by_month_table.fault_month) as fault_change
            from 
            (
                select 
                    date_trunc('month', fault_date) as fault_month, 
                    sum(fault_count) as faults_count
                from restaurant_management_fault_registry 
                where 
                    state = 'confirm' and
                    fault_date >= %s and
                    fault_date <= %s and 
                    check_list_category_id = %s
                group by fault_month
            ) as faults_by_month_table
            order by fault_change
            limit 1;
        """
        for record in self:
            if not record.report_month or not record.report_year or not record.department_id:
                record.relative_by_month_fault_count = 0
                continue

            date_end = date(
                year=int(record.report_year), 
                month=int(record.report_month),
                day=monthrange(int(record.report_year), int(record.report_month))[1]
            )
            date_start = (date_end - relativedelta(days=45)).replace(day=1)
            self.env.cr.execute(query, [date_start.isoformat(), date_end.isoformat(), record.department_id.id])
            data = self.env.cr.fetchall()
            record.relative_by_month_fault_count = data[0][0] if data else 0

    @api.depends("report_year", "report_month", "department_id")
    def _compute_fault_count(self):
        query = """
            select 
                check_list_category_id, 
                sum(fault_count) as faults_count
            from restaurant_management_fault_registry 
            where 
                state = 'confirm' and
                fault_date >= %s and
                fault_date <= %s
            group by check_list_category_id;
        """
        for record in self:
            if not record.report_month or not record.report_year or not record.department_id:
                record.fault_count = 0
                record.fault_count_percentage = 0
                continue

            date_start = date(year=int(record.report_year), month=int(record.report_month), day=1)
            date_end = date_start + relativedelta(months=1)
            self.env.cr.execute(
                query, 
                [date_start.isoformat(), date_end.isoformat()]
            )
            result = self.env.cr.fetchall()
            department_fault_count = [res[1] for res in result if int(res[0]) == record.department_id.id]
            record.fault_count = department_fault_count[0] if department_fault_count else 0
            record.fault_count_percentage = round((record.fault_count/(sum(r[1] for r in result) or 1))*100, 2)

    @api.depends("report_year", "report_month", "department_id")
    def _compute_restaurant_rating_within_department(self):
        query = """
            select 
                coalesce(restaurant_rating.faults, 0) as faults,
                restaurant_rating.restaurants as restaurants
            from (
                select 
                    restaurant_name_to_fault_count.total_faults as faults,
                    array_agg(restaurant_name_to_fault_count.restaurant_name) as restaurants 
                from (
                    select 
                        rmr.name as restaurant_name,
                        restaurant_to_fault_count.total_faults as total_faults
                    from (
                        SELECT 
                            restaurant_id,
                            SUM(fault_count) AS total_faults     
                        FROM restaurant_management_fault_registry 
                        WHERE
                            state = 'confirm' and 
                            fault_date >= %s and 
                            fault_date <= %s and 
                            check_list_category_id = %s
                        GROUP BY restaurant_id 
                    ) as restaurant_to_fault_count
                    
                    right join restaurant_management_restaurant rmr
                    on restaurant_to_fault_count.restaurant_id = rmr.id
                ) as restaurant_name_to_fault_count
                group by total_faults
            ) as restaurant_rating
            order by faults asc;
        """
        for rec in self:
            if not rec.report_month or not rec.report_year or not rec.department_id:
                rec.restaurant_rating_within_department_data = json.dumps([{
                    "faults": 0,
                    "restaurants": 0,
                }])
                continue

            date_start = date(year=int(rec.report_year), month=int(rec.report_month), day=1)
            date_end = date_start + relativedelta(months=1)
            self.env.cr.execute(
                query, 
                [date_start.isoformat(), date_end.isoformat(), rec.department_id.id]
            )
            rec.restaurant_rating_within_department_data = json.dumps([{
                    "faults": row[0],
                    "restaurants": row[1],
                } for row in self.env.cr.fetchall()
            ])

    @api.depends("report_year", "report_month", "department_id")
    def _compute_top_violations(self):
        query = """
            select 
                check_list_fault_count.check_list_id as id, 
                rmcl.name as name,
                check_list_fault_count.total_faults as total_faults
            from (
                SELECT 
                    check_list_id,
                    SUM(fault_count) AS total_faults     
                FROM restaurant_management_fault_registry 
                WHERE
                    state = 'confirm' and 
                    fault_date >= %s and 
                    fault_date <= %s and 
                    check_list_category_id = %s
                GROUP BY check_list_id 
            ) as check_list_fault_count

            inner join restaurant_management_check_list rmcl 
            on check_list_fault_count.check_list_id = rmcl.id
            order by total_faults desc
            limit 10;
        """
        for rec in self:
            if not rec.report_month or not rec.report_year or not rec.department_id:
                rec.top_violations_data = json.dumps([{
                    "id": 0,
                    "name": "",
                    "total_faults": 0,
                }])
                continue
            date_start = date(year=int(rec.report_year), month=int(rec.report_month), day=1)
            date_end = date_start + relativedelta(months=1)
            self.env.cr.execute(
                query, 
                [date_start.isoformat(), date_end.isoformat(), rec.department_id.id]
            )
            rec.top_violations_data = json.dumps([{
                    "id": row[0],
                    "name": row[1],
                    "total_faults": row[2],
                } for row in self.env.cr.fetchall()
            ])

    @api.depends("top_violations_data")
    def _compute_top_violations_chart(self):
        for rec in self:
            if not rec.report_month or not rec.report_year or not rec.department_id:
                rec.top_violations_chart = ""
                continue
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
            layout = go.Layout(
                # title='Double Line Chart',
                xaxis=dict(
                    tickfont=dict(color='white'), 
                    titlefont=dict(color='white'), 
                    showgrid=True,
                ),
                yaxis=dict(
                    tickfont=dict(
                        color='white',
                        size=10,
                    ), 
                    titlefont=dict(color='white'),
                ),
                autosize=True,
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=100, r=1, b=1, t=1, pad=1),
            )

            # Create the bar chart using plotly
            fig = go.Figure(data=go.Bar(
                x=x,  # Use values as the x-axis values
                y=y,  # Use categories as the y-axis values
                orientation='h',  # Set the orientation to horizontal
                marker={"color": ["#71EDF1" for _ in y]},
                # texttemplate='%{y}',  # Use %{y} to display the category names as labels
                # textposition='auto'  # Set the position of the labels
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
            if not record.report_month or not record.report_year or not record.department_id:
                record.fault_count_chart_data = json.dumps({
                    "": "",
                })
                continue

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


    @api.depends("report_year", "report_month", "department_id")
    def _compute_fault_count_chart(self):
        for rec in self:
            if not rec.report_month or not rec.report_year or not rec.department_id:
                rec.fault_count_chart = ""
                continue

            # Create the data for the first line chart
            data = json.loads(rec.fault_count_chart_data)
            label1 = rec.report_year
            label2 = str(int(rec.report_year) - 1)
            y1 = data[label1]
            y2 = data[label2]
            max_value = max(max(y1), max(y2))
            upper_limit = round( max_value*1.1)
            months = [m[1] for m in self._fields['report_month']._description_selection(self.env)]

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


    @api.depends("report_year", "report_month", "department_id")
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
            if not record.report_month or not record.report_year or not record.department_id:
                record.department_rating = 0
                continue

            fault_date_start = date(year=int(record.report_year), month=int(record.report_month), day=1)
            fault_date_end = fault_date_start + relativedelta(months=1)
            self.env.cr.execute(query, [fault_date_start.isoformat(), fault_date_end.isoformat()])
            rating = 1
            data = self.env.cr.fetchall()
            record.department_rating = f"{rating}/{len(data)}"
            for r in data:
                if record.department_id.id in r[0]:
                    record.department_rating = f"{rating}/{len(data)}"
                    break
                rating += 1

        