from odoo import fields, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    rib_key = fields.Char()
    bank_code = fields.Char(
        default="00000",
        size=5,
        string="Bank code"
    )
    agency_code = fields.Char()
    box_code = fields.Char(
        default="00000",
        string="Box code"
    )
    ref_transfert = fields.Char(
        string="Reference"
    )

    _sql_constraints = [
        ('unique_number', 'UNIQUE(acc_number)', 'Account Number must be unique'),
    ]
