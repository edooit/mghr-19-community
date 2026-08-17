{
    'name': "Etech Payslip Pdf report",
    'summary': """
        Module to manage the PDF printing of the employee's pay slip""",
    'author': 'eTech Consulting',
    'contributors': "O'Neal RABELAIS - Tech Lead Oodoo",
    'website': 'https://www.etechconsulting-mg.com/',
    'category': 'Human Resources/Employees',
    'license': 'LGPL-3',
    "version": "19.0.1.0.0",
    'depends': [
        'mg_hr',
        'mg_hr_payroll',
        'mg_hr_payslip_holidays',
    ],
    'data': [
        'data/paperformat_payroll_report.xml',
        'report/custom_layout_standard.xml',
        'report/report_payslip_templates.xml',
        'report/ir_actions_report.xml'
    ],
    'installable': True,
}
