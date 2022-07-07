# -*- coding: utf-8 -*-
{
    'name': "Odoo Debranding",

    'summary': """Odoo Debranding""",

    'description': """
        Odoo Debranding
    """,

    'author': "Pantilei Ianulov",
    'website': "http://www.yourcompany.com",

    'category': 'Technical',
    'version': '15.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web'],

    # always loaded
    'data': [
        # 'security/debranding_security.xml',
        # 'security/ir.model.access.csv',
        'views/menus.xml',
        'views/login_layout.xml',
        'views/web_layout.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'assets': {
        'web._assets_primary_variables': [],
        'web.assets_backend': [
            'odoo_debranding/static/src/js/user_systray_item.js',
            'odoo_debranding/static/src/js/webclient.js',
        ],
        'web.assets_frontend': [],
        'web.assets_tests': [],
        'web.qunit_suite_tests': [],
        'web.assets_qweb': [],
    },
    'license': 'LGPL-3',
}
