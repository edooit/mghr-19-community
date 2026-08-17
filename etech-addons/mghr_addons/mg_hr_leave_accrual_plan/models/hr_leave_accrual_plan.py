import calendar
from datetime import timedelta
from odoo import models, fields, api


class Employee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def create(self, vals):
        employee = super(Employee, self).create(vals)
        employee._create_leave_allocation()
        return employee

    def _create_leave_allocation(self):
        self.ensure_one()
        hiring_date = fields.Date.from_string(self.hiring_date)
        today = fields.Date.today()
        if hiring_date.month == today.month and hiring_date.year == today.year:
            holiday_status = self.env['hr.leave.type'].search(
                [
                    ('work_entry_type_id.code', '=', 'LEAVE120')
                ]
            )
            accrual_plan = self.env.ref(
                'mg_hr_leave_accrual_plan.employee_accrual_plan'
            )
            if holiday_status and accrual_plan:
                allocation_vals = {
                    'name': f'Allocation - {self.name}',
                    'holiday_status_id': holiday_status.id,
                    'allocation_type': 'accrual',
                    'accrual_plan_id': accrual_plan.id,
                    'employee_ids': [(6, 0, [self.id])],
                    'date_from': today - timedelta(days=1),
                    'date_to': False,
                    'department_id': self.department_id.id,
                    'employee_id': self.id,
                    'state': 'confirm',
                    'number_of_days': 0
                }
                allocation = self.env['hr.leave.allocation'].sudo().create(allocation_vals)