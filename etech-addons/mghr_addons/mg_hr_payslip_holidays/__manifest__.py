{
    'name': "Mg payslip holidays",
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Human Resources/Employees',
    'sequence': 10,
    'summary': 'Leave management in pay slip',
    'author': 'eTech Consulting',
    'website': 'https://www.etechconsulting-mg.com',
    'depends': [
        'mg_hr_payroll'
    ],
    'data': [
        'views/hr_leave_type_views.xml',
        'views/hr_payroll_structure.xml',
        'views/hr_payslip.xml',
    ],
    'qweb': [],
    'demo': [],
    'installable': True,
    'application': False,
}
