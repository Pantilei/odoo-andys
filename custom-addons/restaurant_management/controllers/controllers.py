# -*- coding: utf-8 -*-

import base64
import io
import json
import logging
from datetime import datetime, timedelta, timezone

import werkzeug

from odoo import _, http
from odoo.http import Response, request

_logger = logging.getLogger(__name__)


class SecretGuest(http.Controller):

    @http.route('/audits/<string:access_token>', type='http', auth="public")
    def secret_guest_audits(self, access_token, **kw):
        """ Secret Guest Audits """
        audit_temp_link_id = request.env["restaurant_management.audit_temp_links"].sudo().search([
            ("access_token", "=", access_token)
        ], limit=1)
        if not audit_temp_link_id or not audit_temp_link_id.is_active:
            return werkzeug.exceptions.Unauthorized()

        check_list_type_id = request.env.ref("restaurant_management.secret_guest_check_list_type")
        check_list_category_ids = request.env["restaurant_management.check_list_category"].sudo().search([
            ("check_list_type_id", "=", check_list_type_id.id)
        ])
        check_list_data = [{
            "id": category_id.id,
            "name": category_id.name,
            "response_type": category_id.response_type,
            "check_lists": [{
                "id": check_list_id.id,
                "description": check_list_id.description,
                "photo_required": check_list_id.photo_required,
                "comment_required": check_list_id.comment_required,
            } for check_list_id in category_id.check_list_ids]
        } for category_id in check_list_category_ids]
        return request.render("restaurant_management.secret_guest_audit_main_page", {
            "title": _("Check List of Secret Guest"),
            "restaurant": {
                "id": audit_temp_link_id.restaurant_id.id,
                "display_name": audit_temp_link_id.restaurant_id.display_name
            },
            "loading_level": [
                {
                    "id": "low",
                    "value": _("Low level: up to 40%")
                },
                {
                    "id": "medium",
                    "value": _("Medium level: 30%-80%")
                },
                {
                    "id": "high",
                    "value": _("High level: from 80%")
                }
            ],
            "check_list_data": check_list_data
        })
    
    @http.route('/audits/<string:access_token>/file-upload', type='http', auth="public", methods=["POST"], csrf=False)
    def secret_guest_audits_file_upload(self, access_token, **kw):
        """ Secret Guest Audits File Upload"""
        audit_temp_link_id = request.env["restaurant_management.audit_temp_links"].sudo().search([
            ("access_token", "=", access_token)
        ], limit=1)
        if not audit_temp_link_id or not audit_temp_link_id.is_active:
            return werkzeug.exceptions.Unauthorized()

        files = list(kw.values())
        if not files:
            return Response(status=404)
        file = files[0]
        in_memory_file = io.BytesIO()
        file.save(in_memory_file)
        attachment_id = request.env["ir.attachment"].sudo().create({
            'name': file.filename,
            'datas': base64.encodebytes(in_memory_file.getvalue()),
            'type': 'binary',
            'description': file.filename,
            'mimetype': file.mimetype
        })
        return Response(str(attachment_id.id), status=200)
    
    @http.route('/audits/<string:access_token>/file-remove', type='http', auth="public", methods=["DELETE"], csrf=False)
    def secret_guest_audits_file_remove(self, access_token, **kw):
        """ Secret Guest Audits File Remove"""
        audit_temp_link_id = request.env["restaurant_management.audit_temp_links"].sudo().search([
            ("access_token", "=", access_token)
        ], limit=1)
        if not audit_temp_link_id or not audit_temp_link_id.is_active:
            return werkzeug.exceptions.Unauthorized()

        attachment_id = request.env["ir.attachment"].sudo().search([("id", "=", int(request.httprequest.data))])
        attachment_id.sudo().unlink()

        return Response(status=204)

    @http.route('/audits/<string:access_token>/handle', type='json', auth="public")
    def secret_guests_audit_handle(self, access_token, **kw):
        """ Audit Handle"""
        audit_temp_link_id = request.env["restaurant_management.audit_temp_links"].sudo().search([
            ("access_token", "=", access_token)
        ], limit=1)
        if not audit_temp_link_id or not audit_temp_link_id.is_active:
            return {
                "success": False,
                "message": "Unauthorized!"
            }
        print(f"{kw=}")
       
        # request.env['restaurant_management.restaurant_audit'].sudo().create({
            
        # })
        return {
            "success": True,
            "message": "Successefully store!"
        }

    def _get_bg_image_base_url(self):
        return request.env["ir.config_parameter"].sudo().get_param("reviews.bg_image.url")
    
    @http.route('/audits/<string:access_token>/thank-you', type='http', auth="public")
    def secret_guest_audits_thank_you(self, access_token, **kw):
        """ Secret Guest Audits """
        audit_temp_link_id = request.env["restaurant_management.audit_temp_links"].sudo().search([
            ("access_token", "=", access_token)
        ], limit=1)
        if not audit_temp_link_id or not audit_temp_link_id.is_active:
            return werkzeug.exceptions.Unauthorized()
        return request.render("restaurant_management.secret_guest_audit_thank_you_page", {
            "title": _("Thank you !"),
            "message": _("Your audit data is sent!"),
        })
