from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    stat = fields.Char('STAT', tracking=True)
