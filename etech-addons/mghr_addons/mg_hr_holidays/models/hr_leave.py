import math
from datetime import datetime, timedelta

from dateutil.rrule import DAILY, rrule

from odoo import api, models


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def _get_date_reprise(self, date_to):
        """
            Get the reprise date to put in report
            :param date_to:
            :return datetime:
        """
        return (self.date_to + timedelta(days=1)).strftime("%d/%m/%Y")

    @api.model
    def format_leave(self, x):
        return math.floor(x * 10) / 10

    def _get_durations(self, check_leave_type=True, resource_calendar=None):
        """
        Consider weekend_consideration field in leave duration computation
        """
        for rec in self:
            if rec.holiday_status_id.weekend_consideration and not rec.request_unit_half and rec.date_to.date().weekday() == 4:
                rec.request_date_to = rec.date_to + timedelta(days=2)
        result = super(HrLeave, self)._get_durations(check_leave_type, resource_calendar)
        for rec in self:
            days, hours = result.get(rec.id, False)
            if not rec.holiday_status_id.weekend_consideration:
                range_days = {rec.date_to.date() - timedelta(d) for d in range((rec.date_to - rec.date_from).days + 1)}
                weekends = {d for d in range_days if d.weekday() > 4}
                if not rec.holiday_status_id.include_public_holidays_in_duration:
                    holidays = self.env['resource.calendar.leaves'].search([
                        ('date_from', '>=', rec.date_to),
                        ('date_to', '<=', rec.date_to),
                        ('work_entry_type_id.code', '=', 'LEAVE100')
                    ])
                    holidays_list = {
                        (h.date_from + timedelta(days=i)).date()
                        for h in holidays
                        for i in range((h.date_to.date() - h.date_from.date()).days + 1)
                    }
                    weekends -= holidays_list
                days_out = len(weekends)
                if days_out:
                    days -= days_out
                    hours = days * self.env.company.resource_calendar_id.hours_per_day
                    result[rec.id] = (days, hours)
        return result
