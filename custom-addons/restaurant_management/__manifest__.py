# -*- coding: utf-8 -*-
{
    'name': "Restaurant Management",

    'summary': """Restaurant Management""",

    'description': """
        Restaurant Management
    """,

    'author': "Pantilei Ianulov",
    'website': "http://www.yourcompany.com",

    'category': 'Technical',
    'version': '15.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/restaurant_management_security.xml',

        'data/cron.xml',

        'views/restaurant_views.xml',
        'views/restaurant_audit.xml',
        'views/fault_views.xml',
        'views/fault_registry_views.xml',
        'views/fault_category_views.xml',
        'views/restaurant_management_menu_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
        'web._assets_primary_variables': [],
        'web.assets_backend': [
            'restaurant_management/static/src/js/many2many_binary_preview.js',
            'restaurant_management/static/src/js/documnet_viewer_legacy.js',
        ],
        'web.assets_frontend': [],
        'web.assets_tests': [],
        'web.qunit_suite_tests': [],
        'web.assets_qweb': [
            'restaurant_management/static/src/xml/many2many_binary_preview.xml',
            'restaurant_management/static/src/xml/document_viewer_legacy.xml',
        ],
    },
    'license': 'LGPL-3',
}
