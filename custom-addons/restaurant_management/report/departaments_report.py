from ..tools import get_double_y_axis_chart_png, short_date
from odoo import fields, models, api, _
from datetime import date
from calendar import monthrange
from dateutil.rrule import rrule, MONTHLY
from markupsafe import Markup


MONTHS = [
    _("Jan"),
    _("Feb"),
    _("Mar"),
    _("Apr"),
    _("May"),
    _("Jun"),
    _("Jul"),
    _("Aug"),
    _("Sept"),
    _("Oct"),
    _("Nov"),
    _("Dec"),
]

MONTHS_INT = list(range(12))


class DepartamentsReport(models.AbstractModel):
    _name = 'report.restaurant_management.departaments_report'
    _description = 'Departaments Report'

    def _get_report_values(self, docids, data=None):
        RestaurantAudit = self.env["restaurant_management.restaurant_audit"]
        RestaurantNetwork = self.env["restaurant_management.restaurant_network"]
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        FaultCategory = self.env["restaurant_management.check_list_category"]

        year = int(data.get("year"))
        month = int(data.get("month"))

        check_list_category_id = data.get("check_list_category_id")
        if isinstance(check_list_category_id, int):
            check_list_category_id = FaultCategory.browse(
                check_list_category_id)

        restaurant_network_ids = data.get('restaurant_network_ids')
        if len(restaurant_network_ids) and isinstance(restaurant_network_ids[0], int):
            restaurant_network_ids = RestaurantNetwork.browse(
                restaurant_network_ids)

        year_start = int(data.get("year_start"))
        month_start = int(data.get("month_start"))
        year_end = int(data.get("year_end"))
        month_end = int(data.get("month_end"))

        report_date = date(year=year, month=month, day=1)
        date_start = date(year=year_start, month=month_start, day=1)
        date_end = date(year=year_end, month=month_end,
                        day=monthrange(year_end, month_end)[1])
        months = [short_date(d) for d in rrule(MONTHLY,
                                               dtstart=date_start, until=date_end)]

        dynamics_of_faults_png = self._get_dynamics_of_faults_png(
            date_start, date_end, list(enumerate(months)),
            restaurant_network_ids=restaurant_network_ids.ids,
            check_list_category_id=check_list_category_id.id)

        restaurant_rating = FaultRegistry.get_restaurant_rating_data(
            report_date,
            restaurant_network_ids=restaurant_network_ids.ids,
            check_list_category_id=check_list_category_id.id)

        restaurant_rating_per_audit = FaultRegistry.get_restaurant_rating_per_audit_data(
            report_date,
            restaurant_network_ids=restaurant_network_ids.ids,
            check_list_category_id=check_list_category_id.id)

        top_faults = FaultRegistry.get_top_faults(
            date(year=year, month=month, day=1),
            date(year=year, month=month, day=monthrange(year, month)[1]),
            check_list_category_id=check_list_category_id.id,
            restaurant_network_ids=restaurant_network_ids.ids)

        top_faults_with_comments = [
            (
                top_fault[0],
                top_fault[1],
                top_fault[2],
                FaultRegistry.get_category_responsible_comments_of_faults(
                    date(year=year, month=month, day=1),
                    date(year=year, month=month,
                         day=monthrange(year, month)[1]),
                    top_fault[0],
                    # restaurant_network_ids=restaurant_network_ids.ids,
                ),
                FaultRegistry.get_comments_of_faults(
                    date(year=year, month=month, day=1),
                    date(year=year, month=month,
                         day=monthrange(year, month)[1]),
                    top_fault[0],
                    # restaurant_network_ids=restaurant_network_ids.ids,
                ),
            )
            for top_fault in top_faults
        ]
        return {
            'report_date': report_date.strftime('%m/%Y'),

            'check_list_category_name': check_list_category_id.name,

            'dynamics_of_faults_png': dynamics_of_faults_png,

            'restaurant_rating': restaurant_rating,
            'restaurant_rating_per_audit': restaurant_rating_per_audit,

            'months': months,

            'top_faults_with_comments': top_faults_with_comments,
            'Markup': Markup
        }

    def _get_dynamics_of_faults_png(self, date_start, date_end, months,
                                    restaurant_network_ids=None,
                                    check_list_category_id=None):
        data = self.env["restaurant_management.fault_registry"]\
            .get_fault_counts_per_month(
                date_start, date_end,
                restaurant_network_ids=restaurant_network_ids,
                check_list_category_id=check_list_category_id)

        return get_double_y_axis_chart_png(
            months,
            data.get("fault_counts"),
            data.get("fault_per_audit"),
            ['Кол-во ошибок', 'Кол-во ошибок/1 проверку'],
        )
