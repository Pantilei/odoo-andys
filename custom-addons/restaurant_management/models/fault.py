from odoo import models, fields, api
import pandas as pd
import os


class Fault(models.Model):
    _name = "restaurant_management.fault"
    _description = "Faults"
    _rec_name = "description"

    description = fields.Text()
    category_id = fields.Many2one(
        comodel_name="restaurant_management.fault_category",
        required=True
    )

    @api.model
    def _create_faults_and_categories(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        df_category = pd.read_csv(os.path.join(
            path, '../data/fault_category.csv'))
        df_fault = pd.read_csv(os.path.join(path, '../data/fault.csv'))

        result_categ = [self.create_categs(name)
                        for name in df_category['name']]
        result_fault = [self.create_faults(categ_name, description)
                        for categ_name, description in zip(df_fault["category_id"], df_fault["description"])]

    def create_categs(self, name):
        Category = self.env["restaurant_management.fault_category"]
        categ_id = Category.search([('name', '=', name)])
        if categ_id:
            return
        Category.create({
            "name": name
        })
        self.env.cr.commit()

    def create_faults(self, category_name, description):
        print(category_name, description, "\n\n\n\n")
        category_id = self.env["restaurant_management.fault_category"].search([
            ('name', '=', category_name)
        ], limit=1).id
        print(category_id, "\n\n")
        Fault = self.env["restaurant_management.fault"]
        fault = Fault.search(
            [("description", "=", description), ("category_id.name", "=", category_name)])
        if fault:
            return
        Fault.create({
            "description": description,
            "category_id": self.env["restaurant_management.fault_category"].search([
                ('name', 'ilike', category_name)], limit=1).id
        })
