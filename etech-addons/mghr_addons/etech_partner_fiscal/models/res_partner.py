from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    rcs = fields.Char('RCS', tracking=True)
    stat = fields.Char('STAT', tracking=True)
    cin = fields.Char('CIN', tracking=True, size=12)
