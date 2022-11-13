# -*- coding: utf-8 -*-
{
    'name': 'Odoo Backup',
    'version': '15.0',
    'category': 'Technical',
    'sequence': 100,
    'summary': 'Use this module as a template for other modules of Odoo 15th version.',
    'description': "Use this module as a template for other modules of Odoo 15th version.",
    'website': '',
    'depends': [
        'base',
    ],
    'data': [
        'security/odoo_backup_security.xml',
        'security/ir.model.access.csv',

        'data/data.xml',

        'views/odoo_backup_view.xml',

        'views/menu_items.xml',

        'views/templates/mail_templates.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [],
        'web.report_assets_common': [],
        'web.assets_frontend': [],
        'web.assets_tests': [],
        'web.qunit_suite_tests': [],
        'web.assets_qweb': [],
    },
    'external_dependencies': {
        'python': [],
        'bin': []
    },
    'license': 'LGPL-3',
}

