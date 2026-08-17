{
    'name': "Etech partner fiscal",

    'summary': """
       Module to manage fiscal information of partner
       """,
    'author': 'eTech Consulting',
    'website': 'https://www.etechconsulting-mg.com',
    'contributors': "O'Neal RABELAIS",
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',

    'depends': [
        'contacts',
        'base_vat',
    ],
    'data': [
        'views/res_company.xml',
        'views/res_partner.xml'
    ],
}
