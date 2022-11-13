import logging
import os

from datetime import datetime
from contextlib import contextmanager

from odoo import models, api, fields, _, tools, _
from odoo.exceptions import AccessDenied, UserError


_logger = logging.getLogger(__name__)


try:
    import paramiko
except ImportError:
    raise ImportError(
        'This module needs paramiko to automatically write backups to the FTP through SFTP. '
        'Please install paramiko on your system. (sudo pip3 install paramiko)'
    )


class SFTPBackUp(models.AbstractModel):
    _name = "odoo_backup.sftp_backup"
    _inherit = ["odoo_backup.upload_email_notif"]
    _description = "SFTP BackUp"

    sftp_write = fields.Boolean(
        string='Write to external server with SFTP',
        help="If you check this option you can specify the details needed to write to a remote "
             "server with SFTP."
    )
    sftp_path = fields.Char(
        string='Path external server',
        help='The location to the folder where the dumps should be written to. For example '
             '/odoo/backups/.\nFiles will then be written to /odoo/backups/ on your remote server.'
    )
    sftp_host = fields.Char(
        string='IP Address SFTP Server',
        help='The IP address from your remote server. For example 192.168.0.1'
    )
    sftp_port = fields.Integer(
        string='SFTP Port',
        help='The port on the FTP server that accepts SSH/SFTP calls.',
        default=22
    )
    sftp_user = fields.Char(
        string='Username SFTP Server',
        help='The username where the SFTP connection should be made with. This is the user on the '
             'external server.'
    )
    sftp_password = fields.Char(
        string='Password User SFTP Server',
        help='The password from the user where the SFTP connection should be made with. This '
             'is the password from the user on the external server.'
    )
    days_to_keep_sftp = fields.Integer(
        string='Remove SFTP after x days',
        help='Choose after how many days the backup should be deleted from the FTP '
             'server. For example:\nIf you fill in 5 the backups will be removed after '
             '5 days from the FTP server.',
        default=30
    )
    send_mail_sftp_fail = fields.Boolean(
        string='Auto. E-mail on backup fail',
        help='If you check this option you can choose to automaticly get e-mailed '
             'when the backup to the external server failed.'
    )

    def test_sftp_connection(self):
        """
        Test the SFTP Connection
        """
        # Check if there is a success or fail and write messages
        message_title = ""
        message_content = ""
        error = ""
        has_failed = False

        ip_host = self.sftp_host
        port_host = self.sftp_port
        username_login = self.sftp_user
        password_login = self.sftp_password

        # Connect with external server over SFTP, so we know sure that everything works.
        s = paramiko.SSHClient()
        try:
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            s.connect(ip_host, port_host, username_login, password_login, timeout=10)
            sftp = s.open_sftp()
            sftp.close()
            message_title = _("Connection Test Succeeded!\nEverything seems properly set up for FTP back-ups!")
        except Exception as e:
            _logger.critical('There was a problem connecting to the remote ftp: %s', str(e))
            error += str(e)
            has_failed = True
            message_title = _("Connection Test Failed!")
            if len(self.sftp_host) < 8:
                message_content += "\nYour IP address seems to be too short.\n"
            message_content += _("Here is what we got instead:\n")
        finally:
            if s:
                s.close()

        if has_failed:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'sticky': True,
                    'message': _(f"{message_title}\n\n {message_content} '{error}'")
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'sticky': True,
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'sticky': True,
                    'message': _(f"{message_title}\n\n{message_content}")
                }
            }

    @contextmanager
    def _get_sftp_session(self):
        client = None
        sftp_session = None
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.sftp_host, self.sftp_port, self.sftp_user, self.sftp_password, timeout=20)
            sftp_session = client.open_sftp()
            yield sftp_session
        except Exception as error:
            _logger.critical(f'Error connecting to remote server! Error: {str(error)}')
            raise UserError(f'Error connecting to remote server! Error: {str(error)}')
        finally:
            if client:
                client.close()
            if sftp_session:
                sftp_session.close()

    def _create_missing_dirs_in_remote_server(self, sftp):
        current_directory = ''
        for dirElement in self.sftp_path.split('/'):
            current_directory += dirElement + '/'
            try:
                sftp.chdir(current_directory)
            except Exception as ex:
                _logger.info('(Part of the) path didn\'t exist. Creating it now at %s',
                             current_directory)
                # Make directory and then navigate into it
                sftp.mkdir(current_directory, 777)
                sftp.chdir(current_directory)
                pass

    def _check_expired_files_in_remote_server(self, sftp):
        # Navigate in to the correct folder.
        sftp.chdir(self.sftp_path)
        _logger.debug("Checking expired files")
        # Loop over all files in the directory from the back-ups.
        # We will check the creation date of every back-up.
        for file in sftp.listdir(self.sftp_path):
            if self.name in file:
                # Get the full path
                fullpath = os.path.join(self.sftp_path, file)
                # Get the timestamp from the file on the external server
                timestamp = sftp.stat(fullpath).st_mtime
                createtime = datetime.fromtimestamp(timestamp)
                now = datetime.now()
                delta = now - createtime
                # If the file is older than the days_to_keep_sftp (the days to keep that the user filled in
                # on the Odoo form it will be removed.
                if delta.days >= self.days_to_keep_sftp:
                    # Only delete files, no directories!
                    if ".dump" in file or '.zip' in file:
                        _logger.info(f"Delete too old file from SFTP servers: {file}")
                        sftp.unlink(file)

    def _upload_missing_files_to_remote_server(self, sftp):
        sftp.chdir(self.sftp_path)
        # Loop over all files in the directory.
        for f in os.listdir(self.folder):
            if self.name in f:
                fullpath = os.path.join(self.folder, f)
                if os.path.isfile(fullpath):
                    try:
                        sftp.stat(os.path.join(self.sftp_path, f))
                        _logger.debug(
                            f'File {fullpath} already exists on the remote FTP Server ------ skipped'
                        )
                    # This means the file does not exist (remote) yet!
                    except IOError:
                        try:
                            sftp.put(fullpath, os.path.join(self.sftp_path, f))
                            _logger.info('Copying File % s------ success', fullpath)
                        except Exception as err:
                            _logger.critical(
                                f'We cannot write the file to the remote server. Error: {str(err)}'
                            )

    def sftp_upload(self):
        with self._get_sftp_session() as sftp:
            try:
                try:
                    sftp.chdir(self.sftp_path)
                except IOError:
                    # Create directory and subdirs if they do not exist.
                    self._create_missing_dirs_in_remote_server(sftp)
                self._upload_missing_files_to_remote_server(sftp)
                self._check_expired_files_in_remote_server(sftp)

            except Exception as e:
                _logger.error(
                    'Exception! We cannot back up to the FTP server. Here is what we got back instead: {str(e)}'
                )
                # At this point the SFTP backup failed. We will now check if the user wants
                # an e-mail notification about this.
                if self.send_mail_sftp_fail:
                    try:
                        email_context = {
                            "host": self.host,
                            "sftp_host": self.sftp_host,
                            "sftp_user": self.sftp_user,
                            "errors": tools.ustr(e)
                        }
                        self.send_upload_email(
                            'odoo_backup.failed_sftp_upload_email',
                            email_context,
                            "SFTP Upload Failed"
                        )
                    except Exception as ex:
                        _logger.error(_("Cannot send the sftp failed email!"))
