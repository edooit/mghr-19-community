{
    'name': "Mg hr payroll",

    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'category': '',
    'summary': '',
    'author': 'eTech Consulting',
    'website': 'https://www.etechconsulting-mg.com',
    'depends': [
        'mg_hr',
        'mg_hr_category',
    ],
    'data': [
        'security/ir.model.access.csv',

        'data/hr_payroll_structure_type.xml',
        'data/hr_payroll_structure.xml',
        'data/hr_work_entry_type.xml',
        'data/hr_leave_type.xml',
        'views/hr_salary_rule.xml'
    ],
    'assets': {
        'web.report_assets_common': [
            'mg_hr_payroll/static/src/css/pdf_report.css'
        ]
    },
    'installable': True,
    'application': False,
}
