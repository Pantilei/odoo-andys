import os
import time
import shutil
import json
import tempfile
import logging
import traceback

from datetime import datetime

from odoo import models, fields, api, tools, _
from odoo.exceptions import AccessDenied, UserError
import odoo


_logger = logging.getLogger(__name__)


class DbBackup(models.Model):
    _name = 'odoo_backup.backup'
    _inherit = ["odoo_backup.sftp_backup", "odoo_backup.google_drive_backup"]
    _description = 'Backup configuration record'

    def _get_db_name(self):
        dbName = self._cr.dbname
        return dbName

    # Columns for local server configuration
    host = fields.Char(
        string='Host',
        required=True,
        default='localhost'
    )
    port = fields.Char(
        string='Port',
        required=True,
        default=8069
    )
    name = fields.Char(
        string='Database',
        required=True,
        help='Database you want to schedule backups for',
        default=_get_db_name
    )
    folder = fields.Char(
        string='Backup Directory',
        help='Absolute path for storing the backups',
        required='True',
        default='/odoo/backups'
    )
    backup_type = fields.Selection(
        selection=[('zip', 'Zip'), ('dump', 'Dump')],
        string='Backup Type',
        required=True,
        default='zip'
    )
    cron_id = fields.Many2one(
        comodel_name="ir.cron",
        string="Cron",
        readonly=True,
        default=lambda self: self.env.ref("odoo_backup.backup_scheduler")
    )
    notify_user_ids = fields.Many2many(
        comodel_name='res.users',
        string="Person to Notify"
    )
    autoremove = fields.Boolean(
        string='Auto Remove Backups',
        help='If you check this option you can choose to automatically remove the backups older than xx days'
    )
    days_to_keep = fields.Integer(
        'Remove local backups after x days',
        help="Choose after how many days the backup should be deleted. For example:\n"
             "If you fill in 5 the backups will be removed after 5 days.",
        required=True
    )

    @api.model
    def schedule_backup(self):
        """
        Cron job method to perform all backups
        """
        conf_ids = self.search([])
        for rec in conf_ids:
            rec.perform_backup()

    def perform_backup(self):
        """
        Button action to perform backup for a single instance
        """
        if not self.env.user.has_group("odoo_backup.group_manager"):
            _logger.error('Unauthorized database operation. Backups should only be available for backup managers.')
            raise AccessDenied()
        self._create_folder()
        # Create name for dumpfile.
        bkp_file = f'{time.strftime("%Y_%m_%d_%H_%M_%S")}_{self.name}.{self.backup_type}'
        file_path = os.path.join(self.folder, bkp_file)
        # Backup database and write it away
        self._take_dump(self.name, file_path, self.backup_type)
        # Remove all old files (on local server) in case this is configured..
        if self.autoremove:
            self._remove_old_backups()

        # Check if user wants to write to SFTP or not.
        if self.sftp_write:
            self.sftp_upload()

        # Upload to Google drive
        if self.is_google_drive_upload:
            self.google_drive_upload(file_path, bkp_file)

    def _create_folder(self):
        try:
            if not os.path.isdir(self.folder):
                os.makedirs(self.folder)
        except Exception as ex:
            _logger.error(traceback.format_exc())
            raise UserError(_("Cannot created directory tree!"))

    def _take_dump(self, db_name, file_path, backup_format='zip'):
        """
        Dump database `db` into file-like object `stream` if stream is None
        return a file object with the dump.
        """
        with open(file_path, 'wb') as stream:
            _logger.info(f'DUMP DB: {db_name} format {backup_format}')
            cmd = ['pg_dump', '--no-owner']
            cmd.append(db_name)
            if backup_format == 'zip':
                with tempfile.TemporaryDirectory() as dump_dir:
                    filestore = odoo.tools.config.filestore(db_name)
                    # Recursively copy an entire directory tree rooted at filestore
                    # to a directory os.path.join(dump_dir, 'filestore')
                    if os.path.exists(filestore):
                        shutil.copytree(filestore, os.path.join(dump_dir, 'filestore'))
                    # Create in dump_dir manifest.json file
                    with open(os.path.join(dump_dir, 'manifest.json'), 'w') as fh:
                        db = odoo.sql_db.db_connect(db_name)
                        with db.cursor() as cr:
                            json.dump(self._dump_db_manifest(cr), fh, indent=4)
                    cmd.insert(-1, '--file=' + os.path.join(dump_dir, 'dump.sql'))
                    # Execute pg command
                    odoo.tools.exec_pg_command(*cmd)
                    # Zip temporary directory 'dump_dir'
                    odoo.tools.osutil.zip_dir(
                        dump_dir,
                        stream,
                        include_dir=False,
                        fnct_sort=lambda file_name: file_name != 'dump.sql'
                    )
            else:
                cmd.insert(-1, '--format=c')
                stdin, stdout = odoo.tools.exec_pg_command_pipe(*cmd)
                # Copy the contents of the file-like object 'stdout' to the file-like object 'stream'.
                shutil.copyfileobj(stdout, stream)

    def _remove_old_backups(self):
        directory = self.folder
        # Loop over all files in the directory.
        for f in os.listdir(directory):
            fullpath = os.path.join(directory, f)
            # Only delete the ones which are from the current database
            # (Makes it possible to save different databases in the same folder)
            if self.name in fullpath:
                timestamp = os.stat(fullpath).st_ctime
                createtime = datetime.fromtimestamp(timestamp)
                now = datetime.now()
                delta = now - createtime
                if delta.days >= self.days_to_keep:
                    # Only delete files (which are .dump and .zip), no directories.
                    if os.path.isfile(fullpath) and (".dump" in f or '.zip' in f):
                        _logger.info(f"Delete local out-of-date file: {fullpath}")
                        os.remove(fullpath)

    def _dump_db_manifest(self, cr):
        pg_version = f"%d.%d" % divmod(cr._obj.connection.server_version / 100, 100)
        cr.execute("SELECT name, latest_version FROM ir_module_module WHERE state = 'installed'")
        modules = dict(cr.fetchall())
        manifest = {
            'odoo_dump': '1',
            'db_name': cr.dbname,
            'version': odoo.release.version,
            'version_info': odoo.release.version_info,
            'major_version': odoo.release.major_version,
            'pg_version': pg_version,
            'modules': modules,
        }
        return manifest
