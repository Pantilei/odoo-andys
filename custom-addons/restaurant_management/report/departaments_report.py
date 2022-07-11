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


class DepartamentsReport(models.AbstractModel):
    _name = 'report.restaurant_management.departaments_report'
    _description = 'Departaments Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['restaurant_management.fault_registry'].search([])

        restaurant_rating_by_check_list_category = self.env["restaurant_management.fault_registry"].\
            get_restaurant_rating_within_month_for_all_check_list_categories(
                int(data.get("year")),
                int(data.get("month")),
                restaurant_network_id=data.get('restaurant_network_id')
        )
        print("restaurant_rating_per_audit: ",
              restaurant_rating_by_check_list_category)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'restaurant_management.fault_registry',
            'docs': docs,
            'restaurant_rating_by_check_list_category': restaurant_rating_by_check_list_category,
        }
