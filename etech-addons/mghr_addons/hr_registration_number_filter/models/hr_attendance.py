# -*- coding: utf-8 -*-

from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    registration_number = fields.Char(
        related='employee_id.registration_number',
        store=True
    )
