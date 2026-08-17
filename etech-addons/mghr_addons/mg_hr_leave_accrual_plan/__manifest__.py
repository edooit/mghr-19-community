# -*- coding: utf-8 -*-
{
    'name': "Create Leave Accrual Plan",
    'summary': """
     Automatic creation of accumulation plan for an employee
    """,
    'author': 'eTech Consulting',
    'website': 'https://www.etechconsulting-mg.com/',
    'contributors': "O'Neal RABELAIS - Tech Lead Oodoo",
    'category': 'Human Resources/Employees',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'mg_hr',
        'hr_holidays'
    ],
    'data': [
        'data/hr_leave_accrual_plan.xml'
    ],
    'installable': True,
}
