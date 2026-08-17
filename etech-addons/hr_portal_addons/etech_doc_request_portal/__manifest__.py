{
    'name': "Etech Docs Request Portal",
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Employees',
    'license': 'LGPL-3',
    'summary': 'Send a document request',
    'author': 'eTech Consulting',
    'website': 'http://www.etechconsulting-mg.com',
    'contributors': "O'Neal RABELAIS",
    'depends': [
        'etech_home_portal',
        'hr',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_document_security.xml',
        'data/ir_sequence.xml',
        'views/res_company.xml',
        'views/hr_document_type_views.xml',
        'views/hr_document_request_views.xml',
        'views/portal_docs_menu.xml',
        'views/portal_docs_request.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            "etech_doc_request_portal/static/src/scss/doc_request_portal.scss",
        ]
    },
    'installable': True,
    'application': False
}
