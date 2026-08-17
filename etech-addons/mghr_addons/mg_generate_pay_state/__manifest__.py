{
    'name': "Etech Generate pay state",
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Human Resources/Employees',
    'summary': 'Dynamic pay state generation',
    'author': 'eTech Consulting',
    'website': 'https://www.etechconsulting-mg.com',
    'Contributors': "O'Neal RABELAIS - Tech Lead Odoo",
    'depends': [
        'mg_hr',
        'mg_hr_payroll',
        'mg_hr_payment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payslip_config.xml',
        'views/payslip_resume.xml',
        'views/payslip_resume_column.xml',
        'views/ir_actions_act_window.xml',
        'views/ir_ui_menu.xml'
    ],
    'installable': True,
    'application': False,
}
