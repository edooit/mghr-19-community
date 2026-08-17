from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    payslip_payment_mode_id = fields.Many2one('hr.payslip.payment.mode')
