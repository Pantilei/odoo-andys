import itertools
import json
from calendar import monthrange
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from dateutil.rrule import MONTHLY, rrule

from odoo import _, api, fields, models

from ..tools import short_date

COLORS = itertools.cycle((
    ['54', '162', '235'],
    ['255', '99', '132'],
    ['96', '186', '125'],
    ['232', '110', '188'],
    ['12', '13', '14'],
    ['56', '84', '153'],
    ['246', '203', '66'],
    ['108', '97', '206'],
    ['59', '117', '213'],
    ['163', '164', '182'],
    ['90', '179', '138'],
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

    date_start = fields.Date(
        string="Date Start",
        default=_default_date_start
    )
    date_end = fields.Date(
        string="Date End",
        default=_default_date_end
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

    @api.depends("report", "restaurant_id", "check_list_category_ids", "date_start", "date_end")
    def _compute_json_restaurant_rating_chart(self):
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        for record in self:
            if not record.report or not record.date_start or \
                    not record.date_end or not record.restaurant_id or \
                    not record.check_list_category_ids or record.date_start > record.date_end:

                record.json_restaurant_rating_chart = json.dumps({})
                return
            dataset = []
            all_data = []
            for check_list_category_id in record.check_list_category_ids:
                color = ",".join(next(COLORS))
                dataset_data = FaultRegistry.get_restaurant_rating_monthly_data(
                    record.date_start,
                    record.date_end,
                    record.restaurant_id.id,
                    check_list_category_ids=check_list_category_id.ids,
                )
                all_data = [*all_data, *dataset_data]
                dataset.append({
                    "data": dataset_data,
                    "label": check_list_category_id.name,
                    "cubicInterpolationMode": 'monotone',
                    "tension": 0.4,
                    'pointRadius': 5,
                    'pointHoverRadius': 8,

                    'fill': False,
                    'backgroundColor': f'rgb({color}, 0.8)',
                    'labelBackgroundColor': f'rgb({color}, 0.2)',
                    "borderColor": f'rgb({color}, 0.5)',
                    "labelColor": f'rgb({color})',

                    'datalabels': {
                        'anchor': 'bottom',
                        'align': 'top',
                        'font': {
                            'weight': 'bold',
                            'size': 16
                        }
                    }
                })
            data = {
                'labels': record._get_month_range(record.date_start, record.date_end),
                'datasets': dataset,
            }
            options = {
                'responsive': True,
                'maintainAspectRatio': False,
                'title': {
                    'display': True,
                    'text': _('Restaurant Rating Dynamics within Department'),
                    'fontSize': 25,
                },
                'legend': {
                    'display': True,
                    'labels': {
                        'fontSize': 20,
                    }
                },
                'scales': {
                    'yAxes': [{
                        'scaleLabel': {
                            'display': True,
                            'labelString': _("Rating"),
                            'fontSize': 25,
                        },
                        'ticks': {
                            'suggestedMin': 0,
                            'suggestedMax': max(all_data or [0]) + 1,
                            'fontSize': 18,
                        }
                    }],
                    'xAxes': [{
                        'scaleLabel': {
                            'display': True,
                            'labelString': _('Months'),
                            'fontSize': 25,
                        },
                        'ticks': {
                            'fontSize': 18,
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

    @api.depends("report", "restaurant_id", "check_list_category_ids", "date_start", "date_end")
    def _compute_json_restaurant_rating(self):
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        for record in self:
            if not record.report or not record.date_start or \
                    not record.date_end or not record.restaurant_id or \
                    not record.check_list_category_ids or record.date_start > record.date_end:

                record.json_restaurant_rating = json.dumps({
                    "grouped_restaurant_rating_per_audit": [],
                    "restaurant_id": False
                })
                return

            restaurant_rating_per_audit = FaultRegistry.get_restaurant_rating_per_audit_data(
                date_start=record.date_start,
                date_end=record.date_end,
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

    @api.depends("report", "restaurant_id", "check_list_category_ids", "date_start", "date_end")
    def _compute_json_top_faults(self):
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        for record in self:
            if not record.report or not record.date_start or \
                    not record.date_end or not record.restaurant_id or \
                    not record.check_list_category_ids or record.date_start > record.date_end:

                record.json_top_faults = json.dumps({})
                return
            
            res = self.env['restaurant_management.fault_registry'].get_top_faults(
                record.date_start, record.date_end,
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
                        record.date_start,
                        record.date_end,
                        top_fault[0],
                        restaurant_id=record.restaurant_id.id,
                    )
                ))

            record.json_top_faults = json.dumps(top_faults_with_comments)

    @api.depends("report", "restaurant_id", "date_start", "date_end", "check_list_category_ids")
    def _compute_json_chart(self):
        for record in self:
            if not record.report or not record.date_start or \
                    not record.date_end or not record.restaurant_id or \
                    not record.check_list_category_ids or record.date_start > record.date_end:

                record.json_chart = json.dumps({})
                return
            dataset, maximum = self._get_chart_data(record.date_start, record.date_end)
            data = {
                'labels': self._get_month_range(record.date_start, record.date_end),
                'datasets': dataset,
            }

            options = {
                'responsive': True,
                'maintainAspectRatio': False,
                'title': {
                    'display': True,
                    'text': _('Fault counts within departments'),
                    'fontSize': 25,
                },
                'legend': {
                    'display': True,
                    'labels': {
                        'fontSize': 20,
                    }
                },
                'scales': {
                    'yAxes': [{
                        'scaleLabel': {
                            'display': True,
                            'labelString': _("Fault Count / Audit"),
                            'fontSize': 25,
                        },
                        'ticks': {
                            'suggestedMin': 0,
                            'suggestedMax': maximum + 1,
                            'fontSize': 18,
                        }
                    }],
                    'xAxes': [{
                        'scaleLabel': {
                            'display': True,
                            'labelString': _('Months'),
                            'fontSize': 25,
                        },
                        'ticks': {
                            'fontSize': 18,
                        }
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
        return [short_date(r) for r in rrule(MONTHLY, dtstart=date_start.replace(day=1), until=date_end.replace(day=1))]

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
            color = ",".join(next(COLORS))
            data.append({
                'label': check_list_category_id.name,
                'data': res.get('fault_per_audit', []),

                'fill': False,
                'backgroundColor': f'rgb({color}, 0.8)',
                'labelBackgroundColor': f'rgb({color}, 0.2)',
                "borderColor": f'rgb({color}, 0.5)',
                "labelColor": f'rgb({color})',

                'datalabels': {
                    'anchor': 'end',
                    'align': 'top',
                    'font': {
                        'weight': 'bold',
                        'size': 16
                    }
                }
            })
        return data, max(all_data) if len(all_data) else 2
