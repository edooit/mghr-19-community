{
    'name': "Etech home portal",
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Employees',
    'license': 'LGPL-3',
    'summary': 'Leave request from Website (portal)',
    'author': 'eTech Consulting',
    'website': 'https://www.etechconsulting-mg.com',
    'contributors': "O'Neal RABELAIS - Tech Lead",
    'depends': [
        'contacts',
        'portal',
        'mg_hr',
        'mg_hr_category',
    ],
    'data': [
        'views/portal_home_template.xml',
        'views/portal_layout_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            "etech_home_portal/static/src/scss/home_portal.scss",
        ]
    },
    'installable': True,
    'application': False
}
