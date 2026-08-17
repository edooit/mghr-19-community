# -*- coding: utf-8 -*-
{
    'name': "Import Payslip Input",
    'summary': """
     Module to import payslip input value
    """,
    'author': 'eTech Consulting',
    'website': 'https://www.etechconsulting-mg.com/',
    'contributors': "O'Neal RABELAIS",
    'category': 'Human Resources/Employees',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'hr_payroll'
    ],
    'data': [
        'views/hr_payslip_input.xml',
        'views/ir_actions_act_window.xml',
        'views/ir_actions_server.xml',
        'views/ir_ui_menu.xml',
    ],
    'installable': True,
}
