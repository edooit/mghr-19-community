{
    'name': "Etech Leave Portal",
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Employees',
    'license': 'LGPL-3',
    'summary': 'Leave request from Website (portal)',
    'author': 'eTech Consulting',
    'website': 'https://www.etechconsulting-mg.com',
    'contributors': "O'Neal RABELAIS - Tech Lead Odoo",
    'depends': [
        'web',
        'etech_home_portal',
        'hr_holidays'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee.xml',
        'views/hr_leave.xml',
        'views/portal_leave_menu.xml',
        'views/portal_create_leave.xml',
        'views/portal_edit_leave.xml',
        'views/portal_unified_leaves.xml',
        'views/portal_leave_details.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'etech_leave_portal/static/src/js/modal_utils.js',
            'etech_leave_portal/static/src/js/leave_portal_unified.js',
            'etech_leave_portal/static/src/js/leave_form_portal.js',
            'etech_leave_portal/static/src/scss/leave_portal.scss',
        ],
        # loaded on-demand, only when the calendar view is actually displayed
        # (see views/portal_unified_leaves.xml) instead of on every frontend page
        'etech_leave_portal.assets_calendar': [
            'web/static/lib/fullcalendar/core/index.global.js',
            'web/static/lib/fullcalendar/interaction/index.global.js',
            'web/static/lib/fullcalendar/daygrid/index.global.js',
            'web/static/lib/fullcalendar/timegrid/index.global.js',
            'web/static/lib/fullcalendar/list/index.global.js',
            'web/static/lib/fullcalendar/luxon3/index.global.js',
        ],
    },
    'installable': True,
    'application': False
}
