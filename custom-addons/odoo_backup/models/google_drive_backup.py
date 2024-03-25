import logging
import requests
import json
import traceback

from datetime import datetime, timedelta
from werkzeug import urls

from odoo import models, api, fields, _
from odoo.exceptions import UserError

TIMEOUT = 20

GOOGLE_AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_ENDPOINT = 'https://accounts.google.com/o/oauth2/token'
GOOGLE_API_BASE_URL = 'https://www.googleapis.com'
GOOGLE_SCOPES = 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/drive.file'

_logger = logging.getLogger(__name__)


class GoogleDriveBackUp(models.AbstractModel):
    _name = "odoo_backup.google_drive_backup"
    _inherit = ["odoo_backup.upload_email_notif"]
    _description = "Google Drive BackUp"

    def _get_redirect_uri(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param("web.base.url")
        return f"{base_url}/odoo-google-drive-backup/authentication"

    @api.depends('google_client_id')
    def _compute_drive_uri(self):
        for rec in self:
            if rec.id and rec.google_client_id:
                encoded_params = urls.url_encode({
                    'scope': GOOGLE_SCOPES,
                    'redirect_uri': self._get_redirect_uri(),
                    'client_id': rec.google_client_id,
                    'response_type': 'code',
                    'access_type': 'offline',
                    'prompt': 'consent',
                    'state': json.dumps({
                        "backup_id": rec.id
                    })
                })
                google_uri = f'{GOOGLE_AUTH_ENDPOINT}?{encoded_params}'
                rec.google_uri = google_uri
            else:
                rec.google_uri = False

    @api.depends("google_authorization_code", "google_refresh_token", "google_access_token")
    def _hide_google_secret_data(self):
        for rec in self:
            rec.google_authorization_code_hidden = "********" if rec.google_authorization_code else False
            rec.google_refresh_token_hidden = "********" if rec.google_refresh_token else False
            rec.google_access_token_hidden = "********" if rec.google_access_token else False

    # Columns for Google Drive
    is_google_drive_upload = fields.Boolean(
        string='Upload to Google Drive',
        help="If you check this option you can specify the details needed to upload to google drive."
    )
    drive_folder_id = fields.Char(
        string='Folder ID',
        help="make a folder on drive in which you want to upload files; then open that folder; "
             "the last thing in present url will be folder id"
    )
    drive_autoremove = fields.Boolean(
        string='Auto. Remove Uploaded Backups',
        help='If you check this option you can choose to automatically remove the backup after xx days'
    )

    drive_to_remove = fields.Integer(
        string='Remove drive backups after x days',
        help="Choose after how many days the backup should be deleted. For example:\n"
             "If you fill in 5 the backups will be removed after 5 days.",
    )
    google_authorization_code = fields.Char(
        string='Authorization Code'
    )
    google_authorization_code_hidden = fields.Char(
        string='Authorization Code Hidden',
        compute='_hide_google_secret_data'
    )
    google_refresh_token = fields.Char(
        string='Refresh Token'
    )
    google_refresh_token_hidden = fields.Char(
        string='Refresh Token Hidden',
        compute='_hide_google_secret_data'
    )
    google_access_token = fields.Char(
        string='Access Token'
    )
    google_access_token_hidden = fields.Char(
        string="Access Token Hidden",
        compute='_hide_google_secret_data'
    )
    google_access_token_expire_datetime = fields.Datetime(
        string='Access Token Expiration Time'
    )
    google_uri = fields.Char(
        compute='_compute_drive_uri',
        string='URI',
        help="The URL to generate the authorization code from Google"
    )

    google_client_id = fields.Char(
        string="Google Client Id"
    )
    google_client_secret = fields.Char(
        string="Google Client Secret"
    )
    google_redirect_uri = fields.Char(
        string="Google Redirect URI",
        default=_get_redirect_uri
    )

    # GOOGLE DRIVE
    def _get_access_token(self):
        if not self.google_refresh_token:
            raise UserError(_("No Refresh Token!"))
        if (datetime.now() - timedelta(minutes=10)) < self.google_access_token_expire_datetime:
            return self.google_access_token
        else:
            data = {
                'client_id': self.google_client_id,
                'client_secret': self.google_client_secret,
                'refresh_token': self.google_refresh_token,
                'grant_type': "refresh_token",
                'scope': GOOGLE_SCOPES
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            try:
                req = requests.post(GOOGLE_TOKEN_ENDPOINT, data=data, headers=headers, timeout=TIMEOUT)
                req.raise_for_status()
            except requests.HTTPError as he:
                _logger.error(traceback.format_exc())
                raise UserError(_("Could not get access token from google!"))

            return req.json().get("access_token")

    def google_drive_upload(self, file_path, bkp_file):
        access_token = self._get_access_token()

        headers = {"Authorization": f"Bearer {access_token}"}
        para = {
            "name": str(bkp_file),
            "parents": [str(self.drive_folder_id)]
        }
        with open(file_path, "rb") as f:
            files = {
                'data': ('metadata', json.dumps(para), 'application/json; charset=UTF-8'),
                'file': f
            }
            req = requests.post(
                "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                headers=headers,
                files=files
            )

        # SENDING EMAIL NOTIFICATION
        if req.status_code == 200:
            email_context = {
                "bkp_file": bkp_file,
                "drive_folder_id": self.drive_folder_id
            }
            self._send_success_google_upload_email(email_context)
        else:
            response = req.json()
            code = response['error']['code']
            message = response['error']['errors'][0]['message']
            reason = response['error']['errors'][0]['reason']
            email_context = {
                "bkp_file": bkp_file,
                "code": code,
                "message": message,
                "reason": reason
            }
            self._send_failed_google_upload_email(email_context)

        # AUTO REMOVE UPLOADED FILE
        if self.drive_autoremove:
            headers = {
                'Content-type': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'Accept': 'text/plain'
            }
            params = {
                'q': f"mimeType='application/{self.backup_type}' and '{self.drive_folder_id}' in parents",
                'fields': "nextPageToken,files(id, name, createdTime, modifiedTime, mimeType)"
            }
            url = f"{GOOGLE_API_BASE_URL}/drive/v3/files"
            try:
                res = requests.get(url, params=params, headers=headers)
                res.raise_for_status()
            except requests.HTTPError as he:
                _logger.error(traceback.format_exc())
                raise UserError(_("HTTP error occurred when getting google drive folder content"))
            content = res.json()
            for item in content['files']:
                date_today = datetime.today().date()
                create_date = datetime.strptime(str(item['createdTime'])[0:10], '%Y-%m-%d').date()

                delta = date_today - create_date
                if delta.days >= self.drive_to_remove:
                    params = {
                        'access_token': access_token
                    }
                    url = f"{GOOGLE_API_BASE_URL}/drive/v3/files/{item['id']}"
                    try:
                        res = requests.delete(url, params=params, headers=headers)
                        res.raise_for_status()
                    except requests.HTTPError as he:
                        _logger.error(traceback.format_exc())
                        raise UserError(_("HTTP error occurred when trying to delete old backups!"))

    def _send_success_google_upload_email(self, context):
        self.send_upload_email(
            'odoo_backup.successful_google_drive_upload_email',
            context,
            "Google Drive Upload Successful"
        )

    def _send_failed_google_upload_email(self, context):
        self.send_upload_email(
            'odoo_backup.failed_google_drive_upload_email',
            context,
            "Google Drive Upload Failed"
        )
