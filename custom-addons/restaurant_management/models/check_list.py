from odoo import models, fields, api
import pandas as pd
import os


class CheckList(models.Model):
    _name = "restaurant_management.check_list"
    _description = "Check List"
    _rec_name = "description"

    description = fields.Text()
    category_id = fields.Many2one(
        comodel_name="restaurant_management.check_list_category",
        required=True
    )

    @api.model
    def _create_check_lists_and_categories(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        df_category = pd.read_csv(os.path.join(
            path, '../data/check_list_category.csv'))
        df_check_list = pd.read_csv(
            os.path.join(path, '../data/check_list.csv'))

        result_categ = [self.create_categs(name)
                        for name in df_category['name']]
        result_check_list = [self.create_check_list(categ_name, description)
                             for categ_name, description in zip(df_check_list["category_id"], df_check_list["description"])]

    def create_categs(self, name):
        Category = self.env["restaurant_management.check_list_category"]
        categ_id = Category.search([('name', '=', name)])
        if categ_id:
            return
        Category.create({
            "name": name
        })
        self.env.cr.commit()

    def create_check_list(self, category_name, description):
        print(category_name, description, "\n\n\n\n")
        category_id = self.env["restaurant_management.check_list_category"].search([
            ('name', '=', category_name)
        ], limit=1).id
        print(category_id, "\n\n")
        CheckList = self.env["restaurant_management.check_list"]
        check_list = CheckList.search(
            [("description", "=", description), ("category_id.name", "=", category_name)])
        if check_list:
            return
        CheckList.create({
            "description": description,
            "category_id": self.env["restaurant_management.check_list_category"].search([
                ('name', 'ilike', category_name)], limit=1).id
        })
