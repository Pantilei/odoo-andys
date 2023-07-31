import itertools
import json
import random
from calendar import monthrange
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from dateutil.rrule import MONTHLY, rrule

from odoo import _, api, fields, models

from ..tools import short_date

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


class AllRestaurantsReports(models.TransientModel):
    _name = "restaurant_management.all_restaurants_report_wizard"
    _description = "Wizard to print all restaurants report"

    def _default_date_end(self):
        d = date.today() + relativedelta(months=-1)
        return date(year=d.year, month=d.month, day=monthrange(d.year, d.month)[1])

    def _default_date_start(self):
        d = date.today() + relativedelta(months=-1)
        return date(year=d.year, month=d.month, day=1)

    def _get_default_departaments(self):
        return self.env["restaurant_management.check_list_category"].search([
            ("default_category", "=", True),
        ])

    def _get_default_restaurant_networks(self):
        return self.env["restaurant_management.restaurant_network"].search([])

    name = fields.Char(
        string="Name",
        default="Print PDF of report"
    )

    report = fields.Selection(selection=[
        ("fault_count_dynamics", "Fault Count Dynamics"),
        ("relative_faults_distribution", "Relative Faults Distribution"),
    ],
        default="fault_count_dynamics",
        required=True
    )

    dynamics_of_faults_json = fields.Text(
        compute="_compute_dynamics_of_faults_json"
    )

    relative_faults_distribution_one_month_json = fields.Text(
        compute="_compute_relative_faults_distribution_json"
    )

    relative_faults_distribution_month_range_json = fields.Text(
        compute="_compute_relative_faults_distribution_json"
    )

    check_list_category_ids = fields.Many2many(
        comodel_name="restaurant_management.check_list_category",
        relation="restaurant_management_all_r_reports_wizard_rel",
        string="Departments",
        default=_get_default_departaments,
        required=True
    )

    restaurant_network_ids = fields.Many2many(
        comodel_name="restaurant_management.restaurant_network",
        relation="restaurant_management_all_rest_rprts_wizard_rel",
        string="Restaurant Networks",
        default=_get_default_restaurant_networks,
        required=True
    )

    date_start = fields.Date(
        string="Date Start",
        default=_default_date_start
    )
    date_end = fields.Date(
        string="Date End",
        default=_default_date_end
    )

    # @api.depends("report", "restaurant_network_ids", "check_list_category_ids", "date_start", "date_end")
    # def _compute_relative_faults_distribution_json(self):
    #     for record in self:
    #         FaultRegistry = self.env["restaurant_management.fault_registry"]
    #         date_start_short = date(
    #             year=int(record.year),
    #             month=int(record.month),
    #             day=1
    #         )
    #         date_end_short = date(
    #             year=int(record.year),
    #             month=int(record.month),
    #             day=monthrange(year=int(record.year),
    #                            month=int(record.month))[1]
    #         )

    #         fault_count_per_department_short = []
    #         labels_short = []
    #         background_colors = []
    #         for category_id in record.check_list_category_ids:
    #             fault_count_short = FaultRegistry.get_fault_counts(
    #                 date_start_short, date_end_short,
    #                 restaurant_network_ids=record.restaurant_network_ids.ids,
    #                 check_list_category_ids=category_id.ids
    #             )
    #             fault_count_per_department_short.append(fault_count_short)
    #             labels_short.append(category_id.name)
    #             background_colors.append(
    #                 f'rgb({str(round(255*random.random()))}, {str(round(255*random.random()))}, {str(round(255*random.random()))})'
    #             )

    #         # all_count_short = sum(fault_count_per_department_short)
    #         # fault_count_per_department_short_percentage = [
    #         #     round((i/all_count_short)*100, ndigits=1) for i in fault_count_per_department_short
    #         # ]

    #         short_data_chart_configs = self._construct_chart_configs(
    #             fault_count_per_department_short, labels_short, background_colors)
    #         record.relative_faults_distribution_one_month_json = json.dumps(
    #             short_data_chart_configs)

    #         date_start_long = date(
    #             year=int(record.year_start),
    #             month=int(record.month_start),
    #             day=1
    #         )
    #         date_end_long = date(
    #             year=int(record.year_end),
    #             month=int(record.month_end),
    #             day=monthrange(year=int(record.year_end),
    #                            month=int(record.month_end))[1]
    #         )
    #         fault_count_per_department_long = []
    #         labels_long = []
    #         for category_id in record.check_list_category_ids:
    #             fault_count_long = FaultRegistry.get_fault_counts(
    #                 date_start_long, date_end_long,
    #                 restaurant_network_ids=record.restaurant_network_ids.ids,
    #                 check_list_category_ids=category_id.ids
    #             )
    #             fault_count_per_department_long.append(fault_count_long)
    #             labels_long.append(category_id.name)

    #         # all_count_long = sum(fault_count_per_department_long)
    #         # fault_count_per_department_long_percentage = [
    #         #     round((i/all_count_long)*100, ndigits=1) for i in fault_count_per_department_long
    #         # ]

    #         long_data_chart_configs = self._construct_chart_configs(
    #             fault_count_per_department_long, labels_long, background_colors)

    #         record.relative_faults_distribution_month_range_json = json.dumps(
    #             long_data_chart_configs)

    # def _construct_chart_configs(self, data, labels, background_colors):
    #     data = {
    #         'labels': labels,
    #         'datasets': [{
    #             'data': data,
    #             'backgroundColor': background_colors
    #         }],
    #     }

    #     return {
    #         'type': 'pie',
    #         'data': data
    #     }

    @api.depends("report", "restaurant_network_ids", "check_list_category_ids", "date_start", "date_end")
    def _compute_dynamics_of_faults_json(self):
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        for record in self:
            if not record.report or not record.date_start or \
                    not record.date_end or not record.restaurant_network_ids or \
                    not record.check_list_category_ids or record.date_start > record.date_end:

                record.dynamics_of_faults_json = json.dumps({})
                return
            
            fault_registry_data = FaultRegistry.get_fault_counts_per_month(
                record.date_start, record.date_end,
                restaurant_network_ids=record.restaurant_network_ids.ids,
                check_list_category_ids=record.check_list_category_ids.ids
            )
            fault_counts = fault_registry_data.get("fault_counts")
            fault_per_audit = fault_registry_data.get("fault_per_audit")

            dataset = [{
                "data": fault_counts,
                "label": _("Fault Count"),
                "cubicInterpolationMode": 'monotone',
                "tension": 0.4,
                'pointRadius': 5,
                'pointHoverRadius': 8,

                'fill': False,
                'backgroundColor': 'rgb(54, 162, 235, 0.2)',
                'labelBackgroundColor': 'rgb(54, 162, 235, 0.2)',
                "borderColor": "rgb(54, 162, 235, 0.5)",
                'labelColor': 'rgb(54, 162, 235)',

                'yAxisID': 'y1',

                'datalabels': {
                    'font': {
                        'size': 16
                    }
                }
            }, {
                "data": fault_per_audit,
                "label": _("Fault per Audit"),
                "cubicInterpolationMode": 'monotone',
                "tension": 0.4,
                'pointRadius': 5,
                'pointHoverRadius': 8,

                'fill': False,
                'backgroundColor': 'rgb(255, 99, 132, 0.2)',
                'labelBackgroundColor': 'rgb(255, 99, 132, 0.2)',
                "borderColor": "rgb(255, 99, 132, 0.5)",
                'labelColor': 'rgb(255, 99, 132)',

                'yAxisID': 'y2',

                'datalabels': {
                    'font': {
                        'size': 16
                    }
                }
            }]

            data = {
                'labels': record._get_month_range(record.date_start, record.date_end),
                'datasets': dataset,
            }
            options = {
                'responsive': True,
                'maintainAspectRatio': False,

                'title': {
                    'display': False,
                    'text': _('Количество Ошибок')
                },
                'legend': {
                    'display': True,
                    'labels': {
                        'fontSize': 20,
                    }
                },
                'scales': {
                    'yAxes': [{
                        'id': 'y1',
                        'position': 'left',
                        'scaleLabel': {
                            'display': True,
                            'labelString': _("Fault Count"),
                            'fontSize': 25,
                        },
                        'ticks': {
                            'suggestedMin': 0,
                            'suggestedMax': max(fault_counts)*1.1,
                            'fontSize': 20,
                        }
                    }, {
                        'id': 'y2',
                        'position': 'right',
                        'scaleLabel': {
                            'display': True,
                            'labelString': _("Fault Count / Audit"),
                            'fontSize': 25,
                        },
                        'ticks': {
                            'suggestedMin': 0,
                            'suggestedMax': max(fault_per_audit)*1.1,
                            'fontSize': 20,
                        }
                    }],
                    'xAxes': [{
                        'scaleLabel': {
                            'display': True,
                            'labelString': _('Months'),
                            'fontSize': 25,
                        },
                        'ticks': {
                            'fontSize': 20,
                        }
                    }],
                }
            }
            configs = {
                'type': 'line',
                'data': data,
                'options': options,
            }

            record.dynamics_of_faults_json = json.dumps(configs)

    def _get_month_range(self, date_start, date_end):
        return [short_date(r) for r in rrule(MONTHLY, dtstart=date_start, until=date_end)]
