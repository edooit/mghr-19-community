{
    'name': "Mg Hr Payment",
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Employees',
    'summary': 'Customization of HR module',
    'author': 'eTech Consulting',
    'website': 'https://www.etechconsulting-mg.com',
    'contributors': "O'Neal RABELAIS",
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_payment_mode_data.xml',
        'views/hr_payslip_payment_mode.xml',
        'views/hr_employee.xml',
        'views/ir_actions_act_window.xml',
        'views/ir_ui_menu.xml'
    ],
    'qweb': [],
    'demo': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
