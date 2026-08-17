from odoo import api, fields, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    leave_allocation = fields.Float(readonly=True,
                                    string='Current Leave Balance',
                                    compute='_compute_current_leave_balance', digits=(6, 2))
    show_leave_allocation = fields.Boolean(related="struct_id.show_leave_allocation")

    @api.depends('date_from', 'date_to')
    def _compute_current_leave_balance(self):
        for payslip in self:
            if self.employee_id:
                payslip.leave_allocation = self.get_remaining_leaves_120(self.date_to)
            else:
                payslip.leave_allocation = 0

    def get_remaining_leaves_120(self, target_date):
        """
        Helper to compute the remaining leaves for the current employees
        """
        paid_time_of_id = self.env['hr.leave.type'].search([(
            'work_entry_type_id.code',
            '=',
            'LEAVE120')
        ])
        current_leaves = 0
        # check if self.date_from is not set
        if not target_date:
            return 0
        for paid_id in paid_time_of_id:
            # get all allocation and leaves taken without accrual
            self._cr.execute("""
                   SELECT
                           sum(h.number_of_days) AS days,
                           h.employee_id
                       FROM
                           (
                               SELECT holiday_status_id, number_of_days,
                                   state, employee_id
                               FROM hr_leave_allocation
                               WHERE date_from <= %s
                               UNION ALL
                               SELECT holiday_status_id, (number_of_days * -1) as number_of_days,
                                   state, employee_id
                               FROM hr_leave
                               WHERE date_from <= %s
                           ) h
                           JOIN hr_leave_type s ON (s.id=h.holiday_status_id)
                       WHERE
                           s.active = true AND h.state='validate' AND
                           s.requires_allocation='yes' AND
                           s.id = %s AND
                           h.employee_id IN (%s)
                       GROUP BY h.employee_id""", (target_date,
                                                   target_date,
                                                   paid_id.id,
                                                   self.employee_id.id))
            result = self._cr.dictfetchone()
            if result:
                current_leaves += result['days']
            # get Accrual allocation
            allocations = self.env["hr.leave.allocation"].search(
                [('allocation_type', '=', 'accrual'), ('state', '=', 'validate'),
                 ('employee_id', '=', self.employee_id.id),
                 ('date_from', '<=', target_date),
                 ('holiday_status_id', '=', paid_id.id)
                 ])
            accrual_days = 0.0
            if allocations:
                for allocation in allocations:
                    accrual_days += allocation._get_future_leaves_on_spec(target_date)
            current_leaves += accrual_days
            # add the result
        return current_leaves
