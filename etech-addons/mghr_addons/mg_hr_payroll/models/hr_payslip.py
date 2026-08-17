import calendar
from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from odoo import fields, models
from odoo.tools import float_round


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    stc = fields.Float(
        'Number of days not worked',
        default=0.0
    )
    work_location_id = fields.Many2one(
        'hr.work.location',
        related='employee_id.work_location_id',
        store=True
    )
    work_zone_id = fields.Many2one(
        'hr.work.zone', string="Work location zone",
        related='work_location_id.zone_id',
        store=True,
        readonly=True
    )

    department_id = fields.Many2one(
        'hr.department',
        related='employee_id.department_id',
        store=True
    )

    category_id = fields.Many2one(
        'hr.contract.category',
        related='employee_id.category_id'
    )
    index_id = fields.Many2one(
        'hr.contract.index',
        related='employee_id.index_id'
    )
    show_classification = fields.Boolean(
        related="struct_id.show_classification",
        store='True'
    )

    def _get_base_local_dict(self):
        return {
            **super(HrPayslip, self)._get_base_local_dict(),

            'date': date,
            'datetime': datetime,
            'relativedelta': relativedelta,
        }

    def _get_worked_day_lines_values(self, domain=None):
        """
        Override work entry number of days for maternity absence
        :param domain:
        :return:
        """
        self.ensure_one()
        res = self._get_worked_day_lines_values_hours_per_day()

        for work_day_line_id in res:
            work_entry_type = self.env['hr.work.entry.type'].browse(
                work_day_line_id.get('work_entry_type_id')
            )

            # Calculation of maternity leave
            maternity_leave_ids = self.env['hr.leave'].search(
                [
                    ('employee_id', '=', self.employee_id.id),
                    ('state', '=', 'validate'),
                    ('date_from', '<=', self.date_to),
                    ('date_to', '>=', self.date_from),
                    ('holiday_status_id.weekend_consideration', '=', True),
                    ('holiday_status_id.work_entry_type_id.code', '=', 'MATERNITY_LEAVE'),
                ]
            )
            maternity_day = 0

            if work_entry_type.id == maternity_leave_ids.mapped(
                    'holiday_status_id'
            ).work_entry_type_id.id:
                for leave in maternity_leave_ids:
                    l_date_from = max(self.date_from, leave.date_from.date())
                    l_date_to = min(self.date_to, leave.date_to.date())
                    last_day_of_month = calendar.monthrange(l_date_to.year, l_date_to.month)
                    if l_date_to.day in [31]:
                        l_date_to = l_date_to.replace(day=30)
                    elif l_date_to.month == 2 and l_date_to.day == last_day_of_month[1]:
                        adjust = 30 - l_date_to.day
                        maternity_day += adjust
                    maternity_day += (l_date_to - l_date_from).days + 1

                    # Update number_of_days and number_of_hours for work_entry maternity_line
                work_day_line_id.update(
                    {
                        'number_of_days': maternity_day,
                        'number_of_hours': 173.33 if
                        maternity_day == 30 else round((173.33 * maternity_day), 2) / 30
                    }
                )

        return res

    def _round_days(self, work_entry_type, days):
        if work_entry_type.round_days != 'NO':
            precision_rounding = 0.5 if work_entry_type.round_days == "HALF" else 1
            day_rounded = float_round(
                days, precision_rounding=precision_rounding,
                rounding_method=work_entry_type.round_days_type
                )
            return day_rounded
        return days

    def _get_worked_day_lines_values_hours_per_day(self, domain=None):
        """
        Call this function to get all the work entries hours per day
        """
        self.ensure_one()
        res = []
        hours_per_day = self._get_worked_day_lines_hours_per_day()
        # hr.contract was merged into hr.version in Odoo 19; work-hours
        # computation now lives on the payslip's version_id instead of
        # being callable directly on hr.payslip (or the old contract_id).
        work_hours = self.version_id.get_work_hours(
            self.date_from,
            self.date_to,
            domain=domain
        )
        work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
        biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
        add_days_rounding = 0
        for work_entry_type_id, hours in work_hours_ordered:
            work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
            days = round(hours / hours_per_day, 5) if hours_per_day else 0
            if work_entry_type_id == biggest_work:
                days += add_days_rounding
            day_rounded = self._round_days(work_entry_type, days)
            add_days_rounding += (days - day_rounded)
            attendance_line = {
                'sequence': work_entry_type.sequence,
                'work_entry_type_id': work_entry_type_id,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        return res
