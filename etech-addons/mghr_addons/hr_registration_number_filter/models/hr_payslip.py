# -*- coding: utf-8 -*-

from odoo import fields, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    registration_number = fields.Char(
        string="Registration number",
        related='employee_id.registration_number',
        store=True
    )
