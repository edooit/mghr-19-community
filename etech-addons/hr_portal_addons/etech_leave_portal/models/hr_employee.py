# -*- coding: utf-8 -*-

from odoo import models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _get_portal_leave_balance(self):
        """Paid leave balance (LEAVE120) shown on the leave portal."""
        self.ensure_one()
        domain_alloc = [
            ('state', '=', 'validate'),
            ('employee_id', '=', self.id),
            ('holiday_status_id.active', '=', True),
            ('holiday_status_id.work_entry_type_id.code', '=', 'LEAVE120'),
        ]
        domain_taken = [
            ('state', 'in', ['validate1', 'validate']),
            ('employee_id', '=', self.id),
            ('holiday_status_id.work_entry_type_id.code', '=', 'LEAVE120'),
        ]
        leave_allocations = self.env['hr.leave.allocation'].sudo().search(domain_alloc)
        leave_total = sum(leave_allocations.mapped('number_of_days_display'))
        leave_taken = sum(self.env['hr.leave'].sudo().search(domain_taken).mapped('number_of_days'))

        return {
            'leave_balance': round(leave_total - leave_taken, 2),
            'leave_taken': round(leave_taken, 2),
            'leave_allocations': round(leave_total, 2),
        }
