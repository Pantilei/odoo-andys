import os
from datetime import date, datetime

import numpy as np
import pandas as pd

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


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

    active = fields.Boolean(
        string="Archived",
        related='category_id.active'
    )

    @api.onchange("category_id")
    def _on_category_change(self):
        if self.category_id:
            identificators = self.env["restaurant_management.check_list"].search(
                [("category_id", "=", self.category_id.id)]).mapped("identificator")
            self.identificator = max(identificators) + 1 if identificators else 1

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
    def _import_faults_data(self):
        RestaurantAudit = self.env["restaurant_management.restaurant_audit"]
        RestaurantFaultRegistry = self.env["restaurant_management.fault_registry"]

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        df_faults = pd.read_csv(os.path.join(
            path, '../data/may_june_faults.csv')).replace({np.nan: None})

        audits = []
        audit_id = 0
        for record in df_faults.to_dict("records"):
            # print("\n\n", record)
            # if not record['Категория Чек Листа'] or not record['Чек Лист']:
            #     continue

            restaurant_id = self._get_restaurant(record["Ресторан"])
            responsible_id = self._get_responsible(record["Эксперт ДКК"])

            if record['Проверка'] != audit_id:
                audits.append({
                    "restaurant_id": restaurant_id,
                    "responsible_id": responsible_id,
                    "audit_date": datetime.strptime(record['Дата Проверки'], '%d/%m/%Y'),
                    "fault_registry_ids": []
                })

            check_list_category_id = self._get_check_list_category(
                record['Категория Чек Листа'])
            check_list_id = self._get_check_list(
                record['Чек Лист'], check_list_category_id)
            if not all([restaurant_id, responsible_id]):
                print("\n\n")
                print([restaurant_id, responsible_id,
                       check_list_category_id, check_list_id])
                print(record["Ресторан"], record["Эксперт ДКК"], record[
                      'Категория Чек Листа'], record['Чек Лист'])
                raise UserError(" ".join([record["Ресторан"], ": ", record["Эксперт ДКК"], ": ",
                                         record['Категория Чек Листа'], ": ", record['Чек Лист'], ": ", restaurant_id, ": ", responsible_id,
                                         ": ", check_list_category_id, ": ", check_list_id]))

            if check_list_category_id or check_list_id:
                audits[-1]["fault_registry_ids"].append((0, 0, {
                    "check_list_category_id": check_list_category_id,
                    "check_list_id": check_list_id,
                    "fault_count": int(record['Количество Ошибок'] or 0),
                    "severe": record['Грубая ошибка'] or False,
                    "comment": record['Принятые меры Эксперт ДКК'] or False,
                    "director_comment": record['Принятые меры Директор Ресторана'] or False,
                    "check_list_category_responsible_comment": record['Принятые меры Ответственные по департаменту'] or False
                }))
            audit_id = record['Проверка']

        RestaurantAudit.create(audits)

    def _get_restaurant(self, name):
        Restaurant = self.env["restaurant_management.restaurant"]
        return Restaurant.search([("name", "=", name)], limit=1).id

    def _get_responsible(self, name):
        ResUsers = self.env["res.users"]
        return ResUsers.search([("name", "=", name)], limit=1).id

    def _get_check_list_category(self, name):
        if not name:
            return False
        CheckListCategory = self.env["restaurant_management.check_list_category"]
        mod_name = name.strip()[:-2]
        check_list_category_id = CheckListCategory.search(
            [("name", "ilike", mod_name)], limit=1)

        return check_list_category_id.id

    def _get_check_list(self, name, check_list_category_id):
        if not name:
            return False
        CheckList = self.env["restaurant_management.check_list"]
        mod_name = name[4:-2].strip()
        check_list_id = CheckList.search(
            [("name", "ilike", mod_name), ('category_id', '=', check_list_category_id)], limit=1)
        # check_list_id = CheckList.search(
        #     [("full_identificator", "=", mod_name.split(" ")[0]), ('category_id', '=', check_list_category_id)], limit=1)

        return check_list_id.id
