{
    'name': "Sanction",
    'summary': """
        """,
    'author': 'eTech Consulting',
    'website': 'https://www.etechconsulting-mg.com/',
    'category': 'Human Resources/Sanction',
    'license': 'LGPL-3',
    'version': '19.0.1.0.0',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/sanction_type_data.xml',
        'views/hr_sanction.xml',
        'views/hr_sanction_type.xml',
        'views/hr_employee.xml',
        'views/ir_actions_act_window.xml',
        'views/ir_ui_menu.xml'
    ],
}
