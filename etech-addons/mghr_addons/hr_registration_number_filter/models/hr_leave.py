# -*- coding: utf-8 -*-

from odoo import fields, models


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    registration_number = fields.Char(
        string="Registration number",
        related='employee_id.registration_number',
        store=True
    )
