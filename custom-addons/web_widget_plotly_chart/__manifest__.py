{
    "name": "Widget Plotly",
    "summary": """Allow to draw plotly charts.""",
    "author": "LevelPrime srl, Odoo Community Association (OCA)",
    "maintainers": ["pantilei"],
    "website": "https://github.com/OCA/web",
    "category": "Web",
    "version": "15.0.1.0.0",
    "depends": ["web"],
    "data": [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    "external_dependencies": {
        "python": ["plotly==5.14.1"],
    },
    'assets': {
        'web._assets_primary_variables': [],
        'web.assets_backend': [
            'web_widget_plotly_chart/static/src/lib/plotly/plotly-2.20.0.min.js',
            'web_widget_plotly_chart/static/src/js/widget_plotly.js',
        ],
        'web.assets_frontend': [],
        'web.assets_tests': [],
        'web.qunit_suite_tests': [],
        'web.report_assets_common': [],
        'web.assets_qweb': [
            'web_widget_plotly_chart/static/src/xml/widget_plotly.xml'
        ],
    },
    "license": "LGPL-3",
}
