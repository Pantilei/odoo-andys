from odoo import models, fields, api
from odoo.osv import expression
import pandas as pd
import os


class CheckList(models.Model):
    _name = "restaurant_management.check_list"
    _description = "Check List"
    # _rec_name = "description"
    _order = "sequence"

    @api.depends("identificator", "category_id.identificator")
    def _compute_full_identificator(self):
        for record in self:
            if record.category_id and record.identificator:
                record.full_identificator = f"{record.category_id.identificator}.{record.identificator}"
            elif record.category_id:
                record.full_identificator = f"{record.category_id.identificator}."
            else:
                record.full_identificator = ""

    name = fields.Text(
        compute="_compute_name",
        store=True
    )

    description = fields.Text()

    identificator = fields.Integer(
        string="Itentificator within category",
    )

    full_identificator = fields.Char(
        compute="_compute_full_identificator",
        string="Identificator",
        store=True
    )

    sequence = fields.Integer(
        default=10,
        string="Sequence"
    )
    category_id = fields.Many2one(
        comodel_name="restaurant_management.check_list_category",
        required=True
    )

    @api.onchange("category_id")
    def _on_category_change(self):
        if self.category_id:
            self.identificator = max(self.search(
                [("category_id", "=", self.category_id.id)]).mapped("identificator"))+1

    @api.depends("full_identificator", "description")
    def _compute_name(self):
        for record in self:
            if record.description and record.full_identificator:
                record.name = record.full_identificator + ' ' + record.description
            else:
                record.name = ''

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         name = record.full_identificator + ' ' + record.description
    #         result.append((record.id, name))
    #     return result

    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     args = args or []
    #     domain = []
    #     if name:
    #         domain = ['|',
    #                   ('full_identificator', '=', name.split(' ')[0]),
    #                   ('name', operator, name)
    #                   ]
    #     print(domain)
    #     return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    # Temporary methods, remove when not needed
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

    @api.model
    def _extract_identificator(self):
        for record in self.search([]):
            ident, desc = record.description.split(" ", 1)
            print(int(ident.split(".", 1)[1]))
            print(desc)
            record.identificator = int(ident.split(".", 1)[1])
            record.description = desc
