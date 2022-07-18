# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import expression
from ..tools import short_date
import requests
import logging
import traceback
from datetime import datetime, timedelta, date
from dateutil.rrule import rrule, MONTHLY
from calendar import monthrange


requests.packages.urllib3.util.connection.HAS_IPV6 = False

_logger = logging.getLogger(__name__)


class FaultRegistry(models.Model):
    _name = 'restaurant_management.fault_registry'
    _description = 'Fault Registry'
    _order = "id desc"
    _rec_name = "check_list_id"

    @api.depends('check_list_category_id')
    def _compute_no_fault_check_list_category(self):
        for record in self:
            if record.check_list_category_id:
                record.no_fault_check_list_category = record.check_list_category_id.no_fault_category
            else:
                record.no_fault_check_list_category = False

    @api.depends("restaurant_id")
    def _compute_restaurant_directors(self):
        for record in self:
            if record.restaurant_id:
                record.restaurant_director_ids = record.restaurant_id.director_ids.ids
            else:
                record.restaurant_director_ids = False

    state = fields.Selection(selection=[
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancel'),
    ], default="confirm", string="Status")

    fault_type = fields.Selection(selection=[
        ("cook", "Cook"),
        ("suchif", "Suchif"),
        ("waiter", "Waiter"),
        ("tech_personal", "Tech Personal"),
        ("barman", "Barman"),
        ("delivery", "Delivery"),
    ], string="Involved Worker Position")

    guilty_person_id = fields.Many2one(
        comodel_name="res.partner",
        string="Involved Worker Name/Family Name"
    )

    severe = fields.Boolean(
        string="Severe Fault",
        default=False
    )

    fault_count = fields.Integer(
        string="Fault Count",
        default=1
    )

    restaurant_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant",
        string="Restaurant",
        compute="_compute_restaurant",
        store=True
    )
    restaurant_director_ids = fields.Many2many(
        comodel_name="res.users",
        string="Restaurant Directors",
        compute="_compute_restaurant_directors"
    )
    fault_date = fields.Date(
        compute="_compute_fault_date",
        store=True
    )
    restaurant_audit_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant_audit",
        ondelete="cascade"
    )
    check_list_category_id = fields.Many2one(
        comodel_name="restaurant_management.check_list_category",
        required=True,
        string="Check List Category"
    )
    no_fault_check_list_category = fields.Boolean(
        compute="_compute_no_fault_check_list_category"
    )
    check_list_id = fields.Many2one(
        comodel_name="restaurant_management.check_list",
        string="Check List"
    )
    responsible_id = fields.Many2one(
        comodel_name="res.users",
        compute="_compute_responsible",
        store=True,
        string="Expert DCC"
    )

    comment = fields.Text(
        string="Expert DCC comment"
    )

    director_comment = fields.Text(
        string="Taken Measures by Restaurant Director"
    )

    check_list_category_responsible_comment = fields.Text(
        string="Taken Measures by Responsible within Department "
    )

    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        string="Photos"
    )

    available_for_edit = fields.Boolean(
        compute="_compute_available_for_edit",
        string="Availabe for Edit"
    )

    @api.depends("create_date")
    def _compute_available_for_edit(self):
        for record in self:
            record.available_for_edit = record.restaurant_audit_id.available_for_edit

    @api.onchange("check_list_category_id")
    def onchange_check_list_category(self):
        self.check_list_id = False

    @api.depends("restaurant_audit_id")
    def _compute_responsible(self):
        for record in self:
            if record.restaurant_audit_id:
                record.responsible_id = record.restaurant_audit_id.responsible_id.id

    @api.depends("restaurant_audit_id")
    def _compute_restaurant(self):
        for record in self:
            if record.restaurant_audit_id:
                record.restaurant_id = record.restaurant_audit_id.restaurant_id.id

    @api.depends("restaurant_audit_id")
    def _compute_fault_date(self):
        for record in self:
            if record.restaurant_audit_id:
                record.fault_date = record.restaurant_audit_id.audit_date

    def cancel(self):
        self.write({
            "state": "cancel"
        })

    def confirm(self):
        self.write({
            "state": "confirm"
        })

    @api.model
    def get_fault_counts_per_month_rpc(self):
        today = date.today()
        year = today.year
        month = today.month

        date_start = date(year=year-1, month=month, day=1)
        date_end = date(year=year, month=month,
                        day=monthrange(year, month)[1])
        months = [short_date(d) for d in rrule(MONTHLY,
                                               dtstart=date_start, until=date_end)]

        return {
            "months": months,
            "fault_counts_per_month": self.get_fault_counts_per_month(date_start, date_end)
        }

    @api.model
    def get_fault_counts_per_month(self, date_start, date_end,
                                   check_list_category_id=None,
                                   restaurant_id=None, restaurant_network_id=None):

        FaultRegistryModel = self.env["restaurant_management.fault_registry"]
        domain = [
            ('fault_date', '>=', date_start),
            ('fault_date', '<=', date_end),
            ('state', '=', 'confirm')
        ]
        if check_list_category_id:
            domain = expression.AND([
                [("check_list_category_id", "=", check_list_category_id)],
                domain
            ])
        if restaurant_id:
            domain = expression.AND([
                [("restaurant_id", "=", restaurant_id)],
                domain
            ])
        if restaurant_network_id:
            domain = expression.AND([
                [("restaurant_id.restaurant_network_id", "=", restaurant_network_id)],
                domain
            ])

        fault_count_per_month = FaultRegistryModel.read_group(
            domain=domain,
            fields=['fault_count'],
            groupby=['fault_date:month'],
        )

        month_range = list(rrule(MONTHLY, dtstart=date_start, until=date_end))
        fault_counts = [0 for _ in range(len(month_range))]

        for m_i, month in enumerate(month_range):
            for row in fault_count_per_month:
                d = datetime.strptime(
                    row["__range"]["fault_date"]["from"], "%Y-%m-%d")
                if d.month == month.month and d.year == month.year:
                    fault_counts[m_i] = row["fault_count"]

        audit_counts = self.env["restaurant_management.restaurant_audit"]\
            .get_audit_counts_per_month(
                date_start, date_end,
                restaurant_id=restaurant_id,
                restaurant_network_id=restaurant_network_id
        )

        fault_per_audit = [round(fault_count/audit_count, 2)if audit_count else 0 for audit_count,
                           fault_count in zip(audit_counts["actual"], fault_counts)]

        return {
            "fault_per_audit": fault_per_audit,
            "fault_counts": fault_counts,
        }

    @api.model
    def get_restaurant_rating_monthly_data(self, date_start, date_end,
                                           restaurant_id, check_list_category_id=None):
        Restaurant = self.env["restaurant_management.restaurant"]
        if isinstance(restaurant_id, int):
            restaurant_id = Restaurant.browse(restaurant_id)
        restaurant_rating_per_month = []
        for r_date in rrule(MONTHLY, dtstart=date_start, until=date_end):
            restaurant_ratings = self.get_restaurant_rating_data(
                r_date, check_list_category_id=check_list_category_id)
            for idx, d in enumerate(restaurant_ratings):
                if d[0] == restaurant_id.id:
                    restaurant_rating_per_month.append(idx+1)

        return restaurant_rating_per_month

    @api.model
    def get_restaurant_rating_data(self, report_date,
                                   restaurant_network_id=None,
                                   check_list_category_id=None):
        Restaurant = self.env["restaurant_management.restaurant"]
        FaultRegistry = self.env["restaurant_management.fault_registry"]

        restaurant_domain = []
        if restaurant_network_id:
            restaurant_domain = [
                ("restaurant_network_id", "=", restaurant_network_id)
            ]

        res = []
        for restaurant_id in Restaurant.search(restaurant_domain):
            domain = [
                ('fault_date', '>=', date(
                    year=report_date.year, month=report_date.month, day=1)),
                ('fault_date', '<=', date(year=report_date.year,
                                          month=report_date.month,
                                          day=monthrange(report_date.year, report_date.month)[1])),
                ('state', '=', 'confirm')
            ]
            if check_list_category_id:
                domain = expression.AND([
                    [('check_list_category_id', '=', check_list_category_id)],
                    domain
                ])
            domain = expression.AND([
                [("restaurant_id", "=", restaurant_id.id)],
                domain
            ])
            restaurant_faults = FaultRegistry.search(domain)

            fault_count = sum(restaurant_faults.mapped("fault_count"))

            res.append([restaurant_id.id, restaurant_id.name, fault_count])

        if len(res) > 1:
            res.sort(key=lambda r: r[2])

        return res

    @api.model
    def get_restaurant_rating_per_audit_data(self, report_date,
                                             restaurant_network_id=None,
                                             check_list_category_id=None):
        Restaurant = self.env["restaurant_management.restaurant"]
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        FaultAudit = self.env["restaurant_management.restaurant_audit"]
        date_start = date(year=report_date.year,
                          month=report_date.month, day=1)
        date_end = date(year=report_date.year,
                        month=report_date.month,
                        day=monthrange(report_date.year, report_date.month)[1])

        restaurant_domain = []
        if restaurant_network_id:
            restaurant_domain = [
                ("restaurant_network_id", "=", restaurant_network_id)]
        res = []
        for restaurant_id in Restaurant.search(restaurant_domain):
            domain = [
                ('fault_date', '>=', date_start),
                ('fault_date', '<=', date_end),
                ('state', '=', 'confirm')
            ]
            if check_list_category_id:
                domain = expression.AND([
                    [('check_list_category_id', '=', check_list_category_id)],
                    domain
                ])
            domain = expression.AND([
                [("restaurant_id", "=", restaurant_id.id)],
                domain
            ])
            restaurant_faults = FaultRegistry.search(domain)

            fault_count = sum(restaurant_faults.mapped("fault_count"))

            actual_count_of_audits = FaultAudit\
                .get_audit_counts_per_month(date_start, date_end, restaurant_id=restaurant_id.id)["actual"][0]

            res.append(
                [restaurant_id.id, restaurant_id.name, round(fault_count/actual_count_of_audits, 2) if actual_count_of_audits else 0])

        if len(res) > 1:
            res.sort(key=lambda r: r[2])

        return res

    @api.model
    def get_top_faults(self, date_start, date_end,
                       check_list_category_id=None,
                       restaurant_id=None,
                       restaurant_network_id=None):

        FaultRegistryModel = self.env["restaurant_management.fault_registry"]
        domain = [
            ('fault_date', '>=', date_start),
            ('fault_date', '<=', date_end),
            ('state', '=', 'confirm')
        ]
        if check_list_category_id:
            domain = expression.AND([
                [("check_list_category_id", "=", check_list_category_id)],
                domain
            ])
        if restaurant_id:
            domain = expression.AND([
                [("restaurant_id", "=", restaurant_id)],
                domain
            ])
        if restaurant_network_id:
            domain = expression.AND([
                [("restaurant_id.restaurant_network_id", "=", restaurant_network_id)],
                domain
            ])

        grouped_fault_count = FaultRegistryModel.read_group(
            domain=domain,
            fields=['fault_count'],
            groupby=['check_list_id'],
        )
        fault_count_data = [
            (f['check_list_id'][0], f['check_list_id'][1]._value, f["fault_count"])
            for f in grouped_fault_count if f['check_list_id']
        ]

        fault_count_data.sort(key=lambda r: r[2], reverse=True)

        return fault_count_data

    def get_director_comments_of_faults(self, date_start, date_end, check_list_id):
        FaultRegistryModel = self.env["restaurant_management.fault_registry"]
        comments = FaultRegistryModel.search([
            ("check_list_id", "=", check_list_id),
            ("fault_date", ">=", date_start),
            ("fault_date", "<=", date_end),
            ('state', '=', 'confirm')
        ]).mapped("director_comment")

        return "<hr/>".join([c for c in comments if c])

    def get_comments_of_faults(self, date_start, date_end, check_list_id):
        FaultRegistryModel = self.env["restaurant_management.fault_registry"]
        comments = FaultRegistryModel.search([
            ("check_list_id", "=", check_list_id),
            ("fault_date", ">=", date_start),
            ("fault_date", "<=", date_end),
            ('state', '=', 'confirm')
        ]).mapped("comment")

        return "<hr/>".join([c for c in comments if c])

    # @api.model
    # def get_restaurant_rating_within_month_for_all_check_list_categories(
    #     self,
    #     year,
    #     month,
    #     restaurant_network_id=None
    # ):
    #     data = []
    #     for check_list_category_id in self.env["restaurant_management.check_list_category"].search([]):
    #         ordered_absolute_fault_count_per_restaurant = self.get_restaurant_absolute_rating_within_month_and_check_list_category(
    #             year,
    #             month,
    #             check_list_category_id=check_list_category_id.id,
    #             restaurant_network_id=restaurant_network_id
    #         )
    #         ordered_relative_fault_count_per_restaurant = self.get_restaurant_relative_rating_within_month_and_check_list_category(
    #             year,
    #             month,
    #             check_list_category_id=check_list_category_id.id,
    #             restaurant_network_id=restaurant_network_id
    #         )
    #         data.append({
    #             "id": check_list_category_id.id,
    #             "name": check_list_category_id.name,
    #             "restaurants_absolute_rating": ordered_absolute_fault_count_per_restaurant,
    #             "restaurants_relative_rating": ordered_relative_fault_count_per_restaurant
    #         })

    #     return data

    # @api.model
    # def get_restaurant_absolute_rating_within_month_and_check_list_category(
    #     self,
    #     year,
    #     month,
    #     check_list_category_id=None,
    #     restaurant_network_id=None
    # ):
    #     domain = [
    #         ("fault_date", ">=", date(year=year, month=month, day=1)),
    #         ("fault_date", "<=", date(year=year, month=month, day=31)),
    #     ]
    #     if restaurant_network_id:
    #         domain = expression.AND([
    #             [("restaurant_id.restaurant_network_id", "=", restaurant_network_id)],
    #             domain
    #         ])
    #     if check_list_category_id:
    #         domain = expression.AND([
    #             [("check_list_category_id", "=", check_list_category_id)],
    #             domain
    #         ])

    #     fault_count_per_restaurant = self.env["restaurant_management.fault_registry"]\
    #         .read_group(
    #         domain=domain,
    #         fields=['restaurant_id'],
    #         groupby=['restaurant_id'],
    #     )

    #     res = [{
    #         "id": r["restaurant_id"][0],
    #         "name": self.env["restaurant_management.restaurant"].browse(r["restaurant_id"][0]).name,
    #         "count": r["restaurant_id_count"]
    #     } for r in fault_count_per_restaurant]

    #     print("\n\n\n\n", "res:",
    #           res)

    #     res.sort(key=lambda r: r["count"])

    #     return res

    # def get_restaurant_relative_rating_within_month_and_check_list_category(
    #     self,
    #     year,
    #     month,
    #     check_list_category_id = None,
    #     restaurant_network_id = None
    # ):
    #     domain=[
    #         ("fault_date", ">=", date(year=year, month=month, day=1)),
    #         ("fault_date", "<=", date(year=year, month=month, day=31)),
    #     ]
    #     if restaurant_network_id:
    #         domain = expression.AND([
    #             [("restaurant_id.restaurant_network_id", "=", restaurant_network_id)],
    #             domain
    #         ])
    #     if check_list_category_id:
    #         domain = expression.AND([
    #             [("check_list_category_id", "=", check_list_category_id)],
    #             domain
    #         ])

    #     fault_count_per_restaurant = self.env["restaurant_management.fault_registry"]\
    #         .read_group(
    #         domain=domain,
    #         fields=['restaurant_id'],
    #         groupby=['restaurant_id'],
    #     )

    #     res = [{
    #         "id": r["restaurant_id"][0],
    #         "name": self.env["restaurant_management.restaurant"].browse(r["restaurant_id"][0]).name,
    #         "count": r["restaurant_id_count"]/self.env["restaurant_management.restaurant_audit"]
    #         .search_count([
    #             ('restaurant_id', '=', r["restaurant_id"][0]),
    #             ("audit_date", ">=", date(year=year, month=month, day=1)),
    #             ("audit_date", "<=", date(year=year, month=month, day=31)),
    #         ])
    #     } for r in fault_count_per_restaurant]

    #     res.sort(key=lambda r: r["count"])

    #     return res
