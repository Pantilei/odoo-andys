from ..tools import short_date, get_multi_line_png
from odoo import fields, models, api, _
from datetime import date
from calendar import monthrange
from markupsafe import Markup
from dateutil.rrule import rrule, MONTHLY


class RestaurantReport(models.AbstractModel):
    _name = 'report.restaurant_management.restaurant_report'
    _description = 'Restaurant Report'

    def _get_report_values(self, docids, data=None):
        RestaurantAudit = self.env["restaurant_management.restaurant_audit"]
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        FaultCategory = self.env["restaurant_management.check_list_category"]
        Restaurant = self.env["restaurant_management.restaurant"]

        restaurant_id = data.get("restaurant_id")
        if isinstance(restaurant_id, int):
            restaurant_id = Restaurant.browse(restaurant_id)

        check_list_category_ids = data.get("check_list_category_ids")
        if len(check_list_category_ids) and isinstance(check_list_category_ids[0], int):
            check_list_category_ids = FaultCategory.search(
                [("id", "in", check_list_category_ids)])

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
        months = [short_date(d) for d in rrule(MONTHLY,
                                               dtstart=date_start, until=date_end)]

        audit_counts_per_month = RestaurantAudit.get_audit_counts_per_month(
            date_start, date_end, restaurant_id=restaurant_id.id)

        dynamics_of_rating_png = self._get_rating_dynamics_png(
            restaurant_id,
            check_list_category_ids,
            date_start, date_end,
            list(enumerate(months)))

        relative_fault_count_png = self._get_relative_fault_count_png(
            restaurant_id,
            date_start, date_end,
            list(enumerate(months)))

        top_faults = FaultRegistry.get_top_faults(
            date(year=year, month=month, day=1),
            date(year=year, month=month, day=monthrange(year, month)[1]),
            restaurant_id=restaurant_id.id)
        top_faults_with_comments = [
            (
                top_fault[0],
                top_fault[1],
                top_fault[2],
                FaultRegistry.get_director_comments_of_faults(
                    date(year=year, month=month, day=1),
                    date(year=year, month=month, day=monthrange(
                        year, month)[1]),
                    top_fault[0],
                    restaurant_id=restaurant_id.id
                ),
            )
            for top_fault in top_faults
        ]

        return {
            'restaurant_name': restaurant_id.name,
            'report_date': report_date.strftime('%m/%Y'),
            'dynamics_of_rating_png': dynamics_of_rating_png,
            'relative_fault_count_png': relative_fault_count_png,

            'top_faults_with_comments': top_faults_with_comments,

            'months': months,
            'counts_per_month': audit_counts_per_month,
            'Markup': Markup
        }

    def _get_rating_dynamics_png(self, restaurant_id, check_list_category_ids, date_start, date_end, months):
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        CheckListCategory = self.env["restaurant_management.check_list_category"]

        data = FaultRegistry.get_restaurant_rating_monthly_data(
            date_start, date_end, restaurant_id)
        x_categ = months
        ys = [data]
        legend = [_('All')]

        for category in check_list_category_ids:

            data = FaultRegistry.get_restaurant_rating_monthly_data(
                date_start, date_end,
                restaurant_id,
                check_list_category_id=category.id)
            ys.append(data)
            legend.append(category.name)

        return get_multi_line_png(
            x_categ,
            ys,
            legend,
        )

    def _get_relative_fault_count_png(self, restaurant_id, date_start, date_end, months):
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        fault_counts_per_month_of_restaurant = FaultRegistry.get_fault_counts_per_month(
            date_start, date_end,
            check_list_category_id=None,
            restaurant_id=restaurant_id.id)['fault_per_audit']

        fault_counts_per_month_of_restaurant_network = FaultRegistry.get_fault_counts_per_month(
            date_start, date_end,
            check_list_category_id=None,
            restaurant_network_id=restaurant_id.restaurant_network_id.id)['fault_per_audit']

        x_categ = months
        ys = [fault_counts_per_month_of_restaurant,
              fault_counts_per_month_of_restaurant_network]
        legend = [
            f"{restaurant_id.restaurant_network_id.name} ({_('medium value')})", restaurant_id.name]

        return get_multi_line_png(
            x_categ,
            ys,
            legend,
            legend_loc=(0.35, -0.15),
            figsize=[11, 5]
        )
