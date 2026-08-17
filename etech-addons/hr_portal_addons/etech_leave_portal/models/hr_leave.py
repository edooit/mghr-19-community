# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    reason = fields.Char()

    def _check_double_validation_rules(self, employees, state):
        if self.env.user.has_groups('hr_holidays.group_hr_holidays_manager'):
            return

        is_leave_user = self.env.user.has_groups('hr_holidays.group_hr_holidays_user') \
                        or self.env.user.has_groups('base.group_portal')
        if state == 'validate1':
            employees = employees.filtered(lambda employee: employee.leave_manager_id != self.env.user)
            if employees and not is_leave_user:
                raise AccessError(
                    _(
                        'You cannot first approve a time off for %s, because you are not his time off manager',
                        employees[0].name
                    )
                )
        elif state == 'validate' and not is_leave_user:
            # Is probably handled via ir.rule
            raise AccessError(_('You don\'t have the rights to apply second approval on a time off request'))

