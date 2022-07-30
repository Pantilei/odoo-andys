from datetime import timedelta, date
from dateutil.rrule import rrule, MONTHLY
from calendar import monthrange
from ..tools import get_double_y_axis_chart_png, short_date
from odoo import fields, models, api, _


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


class RestaurnatsAllReport(models.AbstractModel):
    _name = 'report.restaurant_management.restaurants_all_report'
    _description = 'Restaurants Report'

    def _get_report_values(self, docids, data=None):
        RestaurantAudit = self.env["restaurant_management.restaurant_audit"]
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        FaultCategory = self.env["restaurant_management.check_list_category"]
        RestaurantNetwork = self.env["restaurant_management.restaurant_network"]

        year = int(data.get("year"))
        month = int(data.get("month"))

        year_start = int(data.get("year_start"))
        month_start = int(data.get("month_start"))
        year_end = int(data.get("year_end"))
        month_end = int(data.get("month_end"))

        restaurant_network_ids = data.get("restaurant_network_ids")
        if len(restaurant_network_ids) and isinstance(restaurant_network_ids[0], int):
            restaurant_network_ids = RestaurantNetwork.browse(
                restaurant_network_ids)

        report_date = date(year=year, month=month, day=1)
        date_start = date(year=year_start, month=month_start, day=1)
        date_end = date(year=year_end, month=month_end,
                        day=monthrange(year_end, month_end)[1])
        months = [short_date(d) for d in rrule(MONTHLY,
                                               dtstart=date_start, until=date_end)]

        counts_per_month = RestaurantAudit.get_audit_counts_per_month(
            date_start, date_end, restaurant_network_ids=restaurant_network_ids.ids)

        dynamics_of_faults_png = self._get_dynamics_of_faults_png(
            date_start, date_end, list(enumerate(months)), restaurant_network_ids=restaurant_network_ids.ids)

        fault_category_ids = FaultCategory.search([])
        fault_category_data = [
            (
                fault_category_id.name,
                self._get_dynamics_of_faults_png(
                    date_start, date_end, list(enumerate(months)),
                    restaurant_network_ids=restaurant_network_ids.ids,
                    check_list_category_ids=fault_category_id.ids),
            ) for fault_category_id in fault_category_ids
        ]

        restaurant_rating = FaultRegistry.get_restaurant_rating_data(
            report_date, restaurant_network_ids=restaurant_network_ids.ids)

        restaurant_rating_per_audit = FaultRegistry.get_restaurant_rating_per_audit_data(
            report_date, restaurant_network_ids=restaurant_network_ids.ids)

        return {
            'report_date': report_date.strftime('%m/%Y'),

            'dynamics_of_faults_png': dynamics_of_faults_png,
            'fault_category_data': fault_category_data,

            'restaurant_rating': restaurant_rating,
            'restaurant_rating_per_audit': restaurant_rating_per_audit,

            'months': months,
            'counts_per_month': counts_per_month
        }

    def _get_dynamics_of_faults_png(self, date_start, date_end, months,
                                    check_list_category_id=None,
                                    check_list_category_ids=None,
                                    restaurant_network_id=None,
                                    restaurant_network_ids=None):
        data = self.env["restaurant_management.fault_registry"]\
            .get_fault_counts_per_month(
                date_start, date_end,
                restaurant_network_id=restaurant_network_id,
                check_list_category_id=check_list_category_id,
                restaurant_network_ids=restaurant_network_ids,
                check_list_category_ids=check_list_category_ids)

        return get_double_y_axis_chart_png(
            months,
            data.get("fault_counts"),
            data.get("fault_per_audit"),
            ['Кол-во ошибок', 'Кол-во ошибок/1 проверку'],
        )
