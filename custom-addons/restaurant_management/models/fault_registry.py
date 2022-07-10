# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import expression

import requests
import logging
import traceback
from datetime import datetime, timedelta, date


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
    ], default="confirm")

    fault_type = fields.Selection(selection=[
        ("cook", "Cook"),
        ("suchif", "Suchif"),
        ("waiter", "Waiter"),
        ("tech_personal", "Tech Personal"),
        ("barman", "Barman"),
        ("delivery", "Delivery"),
    ])

    guilty_person_id = fields.Many2one(
        comodel_name="res.partner",
        string="Guilty Person"
    )

    severe = fields.Boolean(
        string="Severe Fault",
        default=False
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
        required=True
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
        string="Expert DKK"
    )

    comment = fields.Text(
        string="Expert DKK Comment"
    )

    director_comment = fields.Text(
        string="Restaurant Director Comment"
    )

    check_list_category_responsible_comment = fields.Text(
        string="Fault Category Responsible Comment"
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
    def get_fault_counts_per_month(self, year, check_list_category_id=None, restaurant_id=None, restaurant_network_id=None):

        domain = [
            ('fault_date', '>=', date(year=year, month=1, day=1)),
            ('fault_date', '<=', date(year=year, month=12, day=31)),
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

        fault_counts = [0 for _ in range(12)]

        fault_count_per_month = self.env["restaurant_management.fault_registry"].with_context(lang="en_US").read_group(
            domain=domain,
            fields=['restaurant_id'],
            groupby=['fault_date:month'],
        )

        for row in fault_count_per_month:
            month = datetime.strptime(
                row["__range"]["fault_date"]["from"], "%Y-%m-%d").month
            fault_counts[month-1] = row["fault_date_count"]

        audit_counts = self.env["restaurant_management.restaurant_audit"]\
            .get_audit_counts_per_month(year, restaurant_id=restaurant_id, restaurant_network_id=restaurant_network_id)
        fault_per_audit = [round(fault_count/audit_count, 2)if audit_count else 0 for audit_count,
                           fault_count in zip(audit_counts["actual"], fault_counts)]

        return {
            "fault_per_audit": fault_per_audit,
            "fault_counts": fault_counts,
        }

    @api.model
    def get_restaurant_rating_data(self, year, restaurant_network_id=None, check_list_category_id=None):
        restaurant_domain = []
        if restaurant_network_id:
            restaurant_domain = [
                ("restaurant_network_id", "=", restaurant_network_id)]

        res = []
        for restaurant_id in self.env["restaurant_management.restaurant"].search(restaurant_domain):
            domain = [
                ('fault_date', '>=', date(year=year, month=1, day=1)),
                ('fault_date', '<=', date(year=year, month=12, day=31)),
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
            fault_count_per_month = self.env["restaurant_management.fault_registry"]\
                .with_context(lang="en_US")\
                .read_group(
                    domain=domain,
                    fields=['restaurant_id'],
                    groupby=['fault_date:month'],
            )
            fault_counts = [0 for _ in range(12)]

            for row in fault_count_per_month:
                month = datetime.strptime(
                    row["__range"]["fault_date"]["from"], "%Y-%m-%d").month
                fault_counts[month-1] = row["fault_date_count"]

            all_count = sum(fault_counts)
            res.append([restaurant_id.name, *fault_counts, all_count])

        if len(res) > 1:
            res.sort(key=lambda r: r[len(r)-1])

        return res

    @api.model
    def get_restaurant_rating_per_audit_data(self, year, restaurant_network_id=None, check_list_category_id=None):
        restaurant_domain = []
        if restaurant_network_id:
            restaurant_domain = [
                ("restaurant_network_id", "=", restaurant_network_id)]
        res = []
        for restaurant_id in self.env["restaurant_management.restaurant"].search(restaurant_domain):
            domain = [
                ('fault_date', '>=', date(year=year, month=1, day=1)),
                ('fault_date', '<=', date(year=year, month=12, day=31)),
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
            fault_count_per_month = self.env["restaurant_management.fault_registry"]\
                .with_context(lang="en_US")\
                .read_group(
                    domain=domain,
                    fields=['restaurant_id'],
                    groupby=['fault_date:month'],
            )
            fault_counts = [0 for _ in range(12)]

            for row in fault_count_per_month:
                month = datetime.strptime(
                    row["__range"]["fault_date"]["from"], "%Y-%m-%d").month
                fault_counts[month-1] = row["fault_date_count"]

            actual_count_of_audits = self.env["restaurant_management.restaurant_audit"]\
                .get_audit_counts_per_month(year, restaurant_id=restaurant_id.id)["actual"]

            relative_count_of_faults = [
                round(f/ac, 2) if ac else 0 for f, ac in zip(fault_counts, actual_count_of_audits)
            ]

            all_count_relative = round(sum(relative_count_of_faults)/12, 2)
            res.append(
                [restaurant_id.name, *relative_count_of_faults, all_count_relative])

        if len(res) > 1:
            res.sort(key=lambda r: r[len(r)-1])

        return res
