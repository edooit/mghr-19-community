{
    'name': 'Registration number filter',
    'summary': '''
        Add registration number filter on leave, leave allocation and payslip''',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'eTech Consulting',
    'Contributors': "O'Neal RABELAIS",
    'website': 'https://www.etechconsulting-mg.com/',
    'depends': [
        'hr',
        'hr_payroll',
        'hr_holidays'
    ],
    'data': [
        'views/hr_attendance.xml',
        'views/employee.xml',
        'views/hr_payslip.xml',
        'views/hr_leave_allocation.xml',
        'views/hr_leave.xml'
    ],
    'installable': True,

}
