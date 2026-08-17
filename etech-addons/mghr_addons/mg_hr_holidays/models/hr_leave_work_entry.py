from odoo import models


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ If an employee is currently working full time but requests a leave next month
            where he has a new contract working only 3 days/week. This should be taken into
            account when computing the number of days for the leave (2 weeks leave = 6 days).
            Override this method to get number of days according to the contract's calendar
            at the time of the leave.
        """
        days = super(HrLeave, self)._get_number_of_days(date_from, date_to, employee_id)
        if employee_id and not self.holiday_status_id.weekend_consideration:
            employee = self.env['hr.employee'].browse(employee_id)
            # Use sudo otherwise base users can't compute number of days
            contracts = employee.sudo()._get_contracts(date_from, date_to, states=['open'])
            contracts |= employee.sudo()._get_incoming_contracts(date_from, date_to)
            calendar = contracts[:1].resource_calendar_id if contracts else None
            return employee._get_work_days_data_batch(
                date_from, date_to, calendar=calendar
            )[employee.id]

        return days
