from email.policy import default
from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta
from calendar import monthrange

import random


class AuditDistributions(models.Model):
    _name = "restaurant_management.audit_distribution"
    _description = "Audit Distribution"

    restaurant_id = fields.Many2one(
        comodel_name="restaurant_management.restaurant",
        string="Restaurant",
        required=1
    )

    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Expert QCD",
        required=1
    )

    audit_date = fields.Date(
        default=lambda self: date.today(),
        string="Audit Date",
        required=1
    )

    @api.model
    def create_distributions(self):
        PlannedAudits = self.env["restaurant_management.planned_audits"]
        Restaurant = self.env["restaurant_management.restaurant"]
        user_ids = self.env.ref(
            "restaurant_management.group_restaurant_management_auditer").users
        if not user_ids:
            return
        count_per_user = [
            [user_id.id, 0] for user_id in user_ids
        ]

        date_next_month = date.today() + relativedelta(months=+1)
        max_days_next_month = monthrange(
            year=date_next_month.year,
            month=date_next_month.month
        )[1]

        date_start = date(
            year=date_next_month.year,
            month=date_next_month.month,
            day=1
        )
        date_end = date(
            year=date_next_month.year,
            month=date_next_month.month,
            day=max_days_next_month
        )

        for restaurant_id in Restaurant.search([]):
            planned_audit_count = PlannedAudits.get_number_of_audits(
                date_start, date_end,
                restaurant_id=restaurant_id.id
            )[0]
            days_range = int(max_days_next_month/planned_audit_count)
            for i in range(planned_audit_count):
                count_per_user.sort(key=lambda r: r[1])
                self.create({
                    "restaurant_id": restaurant_id.id,
                    "user_id": count_per_user[0][0],
                    "audit_date": date(
                        year=date_next_month.year,
                        month=date_next_month.month,
                        day=(i+1)*random.randint(days_range-2, days_range)
                    )
                })

                count_per_user[0][1] = count_per_user[0][1] + 1
