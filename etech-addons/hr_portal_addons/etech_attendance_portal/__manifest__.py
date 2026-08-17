{
    'name': "Etech Attendance portal",
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Employees',
    'license': 'LGPL-3',
    'summary': 'Show attendance story',
    'author': 'eTech Consulting',
    'website': 'https://www.etechconsulting-mg.com',
    'contributors': "O'Neal RABELAIS - Tech Lead Odoo",
    'depends': [
        'etech_home_portal',
        'etech_late_attendance'
    ],
    'data': [
        'views/portal_attendance_menu.xml',
        'views/my_attendance_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'etech_attendance_portal/static/src/scss/attendance_portal.scss',
        ],
    },
    'installable': True,
    'application': False
}
