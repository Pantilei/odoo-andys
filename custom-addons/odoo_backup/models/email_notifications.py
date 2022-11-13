from odoo import models, fields, api, tools, _


class EmailNotif(models.AbstractModel):
    _name = 'odoo_backup.upload_email_notif'
    _description = "Send email upload notif"

    def send_upload_email(self, template_xml_id, context, subject):
        body = self.env['mail.render.mixin']._render_template(
            template_xml_id,
            'odoo_backup.backup',
            self.ids,
            engine='qweb_view',
            add_context=context
        )[self.id]

        email_to = ""
        for record in self.notify_user_ids.mapped('login'):
            email_to += record + ','

        mail_values = {
            'auto_delete': True,
            'author_id': self.env.user.partner_id.id,
            'email_from': (
                    self.env['res.users'].browse(self.env.uid).company_id.email
                    or self.env.user.email_formatted
                    or self.env.ref('base.user_root').email_formatted
            ),
            'email_to': email_to,
            'body_html': body,
            'state': 'outgoing',
            'subject': subject,
        }
        send_mail = self.env['mail.mail'].sudo().create(mail_values)
        send_mail.send(True)
