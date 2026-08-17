{
    'name': "Hr Contract category",
    'category': 'Human Resources/Category',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'summary': """
        Module to manage the contract category
        """,
    'author': 'eTech Consulting',
    'contributors': "O'Neal RABELAIS",
    'website': 'https://www.etechconsulting-mg.com',
    'depends': [
        'mg_hr'
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/hr_category_data.xml',
        'data/hr_contract_type_data.xml',
        'views/hr_category.xml',
        'views/hr_employee.xml',
        'views/hr_index.xml',
        'views/ir_actions_act_window.xml',
        'views/ir_ui_menu.xml'
    ],

    'installable': True
}
