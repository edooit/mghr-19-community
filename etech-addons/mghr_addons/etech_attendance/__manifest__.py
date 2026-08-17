{
    'name': "Etech Attendance",
    'summary': """
     Module to manage attendance 
    """,
    'author': 'eTech Consulting',
    'website': 'https://www.etechconsulting-mg.com/',
    'contributors': "O'Neal RABELAIS - Tech Lead Odoo",
    'category': 'Human Resources/Employees',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'hr_attendance'
    ],
    'data': [
        'views/hr_attendance.xml',
        'views/res_company.xml'

    ],
    'installable': True,
}
