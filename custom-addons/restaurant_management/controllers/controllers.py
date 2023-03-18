# -*- coding: utf-8 -*-

import base64
import json
import logging
from datetime import datetime, timedelta, timezone

import werkzeug

from odoo import _, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SecretGuest(http.Controller):

    @http.route('/audits/<string:access_token>', type='http', auth="public")
    def secret_guest_audits(self, access_token, **kw):
        """ Secret Guest Audits """
        audit_temp_link_id = request.env["restaurant_management.audit_temp_links"].sudo().search([
            ("access_token", "=", access_token)
        ], limit=1)
        if not audit_temp_link_id or not audit_temp_link_id.is_active:
            return werkzeug.exceptions.NotFound()

        return request.render("restaurant_management.secret_guest_audit_main_page", {
            "title": "TITLE"
        })

    @http.route('/audits/<string:access_token>/handle', type='json', auth="public")
    def secret_guests_audit_handle(self, access_token, **kw):
        """ Reviews Handle"""
        if not kw.get("name", None) or not kw.get("description", None):
            return {
                "success": False,
                "message": "Name and review must be present!"
            }
        department_id = request.env["hr.department"].sudo().search([
            ("uid", "=", access_token)
        ], limit=1)
        if not department_id:
            return {
                "success": False,
                "message": "Department not found!"
            }
        request.env['reviews'].sudo().create({
            "name": kw.get("name"),
            "phone": kw.get("phone", False),
            "email": kw.get("email_from", False),
            "responsible_name": kw.get("name_of_responsible", False),
            "description": kw.get("description"),
            "department_id": department_id.id
        })
        return {
            "success": True,
            "message": ""
        }

    @http.route('/audits/bg-img/<int:form_id>', type='http', auth="public")
    def reviews_bg_image(self, form_id, **kw):
        form_id = request.env["reviews.collection"].sudo().search([
            ("id", "=", form_id)
        ], limit=1)
        if not form_id:
            return werkzeug.exceptions.NotFound()
        return request.env['ir.http'].sudo()._content_image(model='reviews.collection', res_id=form_id, field='bg_img')

    def _get_bg_image_base_url(self):
        return request.env["ir.config_parameter"].sudo().get_param("reviews.bg_image.url")
