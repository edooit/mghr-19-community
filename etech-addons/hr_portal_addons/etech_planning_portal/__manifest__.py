{
    'name': 'Etech Planning Portal',
    'version': '19.0.1.0.0',
    'summary': 'Planning management via the portal with Gantt view',
    'description': """
     Planning management module with Gantt view accessible via the portal
        with permissions based on employee hierarchy.
    """,
    'author': 'Etech Consulting',
    'contributors': "O'Neal RABELAIS - Tech Lead Odoo",
    'website': 'https://www.etechconsulting-mg.com',
    'category': 'Human Resources/Leave',
    'depends': [
        'etech_home_portal',
        'planning',
        'web_gantt',
    ],
    "data": [
        "views/planning_portal_template.xml",
        "views/portal_planning_menu.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            "etech_planning_portal/static/src/scss/planning_portal.scss",
            "etech_planning_portal/static/src/js/planning_portal_gantt.js",
        ]
    },

    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
