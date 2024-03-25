# -*- coding: utf-8 -*-

import json
import logging
import requests

from datetime import datetime, timedelta, timezone

from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)

TIMEOUT = 20

GOOGLE_AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_ENDPOINT = 'https://accounts.google.com/o/oauth2/token'
GOOGLE_API_BASE_URL = 'https://www.googleapis.com'


class GoogleAuth(http.Controller):

    @http.route('/odoo-google-drive-backup/authentication', type='http', auth="public")
    def oauth2callback(self, **kw):
        """ This route/function is called by Google when user Accept/Refuse the consent of Google """
        authorization_code = kw.get('code', None)
        base_url = request.env['ir.config_parameter'].sudo().get_param("web.base.url")
        url_return = f"{base_url}/web"
        if authorization_code:
            state = json.loads(kw.get('state'))
            backup_id = request.env["odoo_backup.backup"].sudo().browse(state.get("backup_id"))
            scope = kw.get('scope', None)
            url_return = f"{base_url}/web#id={backup_id.id}&cids=1&menu_id=4&action=792&model=odoo_backup.backup&view_type=form"
            redirect_uri = backup_id.google_redirect_uri
            client_id = backup_id.google_client_id
            client_secret = backup_id.google_client_secret
            access_token, refresh_token, ttl = self._get_google_tokens(
                authorization_code,
                client_id,
                client_secret,
                redirect_uri
            )
            backup_id.write({
                "google_authorization_code": authorization_code,
                "google_refresh_token": refresh_token,
                "google_access_token": access_token,
                "google_access_token_expire_datetime": datetime.now() + timedelta(seconds=ttl),
            })
            return request.redirect(url_return)
        elif kw.get('error'):
            return request.redirect("%s%s%s" % (url_return, "?error=", kw['error']))
        else:
            return request.redirect("%s%s" % (url_return, "?error=Unknown_error"))

    def _get_google_tokens(self, authorize_code, client_id, client_secret, redirect_uri):
        """ Call Google API to exchange authorization code against token, with POST request, to
            not be redirected.
        """
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            'code': authorize_code,
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        try:
            dummy, response, dummy = self._do_request(GOOGLE_TOKEN_ENDPOINT, params=data, headers=headers,
                                                      method='POST', preuri='')
            access_token = response.get('access_token')
            refresh_token = response.get('refresh_token')
            ttl = response.get('expires_in')
            return access_token, refresh_token, ttl
        except requests.HTTPError:
            error_msg = _("Something went wrong during your token generation. Maybe your Authorization Code is invalid")
            raise request.env['res.config.settings'].get_config_warning(error_msg)

    def _do_request(self, uri, params=None, headers=None, method='POST', preuri="https://www.googleapis.com",
                    timeout=TIMEOUT):
        """ Execute the request to Google API. Return a tuple ('HTTP_CODE', 'HTTP_RESPONSE')
            :param uri : the url to contact
            :param params : dict or already encoded parameters for the request to make
            :param headers : headers of request
            :param method : the method to use to make the request
            :param preuri : pre url to prepend to param uri.
        """
        if params is None:
            params = {}
        if headers is None:
            headers = {}

        _logger.debug("Uri: %s - Type : %s - Headers: %s - Params : %s !", uri, method, headers, params)

        ask_time = datetime.now()
        try:
            if method.upper() in ('GET', 'DELETE'):
                res = requests.request(method.lower(), preuri + uri, params=params, timeout=timeout)
            elif method.upper() in ('POST', 'PATCH', 'PUT'):
                res = requests.request(method.lower(), preuri + uri, data=params, headers=headers, timeout=timeout)
            else:
                raise Exception(_('Method not supported [%s] not in [GET, POST, PUT, PATCH or DELETE]!') % (method))
            res.raise_for_status()
            status = res.status_code

            if int(status) == 204:  # Page not found, no response
                response = False
            else:
                response = res.json()

            try:
                ask_time = datetime.strptime(res.headers.get('date', ''), "%a, %d %b %Y %H:%M:%S %Z")
            except ValueError:
                pass
        except requests.HTTPError as error:
            if error.response.status_code in (204, 404):
                status = error.response.status_code
                response = ""
            else:
                _logger.exception("Bad google request : %s !", error.response.content)
                raise error
        return (status, response, ask_time)
