{
    'name': "Etech Payslip Portal",
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Employees',
    'license': 'LGPL-3',
    'summary': 'View and download payslip in portal',
    'author': 'eTech Consulting',
    'website': 'http://www.etechconsulting-mg.com',
    'contributors': "O'Neal RABELAIS - Tech Lead Odoo",
    'depends': [
        'etech_home_portal',
        'hr_payroll'
    ],
    'data': [
        'views/portal_payslip_menu.xml',
        'views/portal_payslip_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            "etech_payslip_portal/static/src/scss/payslip_portal.scss",
        ]
    },
    'installable': True,
    'application': False
}
