# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import logging
import traceback
from datetime import datetime, timedelta


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
    def get_audit_fault_counts_per_month(self, report_type):
        audit_counts = [0 for _ in range(12)]
        fault_counts = [0 for _ in range(12)]
        audit_count_per_month = self.env["restaurant_management.restaurant_audit"].with_context(lang="en_US").read_group(
            domain=[
                ('audit_date', '>=', datetime.now().date().replace(month=1, day=1))],
            fields=['restaurant_id'],
            groupby=['audit_date:month'],
        )

        fault_count_per_month = self.env["restaurant_management.fault_registry"].with_context(lang="en_US").read_group(
            domain=[
                ('fault_date', '>=', datetime.now().date().replace(month=1, day=1))],
            fields=['restaurant_id'],
            groupby=['fault_date:month'],
        )

        for row in fault_count_per_month:
            month = datetime.strptime(
                row["__range"]["fault_date"]["from"], "%Y-%m-%d").month
            fault_counts[month-1] = row["fault_date_count"]

        for row in audit_count_per_month:
            month = datetime.strptime(
                row["__range"]["audit_date"]["from"], "%Y-%m-%d").month
            audit_counts[month-1] = row["audit_date_count"]

        return {
            "audit_counts": audit_counts,
            "fault_counts": fault_counts,
        }
