from odoo import fields, models, api


class FaultListReport(models.AbstractModel):
    _name = 'report.restaurant_management.report_fault_list'
    _description = 'report list'

    def _get_report_values(self, docids, data=None):
        docs = self.env['restaurant_management.fault_registry'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'restaurant_management.fault_registry',
            'docs': docs
        }
