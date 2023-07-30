# -*- coding: utf-8 -*-

import logging
import traceback
from calendar import monthrange
from datetime import date, datetime, timedelta

import lxml
import requests
from dateutil.rrule import MONTHLY, rrule

from odoo import _, api, fields, models
from odoo.osv import expression

from ..tools import short_date

requests.packages.urllib3.util.connection.HAS_IPV6 = False

_logger = logging.getLogger(__name__)


class FaultRegistry(models.Model):
    _name = 'restaurant_management.fault_registry'
    _description = 'Fault Registry'
    _order = "fault_date desc"
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

    @api.depends("comment")
    def _compute_comment_no_html(self):
        for record in self:
            if record.comment:
                record.comment_no_html = lxml.html.document_fromstring(
                    record.comment).text_content()
            else:
                record.comment_no_html = ""

    @api.depends("director_comment")
    def _compute_director_comment_no_html(self):
        for record in self:
            if record.director_comment:
                record.director_comment_no_html = lxml.html.document_fromstring(
                    record.director_comment).text_content()
            else:
                record.director_comment_no_html = ""

    @api.depends("check_list_category_responsible_comment")
    def _compute_check_list_category_responsible_comment_no_html(self):
        for record in self:
            if record.check_list_category_responsible_comment:
                record.check_list_category_responsible_comment_no_html = lxml.html.document_fromstring(
                    record.check_list_category_responsible_comment).text_content()
            else:
                record.check_list_category_responsible_comment_no_html = ""

    state = fields.Selection(selection=[
        ('pending', 'Pending'),
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
        ("restaurant_director", "Restaurant Director"),
        ("delivery_department_manager", "Delivery Department Manager"),
        ("interier_department_manager", "Interier Department Manager"),
        ("marketing_department_manager", "Marketing Departemnt Manager"),
        ("waiter_department_manager", "Waiter Department Manager"),
        ("it_department_manager", "IT Department Manager"),
        ("supplier_department_manager", "Supplier Department Manager"),
        ("technical_department_manager", "Technical Department Manager"),
        ("factory_director", "Factory Director")
    ], string="Involved Worker Position", index=True)

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
        index=True,
        string="Restaurant",
        compute="_compute_restaurant",
        store=True,
        ondelete="restrict"
    )
    restaurant_network_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant_network",
        index=True,
        string="Restaurant Network",
        related="restaurant_id.restaurant_network_id",
        readonly=False,
        store=True,
        ondelete="restrict"
    )

    restaurant_director_ids = fields.Many2many(
        comodel_name="res.users",
        string="Restaurant Directors",
        compute="_compute_restaurant_directors"
    )
    fault_date = fields.Date(
        compute="_compute_fault_date",
        store=True,
        index=True
    )
    restaurant_audit_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant_audit",
        ondelete="cascade"
    )
    check_list_category_id = fields.Many2one(
        comodel_name="restaurant_management.check_list_category",
        index=True,
        required=True,
        string="Check List Category",
        ondelete="restrict"
    )
    no_fault_check_list_category = fields.Boolean(
        compute="_compute_no_fault_check_list_category"
    )
    check_list_id = fields.Many2one(
        comodel_name="restaurant_management.check_list",
        index=True,
        string="Check List",
        ondelete="restrict"
    )

    check_check_list_identificator = fields.Char(
        related="check_list_id.full_identificator",
        string="Identificator",
        store=True
    )

    responsible_id = fields.Many2one(
        comodel_name="res.users",
        compute="_compute_responsible",
        store=True,
        string="Auditer"
    )

    comment = fields.Text(
        string="Сomment"
    )

    director_comment = fields.Text(
        string="Taken Measures by Restaurant Director"
    )

    check_list_category_responsible_comment = fields.Text(
        string="Taken Measures by Responsible within Department "
    )

    comment_no_html = fields.Text(
        string="Сomment (No HTML)",
        compute="_compute_comment_no_html"
    )

    director_comment_no_html = fields.Text(
        string="Taken Measures by Restaurant Director (No HTML)",
        compute="_compute_director_comment_no_html"
    )

    check_list_category_responsible_comment_no_html = fields.Text(
        string="Taken Measures by Responsible within Department (No HTML)",
        compute="_compute_check_list_category_responsible_comment_no_html"
    )

    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        string="Photos"
    )

    attachment_exists = fields.Boolean(
        string="Photos",
        compute="_compute_attachment_exists"
    )

    available_for_edit = fields.Boolean(
        compute="_compute_available_for_edit",
        string="Availabe for Edit"
    )

    fault_occurrence_info = fields.Html(
        string="Fault Occurrence",
        compute="_compute_fault_occurance",
    )

    fault_present = fields.Selection(
        selection=[
            ("yes", "Yes"),
            ("no", "No")
        ],
        string="Fault Present",
        index=True
    )
    grade = fields.Integer(
        string="Grade",
        index=True
    )

    check_list_type_id = fields.Many2one(
        comodel_name="restaurant_management.check_list_type",
        related="restaurant_audit_id.check_list_type_id",
        string="Check List Type",
        store=True
    )

    is_qcd_check_list_type = fields.Boolean(
        compute="_compute_check_list_type"
    )

    is_video_surveillance_check_list_type = fields.Boolean(
        compute="_compute_check_list_type"
    )

    is_secret_guest_check_list_type = fields.Boolean(
        compute="_compute_check_list_type"
    )

    @api.depends("attachment_ids")
    def _compute_attachment_exists(self):
        for record in self:
            record.attachment_exists = len(record.attachment_ids) != 0

    def _compute_check_list_type(self):
        qcd_check_list_type = self.env.ref("restaurant_management.qcd_check_list_type")
        video_surveillance_check_list_type = self.env.ref("restaurant_management.video_surveillance_check_list_type")
        secret_guest_check_list_type = self.env.ref("restaurant_management.secret_guest_check_list_type")
        for record in self:
            record.is_qcd_check_list_type = record.check_list_type_id == qcd_check_list_type
            record.is_video_surveillance_check_list_type = record.check_list_type_id == video_surveillance_check_list_type
            record.is_secret_guest_check_list_type = record.check_list_type_id == secret_guest_check_list_type

    @api.depends("check_list_id", "restaurant_id", "fault_date")
    def _compute_fault_occurance(self):
        for record in self:
            if record.check_list_id and record.restaurant_id and record.fault_date:
                count = sum(self.search([
                    ("check_list_id", "=", record.check_list_id.id),
                    ("restaurant_id", "=", record.restaurant_id.id),
                    ("fault_date", ">=", record.fault_date - timedelta(days=30))
                ]).mapped("fault_count"))
                record.fault_occurrence_info = _(f"""
                    <p class="{'text-danger' if count >= 2 else 'text-warning' if count == 1 else 'text-primary'}">Эта ошибка повторилась <strong>{count}</strong> раз за последние 30 дней внутри этого департамента и ресторана!</p>
                """)
            else:
                record.fault_occurrence_info = False

    @api.depends("create_date")
    def _compute_available_for_edit(self):
        for record in self:
            record.available_for_edit = record.restaurant_audit_id.available_for_edit

    @api.onchange("check_list_category_id")
    def onchange_check_list_category(self):
        self.check_list_id = False

    @api.depends("restaurant_audit_id.responsible_id")
    def _compute_responsible(self):
        for record in self:
            if record.restaurant_audit_id:
                record.responsible_id = record.restaurant_audit_id.responsible_id.id

    @api.depends("restaurant_audit_id.restaurant_id")
    def _compute_restaurant(self):
        for record in self:
            if record.restaurant_audit_id:
                record.restaurant_id = record.restaurant_audit_id.restaurant_id.id

    @api.depends("restaurant_audit_id.audit_date")
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

    # Data provide methods
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
                                   restaurant_id=None,
                                   restaurant_network_id=None,
                                   check_list_category_ids=None,
                                   restaurant_ids=None,
                                   restaurant_network_ids=None):
        if check_list_category_ids is None:
            check_list_category_ids = []

        if restaurant_ids is None:
            restaurant_ids = []

        if restaurant_network_ids is None:
            restaurant_network_ids = []

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

        if len(check_list_category_ids):
            domain = expression.AND([
                [("check_list_category_id", "in", check_list_category_ids)],
                domain
            ])
        if len(restaurant_ids):
            domain = expression.AND([
                [("restaurant_id", "in", restaurant_ids)],
                domain
            ])
        if len(restaurant_network_ids):
            domain = expression.AND([
                [("restaurant_id.restaurant_network_id", "in", restaurant_network_ids)],
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
    def get_fault_counts(self, date_start, date_end,
                         check_list_category_ids=None,
                         restaurant_ids=None,
                         restaurant_network_ids=None):
        if check_list_category_ids is None:
            check_list_category_ids = []

        if restaurant_ids is None:
            restaurant_ids = []

        if restaurant_network_ids is None:
            restaurant_network_ids = []

        FaultRegistryModel = self.env["restaurant_management.fault_registry"]
        domain = [
            ('fault_date', '>=', date_start),
            ('fault_date', '<=', date_end),
            ('state', '=', 'confirm')
        ]

        if len(check_list_category_ids):
            domain = expression.AND([
                [("check_list_category_id", "in", check_list_category_ids)],
                domain
            ])
        if len(restaurant_ids):
            domain = expression.AND([
                [("restaurant_id", "in", restaurant_ids)],
                domain
            ])
        if len(restaurant_network_ids):
            domain = expression.AND([
                [("restaurant_id.restaurant_network_id", "in", restaurant_network_ids)],
                domain
            ])
        fault_count = FaultRegistryModel.search_count(domain)

        return fault_count

    @api.model
    def get_restaurant_rating_monthly_data(self, date_start, date_end,
                                           restaurant_id,
                                           check_list_category_id=None,
                                           check_list_category_ids=None):
        Restaurant = self.env["restaurant_management.restaurant"]
        if isinstance(restaurant_id, int):
            restaurant_id = Restaurant.browse(restaurant_id)
        restaurant_rating_per_month = []
        for r_date in rrule(MONTHLY, dtstart=date_start, until=date_end):
            restaurant_ratings = self.get_restaurant_rating_per_audit_data(
                r_date,
                restaurant_network_id=restaurant_id.restaurant_network_id.id,
                check_list_category_id=check_list_category_id,
                check_list_category_ids=check_list_category_ids,
            )

            restaurant_rating_per_month.extend(
                d[3] for d in restaurant_ratings if d[0] == restaurant_id.id
            )

        return restaurant_rating_per_month

    @api.model
    def get_restaurant_rating_data(self, report_date,
                                   restaurant_network_id=None,
                                   restaurant_network_ids=None,
                                   check_list_category_id=None,
                                   check_list_category_ids=None):
        """
        Returns the rating in form of:
        list([restaurant_id, restaurant_name, fault_count, rating])
        """
        if restaurant_network_ids is None:
            restaurant_network_ids = []
        if check_list_category_ids is None:
            check_list_category_ids = []

        Restaurant = self.env["restaurant_management.restaurant"]
        FaultRegistry = self.env["restaurant_management.fault_registry"]

        restaurant_domain = []
        if restaurant_network_id:
            restaurant_domain = [
                ("restaurant_network_id", "=", restaurant_network_id)
            ]

        if len(restaurant_network_ids):
            restaurant_domain = [
                ("restaurant_network_id", "in", restaurant_network_ids)
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
            if len(check_list_category_ids):
                domain = expression.AND([
                    [('check_list_category_id', 'in', check_list_category_ids)],
                    domain
                ])
            domain = expression.AND([
                [("restaurant_id", "=", restaurant_id.id)],
                domain
            ])
            restaurant_faults = FaultRegistry.search(domain)

            fault_count = sum(restaurant_faults.mapped("fault_count"))

            res.append([restaurant_id.id, restaurant_id.name, fault_count, 1])

        if len(res) > 1:
            res.sort(key=lambda r: r[2])
            res_with_rating = []
            rating = 1
            fault_count = res[0][2]
            for r in res:
                if not len(res_with_rating) or fault_count == r[2]:
                    res_with_rating.append([*r[:-1], rating])
                    continue
                rating += 1
                res_with_rating.append([*r[:-1], rating])
                fault_count = r[2]

            return res_with_rating

        return res

    @api.model
    def get_restaurant_rating_per_audit_data(
        self, 
        report_date=None,
        restaurant_network_id=None,
        restaurant_network_ids=None,
        check_list_category_id=None,
        check_list_category_ids=None,
        date_start=None,
        date_end=None,
    ):
        """
        Returns the rating in form of:
        list([restaurant_id, restaurant_name, relative_fault_count, rating])
        """
        if restaurant_network_ids is None:
            restaurant_network_ids = []
        if check_list_category_ids is None:
            check_list_category_ids = []

        Restaurant = self.env["restaurant_management.restaurant"]
        FaultRegistry = self.env["restaurant_management.fault_registry"]
        FaultAudit = self.env["restaurant_management.restaurant_audit"]
        if not date_start:
            date_start = date(year=report_date.year,
                            month=report_date.month, day=1)
        if not date_end:
            date_end = date(year=report_date.year,
                            month=report_date.month,
                            day=monthrange(report_date.year, report_date.month)[1])

        restaurant_domain = []
        if restaurant_network_id:
            restaurant_domain = [
                ("restaurant_network_id", "=", restaurant_network_id)]

        if len(restaurant_network_ids):
            restaurant_domain = [
                ("restaurant_network_id", "in", restaurant_network_ids)]
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
            if len(check_list_category_ids):
                domain = expression.AND([
                    [('check_list_category_id', 'in', check_list_category_ids)],
                    domain
                ])
            domain = expression.AND([
                [("restaurant_id", "=", restaurant_id.id)],
                domain
            ])
            restaurant_faults = FaultRegistry.search(domain)

            fault_count = sum(restaurant_faults.mapped("fault_count"))

            actual_count_of_audits = FaultAudit.get_audit_counts_per_month(
                date_start, date_end,
                restaurant_id=restaurant_id.id
            )["actual"][0]

            res.append(
                [restaurant_id.id, restaurant_id.name, round(fault_count/actual_count_of_audits, 2) if actual_count_of_audits else 0, 1])

        if len(res) > 1:
            res.sort(key=lambda r: r[2])
            res_with_rating = []
            rating = 1
            relative_fault_count = res[0][2]
            for r in res:
                if not len(res_with_rating) or relative_fault_count == r[2]:
                    res_with_rating.append([*r[:-1], rating])
                    continue
                rating += 1
                res_with_rating.append([*r[:-1], rating])
                relative_fault_count = r[2]
            return res_with_rating

        return res

    @api.model
    def get_top_faults(self, date_start, date_end,
                       check_list_category_id=None,
                       check_list_category_ids=None,
                       restaurant_id=None,
                       restaurant_ids=None,
                       restaurant_network_id=None,
                       restaurant_network_ids=None):

        if restaurant_network_ids is None:
            restaurant_network_ids = []
        if check_list_category_ids is None:
            check_list_category_ids = []
        if restaurant_ids is None:
            restaurant_ids = []

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

        if len(check_list_category_ids):
            domain = expression.AND([
                [("check_list_category_id", "in", check_list_category_ids)],
                domain
            ])
        if len(restaurant_ids):
            domain = expression.AND([
                [("restaurant_id", "in", restaurant_ids)],
                domain
            ])
        if len(restaurant_network_ids):
            domain = expression.AND([
                [("restaurant_id.restaurant_network_id", "in", restaurant_network_ids)],
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

    def get_director_comments_of_faults(self, date_start, date_end, check_list_id,
                                        restaurant_id=None,
                                        restaurant_ids=None,
                                        restaurant_network_ids=None):

        if restaurant_ids is None:
            restaurant_ids = []

        if restaurant_network_ids is None:
            restaurant_network_ids = []

        FaultRegistryModel = self.env["restaurant_management.fault_registry"]
        domain = [
            ("check_list_id", "=", check_list_id),
            ("fault_date", ">=", date_start),
            ("fault_date", "<=", date_end),
            ('state', '=', 'confirm')
        ]
        if len(restaurant_network_ids):
            domain = expression.AND([
                [("restaurant_id.restaurant_network_id", "in", restaurant_network_ids)],
                domain
            ])

        if len(restaurant_ids):
            domain = expression.AND([
                [("restaurant_id", "in", restaurant_ids)],
                domain
            ])

        if restaurant_id:
            domain = expression.AND([
                [("restaurant_id", "=", restaurant_id)],
                domain
            ])

        comments = FaultRegistryModel.search(domain).mapped("director_comment")

        return "<hr/>".join([c for c in comments if c])

    def get_category_responsible_comments_of_faults(self, date_start, date_end, check_list_id,
                                                    restaurant_network_ids=None):
        if restaurant_network_ids is None:
            restaurant_network_ids = []

        FaultRegistryModel = self.env["restaurant_management.fault_registry"]

        domain = [
            ("check_list_id", "=", check_list_id),
            ("fault_date", ">=", date_start),
            ("fault_date", "<=", date_end),
            ('state', '=', 'confirm')
        ]
        if len(restaurant_network_ids):
            domain = expression.AND([
                [("restaurant_id.restaurant_network_id", "in", restaurant_network_ids)],
                domain
            ])

        comments = FaultRegistryModel.search(domain).mapped(
            "check_list_category_responsible_comment")

        return "<hr/>".join([c for c in comments if c])

    def get_comments_of_faults(self, date_start, date_end, check_list_id,
                               restaurant_network_ids=None):
        if restaurant_network_ids is None:
            restaurant_network_ids = []

        FaultRegistryModel = self.env["restaurant_management.fault_registry"]
        domain = [
            ("check_list_id", "=", check_list_id),
            ("fault_date", ">=", date_start),
            ("fault_date", "<=", date_end),
            ('state', '=', 'confirm')
        ]
        if len(restaurant_network_ids):
            domain = expression.AND([
                [("restaurant_id.restaurant_network_id", "in", restaurant_network_ids)],
                domain
            ])
        comments = FaultRegistryModel.search(domain).mapped("comment")

        return "<hr/>".join([c for c in comments if c])

    # Crons
    @api.model
    def clear_old_attachments(self):
        old_faults = self.env['restaurant_management.fault_registry'].search([
            ("fault_date", "<", datetime.now()-timedelta(weeks=20))
        ])
        attachment_ids = old_faults.mapped("attachment_ids")
        _logger.info("Number of attachments deleted: %s", len(attachment_ids))
        attachment_ids.unlink()
