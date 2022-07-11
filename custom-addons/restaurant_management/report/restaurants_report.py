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
        return get_char_svg(
            list(zip(MONTHS_INT, MONTHS)),
            data.get("fault_counts"),
            data.get("fault_per_audit"),
            ['Кол-во ошибок', 'Кол-во ошибок/1 проверку'],
        )
