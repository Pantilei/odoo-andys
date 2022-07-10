import base64
import io
from odoo import fields, models, api, _
from matplotlib import pyplot as plt
from datetime import date
from scipy import interpolate
import warnings

warnings.filterwarnings("ignore")


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


class FaultListReport(models.AbstractModel):
    _name = 'report.restaurant_management.general_report'
    _description = 'General Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['restaurant_management.fault_registry'].search([])

        fault_category_ids = self.env["restaurant_management.check_list_category"].search([
        ])
        fault_category_data = [
            (
                fault_category_id.name,
                self._get_dynamics_of_faults_svg(
                    int(data.get("year")),
                    restaurant_network_id=data.get('restaurant_network_id'),
                    check_list_category_id=fault_category_id.id),
            ) for fault_category_id in fault_category_ids
        ]

        restaurant_rating = self.env["restaurant_management.fault_registry"].\
            get_restaurant_rating_data(
                int(data.get("year")), restaurant_network_id=data.get('restaurant_network_id'))

        restaurant_rating_per_audit = self.env["restaurant_management.fault_registry"].\
            get_restaurant_rating_per_audit_data(
                int(data.get("year")), restaurant_network_id=data.get('restaurant_network_id'))

        counts_per_month = self._get_audit_counts_per_month(
            int(data.get("year")), data.get("restaurant_network_id"))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'restaurant_management.fault_registry',
            'docs': docs,
            'dynamics_of_faults_svg': self._get_dynamics_of_faults_svg(
                int(data.get("year")),
                restaurant_network_id=data.get('restaurant_network_id')),
            'fault_category_data': fault_category_data,
            'restaurant_rating': restaurant_rating,
            'restaurant_rating_per_audit': restaurant_rating_per_audit,
            'months': MONTHS,
            'counts_per_month': counts_per_month
        }

    def _get_audit_counts_per_month(self, year, restaurant_network_id=None):
        return self.env["restaurant_management.restaurant_audit"]\
            .get_audit_counts_per_month(
                year,
                restaurant_id=None,
                restaurant_network_id=restaurant_network_id
        )

    def _get_dynamics_of_faults_svg(self, year, restaurant_network_id, check_list_category_id=None):
        data = self.env["restaurant_management.fault_registry"]\
            .get_fault_counts_per_month(
                year,
                check_list_category_id=check_list_category_id,
                restaurant_id=None,
                restaurant_network_id=restaurant_network_id)
        return self._get_char_svg(
            data.get("fault_counts"),
            data.get("fault_per_audit"),
            ['Кол-во ошибок', 'Кол-во ошибок/1 проверку'],
        )

    def _get_char_svg(self, y1, y2, legend):
        plt.rcParams["figure.figsize"] = [7.50, 3.50]
        plt.rcParams["figure.autolayout"] = True

        ax1 = plt.subplot()
        ax2 = ax1.twinx()

        l1, = ax1.plot(MONTHS, y1, color="red", marker="o")
        l2, = ax2.plot(MONTHS, y2, color="orange", marker="o")
        plt.legend([l1, l2], legend)
        plt.grid()

        # bspline_y1 = interpolate.make_interp_spline(MONTHS_INT, y1)
        # bspline_y2 = interpolate.make_interp_spline(MONTHS_INT, y2)

        # y1_new = bspline_y1([i/10 for i in range(110)])
        # y2_new = bspline_y2([i/10 for i in range(110)])

        # l1, = ax1.plot([i/10 for i in range(110)], y1_new, color="red")
        # l2, = ax2.plot([i/10 for i in range(110)], y2_new, color="orange")
        # plt.legend([l1, l2], ['Кол-во ошибок', 'Кол-во ошибок/1 проверки'])

        # ax1.set_xticks(range(12))
        # ax1.set_xticklabels(MONTHS)

        source = io.BytesIO()
        plt.savefig(source, format="svg")
        plt.close()

        return base64.b64encode(source.getvalue())
