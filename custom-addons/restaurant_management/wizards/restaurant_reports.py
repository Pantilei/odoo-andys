from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY
from calendar import monthrange

import json
import itertools

from ..tools import short_date


COLORS = itertools.cycle((
    'rgb(54, 162, 235)',
    'rgb(54, 162, 235, 0.5)',
    'rgb(255, 99, 132)',
    'rgb(255, 99, 132, 0.5)',
    'rgb(96, 186, 125)',
    'rgb(96, 186, 125, 0.5)',
    'rgb(202, 110, 188)',
    'rgb(202, 110, 188, 0.5)',
    'rgb(12, 13, 14)',
    'rgb(12, 13, 14, 0.5)',
    'rgb(56, 84, 153)',
    'rgb(56, 84, 153, 0.5)',
    'rgb(246, 203, 66)',
    'rgb(246, 203, 66, 0.5)',
    'rgb(108, 97, 206)',
    'rgb(108, 97, 206, 0.5)',
    'rgb(59, 117, 213)',
    'rgb(59, 117, 213, 0.5)',
    'rgb(163, 164, 182)',
    'rgb(163, 164, 182, 0.5)',
    'rgb(90, 179, 138)',
    'rgb(90, 179, 138, 0.5)',
))

LINE_COLORS = itertools.cycle((
    'rgb(54, 162, 235)',
    'rgb(255, 99, 132)',
    'rgb(96, 186, 125)',
    'rgb(202, 110, 188)',
    'rgb(12, 13, 14)',
    'rgb(56, 84, 153)',
    'rgb(246, 203, 66)',
    'rgb(108, 97, 206)',
    'rgb(59, 117, 213)',
    'rgb(163, 164, 182)',
    'rgb(90, 179, 138)',
    'rgb(50, 129, 108)',
    'rgb(10, 109, 108)',
))


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


class RestaurantReports(models.TransientModel):
    _name = "restaurant_management.restaurant_reports_wizard"
    _description = "Wizard to print the restaurant reports"

    def _default_month_end(self):
        return str(date.today().month)

    def _default_month_start(self):
        return str((date.today() + relativedelta(months=-2)).month)

    def _get_default_departaments(self):
        return self.env["restaurant_management.check_list_category"].search([
            ("default_category", "=", True),
        ])

    def _default_restaurant_id(self):
        Restaurant = self.env["restaurant_management.restaurant"]
        restaurant_id = Restaurant.search([
            ("director_ids", "in", self.env.user.ids)
        ], limit=1)
        if not restaurant_id:
            restaurant_id = Restaurant.search([], limit=1)
        return restaurant_id

    name = fields.Char(
        string="Name",
        default="Print PDF of report"
    )

    report = fields.Selection(selection=[
        ("restaurant_rating", "Restaurant Rating"),
        ("restaurant_rating_graph", "Restaurant Rating (Graph)"),
        ("fault_count_dynamics", "Fault count dynamics"),
        ("top_faults", "Top Faults"),
    ],
        default="restaurant_rating",
        # required=True
    )

    restaurant_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant",
        string="Restaurant",
        required=True,
        default=_default_restaurant_id
    )

    check_list_category_ids = fields.Many2many(
        comodel_name="restaurant_management.check_list_category",
        relation="restaurant_management_clc_r_reports_wizard_rel",
        string="Departments",
        default=_get_default_departaments,
        required=True
    )

    # restaurant_network_ids = fields.Many2many(
    #     comodel_name="restaurant_management.restaurant_network",
    #     relation="restaurant_management_rn_r_reports_wizard_rel",
    #     string="Restaurant Networks",
    #     default=_default_restaurant_network_id
    # )

    year = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        string="Year of Report",
        default=lambda self: str(date.today().year)
    )

    month = fields.Selection(
        string="Month of Report",
        selection=MONTHS,
        default=lambda self: str(
            (date.today() + relativedelta(months=-1)).month),
    )

    year_start = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        string="Year Start",
        default=lambda self: str(date.today().year)
    )

    month_start = fields.Selection(
        string="Month Start",
        selection=MONTHS,
        default=_default_month_start,
    )

    year_end = fields.Selection(
        selection=[(str(year), str(year)) for year in range(1999, 2049)],
        string="Date End",
        default=lambda self: str(date.today().year),
    )

    month_end = fields.Selection(
        selection=MONTHS,
        default=_default_month_end,
        string="Month End"
    )

    json_chart = fields.Text(
        compute="_compute_json_chart"
    )

    json_top_faults = fields.Text(
        compute="_compute_json_top_faults"
    )

    json_restaurant_rating = fields.Text(
        compute="_compute_json_restaurant_rating"
    )

    json_restaurant_rating_chart = fields.Text(
        compute="_compute_json_restaurant_rating_chart"
    )

    @api.depends("report", "restaurant_id", "check_list_category_ids", "year_start", "month_start", "year_end", "month_end")
    def _compute_json_restaurant_rating_chart(self):
        RestaurantNetwork = self.env["restaurant_management.restaurant_network"]
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        FaultCategory = self.env["restaurant_management.check_list_category"]
        for record in self:
            date_start = date(
                year=int(record.year_start),
                month=int(record.month_start),
                day=1
            )
            date_end = date(
                year=int(record.year_end),
                month=int(record.month_end),
                day=monthrange(year=int(record.year_end),
                               month=int(record.month_end))[1]
            )
            dataset = []
            all_data = []
            for check_list_category_id in record.check_list_category_ids:
                color = next(LINE_COLORS)
                dataset_data = FaultRegistry.get_restaurant_rating_monthly_data(
                    date_start,
                    date_end,
                    record.restaurant_id.id,
                    check_list_category_ids=check_list_category_id.ids,
                )
                all_data = [*all_data, *dataset_data]
                dataset.append({
                    "data": dataset_data,
                    "label": check_list_category_id.name,
                    "borderColor": color,
                    "cubicInterpolationMode": 'monotone',
                    "tension": 0.4,
                    'pointRadius': 5,
                    'pointHoverRadius': 8,
                    'fill': False,
                    'datalabels': {
                        'color': color,
                        'anchor': 'bottom',
                        'align': 'top',
                        # 'formatter': 'Math.round',
                        'font': {
                            'weight': 'bold',
                            'size': 16
                        }
                    }
                })
            data = {
                'labels': record._get_month_range(date_start, date_end),
                'datasets': dataset,
            }
            options = {
                'responsive': True,
                'maintainAspectRatio': False,
                'title': {
                    'display': True,
                    'text': _('Restaurant Rating')
                },
                'legend': {
                    'display': True,
                    # 'labels': {
                    #     'fontColor': 'rgb(255, 99, 132)'
                    # }
                },
                'scales': {
                    'yAxes': [{
                        'scaleLabel': {
                            'display': True,
                            'labelString': _("Rating")
                        },
                        'ticks': {
                            'suggestedMin': 0,
                            'suggestedMax': max(all_data) + 1,
                        }
                    }],
                    'xAxes': [{
                        'scaleLabel': {
                            'display': True,
                            'labelString': _('Months')
                        },
                    }],
                }
            }
            configs = {
                'type': 'line',
                'data': data,
                'options': options,
            }

            record.json_restaurant_rating_chart = json.dumps(configs)

    @api.depends("report", "restaurant_id", "check_list_category_ids", "year", "month")
    def _compute_json_restaurant_rating(self):
        RestaurantNetwork = self.env["restaurant_management.restaurant_network"]
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        FaultCategory = self.env["restaurant_management.check_list_category"]
        for record in self:
            if not record.report or not record.year or \
                    not record.month or not record.restaurant_id or \
                    not record.check_list_category_ids:

                record.json_restaurant_rating = json.dumps({
                    "grouped_restaurant_rating_per_audit": [],
                    "restaurant_id": False
                })
                return
            report_date = date(
                year=int(record.year),
                month=int(record.month),
                day=1
            )

            # restaurant_rating = FaultRegistry.get_restaurant_rating_data(
            #     report_date,
            #     restaurant_network_id=record.restaurant_id.restaurant_network_id.id,
            #     check_list_category_ids=record.check_list_category_ids.ids)

            restaurant_rating_per_audit = FaultRegistry.get_restaurant_rating_per_audit_data(
                report_date,
                restaurant_network_id=record.restaurant_id.restaurant_network_id.id,
                check_list_category_ids=record.check_list_category_ids.ids)

            grouped_restaurant_rating_per_audit = []
            for r in restaurant_rating_per_audit:
                if not len(grouped_restaurant_rating_per_audit):
                    grouped_restaurant_rating_per_audit.append(
                        [[r[0]], [r[1]], r[2]])
                    continue
                if r[2] == grouped_restaurant_rating_per_audit[-1][2]:
                    grouped_restaurant_rating_per_audit[-1][0].append(r[0])
                    grouped_restaurant_rating_per_audit[-1][1].append(r[1])
                else:
                    grouped_restaurant_rating_per_audit.append(
                        [[r[0]], [r[1]], r[2]])

            record.json_restaurant_rating = json.dumps({
                "grouped_restaurant_rating_per_audit": grouped_restaurant_rating_per_audit,
                "restaurant_id": record.restaurant_id.id
            })

    @api.depends("report", "restaurant_id", "check_list_category_ids", "year", "month")
    def _compute_json_top_faults(self):
        RestaurantNetwork = self.env["restaurant_management.restaurant_network"]
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        FaultCategory = self.env["restaurant_management.check_list_category"]
        for record in self:
            if not record.report or not record.year or not record.month or \
                    not record.check_list_category_ids:

                record.json_top_faults = json.dumps([])
                return

            date_start = date(
                year=int(record.year),
                month=int(record.month),
                day=1
            )
            date_end = date(
                year=int(record.year),
                month=int(record.month),
                day=monthrange(year=int(record.year),
                               month=int(record.month))[1]
            )
            res = self.env['restaurant_management.fault_registry'].get_top_faults(
                date_start, date_end,
                check_list_category_id=None,
                check_list_category_ids=record.check_list_category_ids.ids,
                restaurant_id=record.restaurant_id.id,
                restaurant_ids=None,
                restaurant_network_id=None,
                restaurant_network_ids=None
            )
            rows = res[:10] if len(res) >= 10 else res
            top_faults_with_comments = []
            for top_fault in rows:
                top_faults_with_comments.append((
                    top_fault[0],
                    top_fault[1],
                    top_fault[2],
                    FaultRegistry.get_director_comments_of_faults(
                        date_start,
                        date_end,
                        top_fault[0],
                        restaurant_id=record.restaurant_id.id,
                    )
                ))

            record.json_top_faults = json.dumps(top_faults_with_comments)

    @api.depends("report", "restaurant_id", "year_start", "year_end", "month_start", "month_end", "check_list_category_ids")
    def _compute_json_chart(self):
        for record in self:
            date_start = date(
                year=int(self.year_start),
                month=int(self.month_start),
                day=1
            )
            date_end = date(
                year=int(self.year_end),
                month=int(self.month_end),
                day=monthrange(year=int(self.year_end),
                               month=int(self.month_end))[1]
            )
            dataset, maximum = self._get_chart_data(date_start, date_end)
            data = {
                'labels': self._get_month_range(date_start, date_end),
                'datasets': dataset,
            }

            options = {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'position': 'top',
                    },
                    'title': {
                        'display': True,
                        'text': 'Chart.js Bar Chart'
                    }
                },
                'title': {
                    'display': True,
                    'text': _('Fault counts within departments')
                },
                'legend': {
                    'display': True,
                },
                'scales': {
                    'yAxes': [{
                        'scaleLabel': {
                            'display': True,
                            'labelString': _("Fault Count/Audit")
                        },
                        'ticks': {
                            'suggestedMin': 0,
                            'suggestedMax': maximum + 1,
                        }
                    }],
                    'xAxes': [{
                        'scaleLabel': {
                            'display': True,
                            'labelString': _('Months')
                        },
                    }],
                }
            }
            configs = {
                'type': 'bar',
                'data': data,
                'options': options,
            }

            record.json_chart = json.dumps(configs)

    def _get_month_range(self, date_start, date_end):
        return [short_date(r) for r in rrule(MONTHLY, dtstart=date_start, until=date_end)]

    def _get_chart_data(self, date_start, date_end):
        CheckListCategory = self.env["restaurant_management.check_list_category"]
        data = []
        all_data = []
        for check_list_category_id in CheckListCategory.browse(self.check_list_category_ids.ids):
            res = self.env['restaurant_management.fault_registry']\
                .get_fault_counts_per_month(
                    date_start,
                    date_end,
                    check_list_category_id=check_list_category_id.id,
                    restaurant_id=self.restaurant_id.id,
                    restaurant_network_id=None,
                    check_list_category_ids=None,
                    restaurant_ids=None,
                    restaurant_network_ids=None
            )
            all_data = [*all_data, *res.get('fault_per_audit', [])]
            color = next(COLORS)
            data.append({
                'label': check_list_category_id.name,
                'data': res.get('fault_per_audit', []),
                'borderColor': color,
                'backgroundColor': next(COLORS),
                'datalabels': {
                    'color': color,
                    'anchor': 'end',
                    'align': 'top',
                    'font': {
                        'weight': 'bold',
                        'size': 16
                    }
                }
            })
        return data, max(all_data)
