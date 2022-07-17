from datetime import timedelta, date
from dateutil.rrule import rrule, MONTHLY
from calendar import monthrange
from ..tools import get_char_svg
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


class RestaurnatsReport(models.AbstractModel):
    _name = 'report.restaurant_management.restaurants_report'
    _description = 'Restaurants Report'

    def _get_report_values(self, docids, data=None):
        # docs = self.env['restaurant_management.fault_registry'].search([])
        RestaurantAudit = self.env["restaurant_management.restaurant_audit"]
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        FaultCategory = self.env["restaurant_management.check_list_category"]

        year = int(data.get("year"))
        month = int(data.get("month"))

        year_start = int(data.get("year_start"))
        month_start = int(data.get("month_start"))
        year_end = int(data.get("year_end"))
        month_end = int(data.get("month_end"))

        report_date = date(year=year, month=month, day=1)
        date_start = date(year=year_start, month=month_start, day=1)
        date_end = date(year=year_end, month=month_end,
                        day=monthrange(year_end, month_end)[1])
        months = [self._short_date(d) for d in rrule(MONTHLY,
                                                     dtstart=date_start, until=date_end)]

        counts_per_month = RestaurantAudit.get_audit_counts_per_month(
            date_start, date_end)

        dynamics_of_faults_png = self._get_dynamics_of_faults_png(
            date_start, date_end, list(enumerate(months)))

        fault_category_ids = FaultCategory.search([])
        fault_category_data = [
            (
                fault_category_id.name,
                self._get_dynamics_of_faults_png(
                    date_start, date_end, list(enumerate(months)),
                    check_list_category_id=fault_category_id.id),
            ) for fault_category_id in fault_category_ids
        ]

        restaurant_rating = FaultRegistry.get_restaurant_rating_data(
            report_date)

        restaurant_rating_per_audit = FaultRegistry.get_restaurant_rating_per_audit_data(
            report_date)

        return {
            # 'doc_ids': docids,
            # 'doc_model': 'restaurant_management.fault_registry',
            # 'docs': docs,

            'dynamics_of_faults_png': dynamics_of_faults_png,
            'fault_category_data': fault_category_data,

            'restaurant_rating': restaurant_rating,
            'restaurant_rating_per_audit': restaurant_rating_per_audit,

            'months': months,
            'counts_per_month': counts_per_month
        }

    def _short_date(self, dt):
        a = dt.strftime('%m/%Y').split('/')
        return "/".join([a[0], a[1][2:]])

    def _get_dynamics_of_faults_png(self, date_start, date_end, months, check_list_category_id=None):
        data = self.env["restaurant_management.fault_registry"]\
            .get_fault_counts_per_month(
                date_start, date_end,
                check_list_category_id=check_list_category_id)

        return get_char_svg(
            months,
            data.get("fault_counts"),
            data.get("fault_per_audit"),
            ['Кол-во ошибок', 'Кол-во ошибок/1 проверку'],
        )
