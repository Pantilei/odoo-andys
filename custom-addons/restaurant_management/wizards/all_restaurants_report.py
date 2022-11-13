from numpy import dstack
from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY
from calendar import monthrange

import json
import itertools

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

    def _default_month_end(self):
        return str((date.today()).month)

    def _default_month_start(self):
        return str((date.today() + relativedelta(months=-2)).month)

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

    dynamics_of_faults_json = fields.Text(
        compute="_compute_dynamics_of_faults_json"
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
        default=lambda self: str(
            (date.today() + relativedelta(months=-2)).year)
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

    @api.depends("restaurant_network_ids", "check_list_category_ids", "year_start",
                 "year_end", "month_start", "month_end")
    def _compute_dynamics_of_faults_json(self):
        FaultRegistry = self.env["restaurant_management.fault_registry"]
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
            fault_registry_data = FaultRegistry.get_fault_counts_per_month(
                date_start, date_end,
                restaurant_network_ids=record.restaurant_network_ids.ids,
                check_list_category_ids=record.check_list_category_ids.ids
            )
            fault_counts = fault_registry_data.get("fault_counts")
            fault_per_audit = fault_registry_data.get("fault_per_audit")

            dataset = [{
                "data": fault_counts,
                "label": _("Fault Count"),
                "borderColor": "rgb(54, 162, 235, 0.4)",
                "cubicInterpolationMode": 'monotone',
                "tension": 0.4,
                'pointRadius': 5,
                'pointHoverRadius': 8,
                'fill': False,
                'yAxisID': 'y1',
                'datalabels': {
                    'color': 'rgb(54, 162, 235)',
                    'anchor': 'top',
                    # 'align': 'top',
                    'align': 'left',
                    'offset': 10,
                    'font': {
                        'weight': 'bold',
                        'size': 20
                    }
                }
            }, {
                "data": fault_per_audit,
                "label": _("Fault per Audit"),
                "borderColor": "rgb(255, 99, 132, 0.5)",
                "cubicInterpolationMode": 'monotone',
                "tension": 0.4,
                'pointRadius': 5,
                'pointHoverRadius': 8,
                'fill': False,
                'yAxisID': 'y2',
                'datalabels': {
                    'color': 'rgb(255, 99, 132)',
                    'anchor': 'bottom',
                    'align': 'right',
                    'offset': 10,
                    'font': {
                        'weight': 'bold',
                        'size': 20
                    }
                }
            }]

            data = {
                'labels': record._get_month_range(date_start, date_end),
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
