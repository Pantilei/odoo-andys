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
    'depends': ['base', 'web', 'muk_web_theme'],

    # always loaded
    'data': [
        'security/restaurant_management_security.xml',
        'security/ir.model.access.csv',

        'data/cron.xml',

        'views/restaurant_views.xml',
        'views/restaurant_network_views.xml',
        'views/restaurant_audit_view.xml',
        'views/check_list_views.xml',
        'views/check_list_category_views.xml',
        'views/fault_registry_views.xml',

        'wizards/reports.xml',
        'wizards/departaments_reports.xml',
        'wizards/restaurant_reports.xml',

        'views/menu_items.xml',
        'views/res_users.xml',
        'views/res_users_preference.xml',

        'report/layout.xml',
        'report/paper_format.xml',
        'report/fault_list_report.xml',
        'report/restaurants_all_report.xml',
        'report/departaments_report.xml',
        'report/restaurant_report.xml',

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
            'web/static/lib/Chart/Chart.js',
            'restaurant_management/static/src/libs/chartjs-plugin-datalabels.js',

            'restaurant_management/static/src/scss/variables/derived_variables.scss',
            'restaurant_management/static/src/scss/document_viewer.scss',
            'restaurant_management/static/src/scss/reports_action.scss',

            'restaurant_management/static/src/js/documnet_viewer_legacy.js',
            'restaurant_management/static/src/js/many2one_selection_owl_widget.js',
            'restaurant_management/static/src/js/reports_action.js',

            'restaurant_management/static/src/js/json_to_chart_widget.js',

            'restaurant_management/static/src/js/json_to_table_widget.js',
            'restaurant_management/static/src/scss/json_to_table_widget.scss',
        ],
        'web.assets_frontend': [],
        'web.assets_tests': [],
        'web.qunit_suite_tests': [],
        'web.report_assets_common': [
            'restaurant_management/static/src/scss/report_styles.scss',
        ],
        'web.assets_qweb': [
            'restaurant_management/static/src/xml/many2many_binary_preview.xml',
            'restaurant_management/static/src/xml/document_viewer_legacy.xml',
            'restaurant_management/static/src/xml/many2one_selection_owl_widget.xml',
            'restaurant_management/static/src/xml/reports_action.xml',
            'restaurant_management/static/src/xml/json_to_chart_widget.xml',
            'restaurant_management/static/src/xml/json_to_table_widget.xml',
        ],
    },
    'license': 'LGPL-3',
}
