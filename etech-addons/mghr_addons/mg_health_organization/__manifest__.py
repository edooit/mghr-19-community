{
    'name': "Health organization",
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Employees',
    'license': 'LGPL-3',
    'summary': "Management of an employee's health organization",
    'author': 'eTech Consulting',
    'website': 'https://www.etechconsulting-mg.com',
    'contributors': "O'Neal RABELAIS",
    'depends': ['mg_hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/health_organization.xml',
        'views/hr_employee.xml',
        'views/ir_actions_act_window.xml',
        'views/ir_ui_menu.xml'
    ],
    'installable': True,
    'application': False,
}
