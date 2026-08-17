# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"
    _populate_sizes = {"small": 100, "medium": 800, "large": 10000}
    _populate_dependencies = ['hr.employee', 'hr.leave.type']

    def _get_future_leaves_on_spec(self, accrual_date):
        # As computing future accrual allocation days automatically updates the allocation,
        # We need to create a temporary copy of
        # that allocation to return the difference in number of days
        # to see how much more days will be allocated from now until that date.
        self.ensure_one()
        if not accrual_date:
            return 0

        if not (self.accrual_plan_id
                and self.state == 'validate'
                and self.allocation_type == 'accrual'
                and (not self.date_to or self.date_to > accrual_date)
                and (not self.nextcall or self.nextcall <= accrual_date)):
            return 0

        fake_allocation = self.env['hr.leave.allocation'].new(origin=self)
        fake_allocation.sudo()._process_accrual_plans(accrual_date, log=False)
        result = round((fake_allocation.number_of_days - self.number_of_days), 2)

        # Explicitly delete fake_allocation
        del fake_allocation
        return result
