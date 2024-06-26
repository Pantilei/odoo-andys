import itertools
import json
from calendar import monthrange
from datetime import date

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


class DepartamentsReports(models.TransientModel):
    _name = "restaurant_management.departaments_reports_wizard"
    _description = "Wizard to print the departaments reports"

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
        ("restaurant_rating", "Restaurant Rating"),
        ("fault_count_dynamics", "Fault Count Dynamics"),
        ("top_faults", "Top Faults"),
    ],
        default="restaurant_rating",
        required=True
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

    check_list_category_ids = fields.Many2many(
        comodel_name="restaurant_management.check_list_category",
        relation="restaurant_management_clc_dprtm_wizard_rel",
        string="Departments",
        default=_get_default_departaments,
        required=True
    )

    restaurant_network_ids = fields.Many2many(
        comodel_name="restaurant_management.restaurant_network",
        relation="restaurant_management_rn_dprt_rprts_wizard_rel",
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

    @api.depends("report", "restaurant_network_ids", "check_list_category_ids", "date_start", "date_end")
    def _compute_json_restaurant_rating(self):
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        for record in self:
            if not record.report or not record.date_start or \
                    not record.date_end or not record.restaurant_network_ids or \
                    not record.check_list_category_ids or record.date_start > record.date_end:

                record.json_restaurant_rating = json.dumps({
                    "grouped_restaurant_rating_per_audit": [],
                })
                return
            restaurant_rating_per_audit = FaultRegistry.get_restaurant_rating_per_audit_data(
                date_start=record.date_start,
                date_end=record.date_end,
                restaurant_network_ids=record.restaurant_network_ids.ids,
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
            })

    @api.depends("report", "restaurant_network_ids", "check_list_category_ids", "date_start", "date_end")
    def _compute_json_top_faults(self):
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        for record in self:
            if not record.report or not record.date_start or \
                    not record.date_end or not record.restaurant_network_ids or \
                    not record.check_list_category_ids or record.date_start > record.date_end:

                record.json_top_faults = json.dumps({})
                return

            res = self.env['restaurant_management.fault_registry'].get_top_faults(
                record.date_start, record.date_end,
                check_list_category_id=None,
                check_list_category_ids=record.check_list_category_ids.ids,
                restaurant_id=None,
                restaurant_ids=None,
                restaurant_network_id=None,
                restaurant_network_ids=record.restaurant_network_ids.ids
            )
            rows = res[:20] if len(res) >= 20 else res
            top_faults_with_comments = []
            for top_fault in rows:
                top_faults_with_comments.append((
                    top_fault[0],
                    top_fault[1],
                    top_fault[2],
                    FaultRegistry.get_category_responsible_comments_of_faults(
                        record.date_start,
                        record.date_end,
                        top_fault[0],
                        restaurant_network_ids=record.restaurant_network_ids.ids,
                    )
                ))

            record.json_top_faults = json.dumps(top_faults_with_comments)

    @api.depends("report", "date_start", "date_end", "restaurant_network_ids", "check_list_category_ids")
    def _compute_json_chart(self):
        for record in self:
            if not record.report or not record.date_start or \
                    not record.date_end or not record.restaurant_network_ids or \
                    not record.check_list_category_ids or record.date_start > record.date_end:

                record.json_chart = json.dumps({
                    'type': 'bar',
                    'data': {
                        'labels': 0,
                        'datasets': [{
                            'type': 'bar',
                            'label': 0,
                            'data': [0]
                        }]
                    },
                    'options': record._get_chart_options(0, 5),
                })
                return

            chart_data = record._get_chart_data(
                record.date_start, record.date_end, record.check_list_category_ids)

            options = record._get_chart_options(
                chart_data["mean_value"], chart_data["max_value"])
            configs = {
                'type': 'bar',
                'data': chart_data["data"],
                'options': options,
            }

            record.json_chart = json.dumps(configs)

    def _get_month_range(self, date_start, date_end):
        return [
            short_date(r) 
            for r in rrule(MONTHLY, dtstart=date_start.replace(day=1), until=date_end.replace(day=1))
        ]

    def _get_chart_data(self, date_start, date_end, check_list_category_ids):
        Restaurant = self.env["restaurant_management.restaurant"]
        data = []
        labels = []
        all_values = []
        for restaurant_id in Restaurant.search([("restaurant_network_id", "in", self.restaurant_network_ids.ids)]):
            res = self.env['restaurant_management.fault_registry']\
                .get_fault_counts_per_month(
                    date_start,
                    date_end,
                    check_list_category_id=None,
                    restaurant_id=restaurant_id.id,
                    restaurant_network_id=None,
                    check_list_category_ids=check_list_category_ids.ids,
                    restaurant_ids=None,
                    restaurant_network_ids=self.restaurant_network_ids.ids
            )
            data.append(res.get('fault_per_audit', []))
            labels.append(restaurant_id.name)
            all_values = [*all_values, *res.get('fault_per_audit', [])]
        max_value = max(all_values) if len(all_values) else 2
        mean_value = sum(all_values)/len(all_values)
        month_range = self._get_month_range(date_start, date_end)
        datasets = []
        for i, r in enumerate(zip(*data)):
            color = ",".join(next(COLORS))
            datasets.append({
                'type': 'bar',
                'label': month_range[i],
                'data': r,

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
                        'size': 12
                    }
                }
            })
        return {
            "mean_value": mean_value,
            "max_value": max_value,
            "data": {
                'labels': labels,
                'datasets': datasets,
            }
        }

    def _get_chart_options(self, mean_value, max_value):
        return {
            'responsive': True,
            'maintainAspectRatio': False,
            'title': {
                'display': False,
                'text': _('Fault counts within restaurants')
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
                        'suggestedMax': max_value + 1,
                        'fontSize': 18,
                    }
                }],
                'xAxes': [{
                    'scaleLabel': {
                        'display': True,
                        'labelString': _('Restaurants'),
                        'fontSize': 25,
                    },
                    'ticks': {
                        'fontSize': 16,
                    }
                }],
            },

            'annotation': {
                'annotations': [{
                    'drawTime': 'afterDraw',
                    'id': 'a-line-1',
                    'type': 'line',
                    'mode': 'horizontal',
                    'scaleID': 'y-axis-0',
                    'value': round(mean_value, 2),
                    'borderColor': 'red',
                    'borderWidth': 1,
                    'label': {
                        'enabled': True,
                        'position': "center",
                        'content': round(mean_value, 2),
                        'font': {
                            'weight': 'normal',
                            'fontSize': 10
                        },

                    }
                }]
            },
        }
