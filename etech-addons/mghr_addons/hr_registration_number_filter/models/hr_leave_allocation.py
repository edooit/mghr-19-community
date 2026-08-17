# -*- coding: utf-8 -*-

from odoo import fields, models


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    registration_number = fields.Char(
        string="Registration number",
        related='employee_id.registration_number',
        store=True
    )
