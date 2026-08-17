from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    email_docs = fields.Many2many(
        'hr.employee',
        domain="[('company_id', '=', id)]"
    )
