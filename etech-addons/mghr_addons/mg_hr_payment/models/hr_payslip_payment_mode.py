from odoo import fields, models


class HrPayslipPaymentMode(models.Model):
    _name = 'hr.payslip.payment.mode'
    _description = 'Payment Mode'

    name = fields.Char(required=True)
    note = fields.Text(string='Description')
