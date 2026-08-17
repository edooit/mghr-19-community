{
    'name': "People nationality",

    'summary': """
       Module to manage nationality of people""",
    'author': 'eTech Consulting',
    'website': 'https://www.etechconsulting-mg.com',
    'contributors': "O'Neal RABELAIS",
    'license': 'LGPL-3',
    'category': 'Human Resources/Employees',
    'version': '19.0.1.0.0',
    'depends': [
        'contacts',
        'hr'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/nationality_data.xml',
        'views/people_nationality.xml',
        'views/hr_employee.xml',
        'views/ir_actions_act_window.xml',
        'views/ir_ui_menu.xml'
    ],
}
