import pytz
from odoo import models, fields, api
from datetime import datetime, timedelta, time
from pytz import timezone


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    night_hours = fields.Float(
        compute="_compute_night_hours",
        store=True
    )

    sunday_hours = fields.Float(
        string='Sunday Hours',
        compute='_compute_special_hours',
        store=True,
        help='Number of hours worked on Sundays'
    )

    public_holiday_hours = fields.Float(
        string='Public Holiday Hours',
        compute='_compute_special_hours',
        store=True,
        help='Number of hours worked on public holidays'
    )

    is_sunday = fields.Boolean(
        string='Is Sunday',
        compute='_compute_special_hours',
        store=True
    )

    is_public_holiday = fields.Boolean(
        string='Is Public Holiday',
        compute='_compute_special_hours',
        store=True
    )

    validated_night_hours = fields.Float()
    validated_sunday_hours = fields.Float()
    validated_public_holidays_hours = fields.Float()

    @api.depends(
        'check_in',
        'check_out'
    )
    def _compute_night_hours(self):
        for attendance in self:
            if not attendance.check_in or not attendance.check_out:
                attendance.night_hours = 0.0
                continue

            employee = attendance.employee_id
            company = employee.company_id
            night_start = company.night_start or 22.0
            night_end = company.night_end or 5.0
            night_start_time = time(int(night_start), int((night_start % 1) * 60))
            night_end_time = time(int(night_end), int((night_end % 1) * 60))

            check_in = attendance.check_in
            check_out = attendance.check_out

            tz = pytz.timezone(employee.tz or 'UTC')
            check_in = check_in.astimezone(tz)
            check_out = check_out.astimezone(tz)

            if check_out < check_in:
                check_out += timedelta(days=1)

            total_night_hours = 0.0
            current_time = check_in

            while current_time < check_out:
                next_day = current_time + timedelta(days=1)

                night_start_datetime = tz.localize(datetime.combine(current_time.date(), night_start_time))
                night_end_datetime = tz.localize(
                    datetime.combine(next_day.date(), night_end_time)
                )

                if check_out < night_end_datetime:
                    night_end_datetime = check_out

                if check_in <= night_end_datetime and check_out >= night_start_datetime:
                    start_night = max(check_in, night_start_datetime)
                    end_night = min(check_out, night_end_datetime)
                    total_night_hours += (end_night - start_night).total_seconds() / 3600

                current_time = next_day

            attendance.night_hours = total_night_hours

    def validate_night_hours(self):
        for attendance in self:
            if attendance.night_hours > 0:
                attendance.validated_night_hours = attendance.night_hours

    def validate_sunday_hours(self):
        for attendance in self:
            if attendance.sunday_hours > 0:
                attendance.validated_sunday_hours = attendance.sunday_hours

    def validate_public_holydays_hours(self):
        for attendance in self:
            if attendance.public_holiday_hours > 0:
                attendance.validated_public_holidays_hours = attendance.public_holiday_hours

    @api.depends('check_in', 'check_out')
    def _compute_special_hours(self):
        """
        Compute Sunday hours and public holiday hours based on actual hours worked on those specific days
        """
        for attendance in self:
            if not attendance.check_in or not attendance.check_out:
                attendance.sunday_hours = 0.0
                attendance.public_holiday_hours = 0.0
                attendance.is_sunday = False
                attendance.is_public_holiday = False
                continue

            # Initialize hours
            sunday_hours = 0.0
            public_holiday_hours = 0.0

            # Get user timezone
            user_tz = self.env.user.tz or 'UTC'

            # Convert to user's timezone
            check_in_utc = attendance.check_in
            check_out_utc = attendance.check_out

            check_in_local = check_in_utc.astimezone(timezone(user_tz))
            check_out_local = check_out_utc.astimezone(timezone(user_tz))

            # Check if attendance spans multiple days
            if check_in_local.date() != check_out_local.date():
                # Attendance spans multiple days - calculate hours for each day
                current_date = check_in_local.date()
                end_date = check_out_local.date()

                while current_date <= end_date:
                    # Create datetime objects for day start and end in user timezone
                    day_start = timezone(user_tz).localize(
                        datetime.combine(current_date, time(0, 0, 0))
                    )
                    day_end = timezone(user_tz).localize(
                        datetime.combine(current_date, time(23, 59, 59))
                    )

                    # Calculate overlap between attendance and this day
                    overlap_start = max(check_in_local, day_start)
                    overlap_end = min(check_out_local, day_end)

                    if overlap_start < overlap_end:
                        day_hours = (overlap_end - overlap_start).total_seconds() / 3600.0

                        # Check if this day is Sunday
                        if current_date.weekday() == 6:  # 6 = Sunday
                            sunday_hours += day_hours

                        # Check if this day is public holiday
                        if self._is_public_holiday(current_date):
                            public_holiday_hours += day_hours

                    current_date += timedelta(days=1)
            else:
                # Attendance is within the same day (minus 1h lunch break)
                day_hours = max(attendance.worked_hours - 1.0, 0.0)
                current_date = check_in_local.date()

                if current_date.weekday() == 6:  # Sunday
                    sunday_hours = day_hours

                if self._is_public_holiday(current_date):
                    public_holiday_hours = day_hours

            attendance.sunday_hours = sunday_hours
            attendance.public_holiday_hours = public_holiday_hours
            attendance.is_sunday = bool(sunday_hours > 0)
            attendance.is_public_holiday = bool(public_holiday_hours > 0)

    def _is_public_holiday(self, date):
        """
        Check if the given date is a public holiday
        """
        holiday_days = self.env['resource.calendar.leaves'].search(
            [
                ('date_from', '<=', date),
                ('date_to', '>=', date),
                ('work_entry_type_id.code', '=', 'LEAVE100')
            ]
        )
        return bool(holiday_days)

    def get_employee_special_hours(self, employee_id, date_from, date_to):
        """
        Get total Sunday and public holiday hours for an employee in a date range
        """
        domain = [
            ('employee_id', '=', employee_id),
            ('check_in', '>=', date_from),
            ('check_out', '<=', date_to)
        ]

        attendances = self.search(domain)

        total_night_hours = sum(attendances.mapped('validated_night_hours'))
        total_sunday_hours = sum(attendances.mapped('validated_sunday_hours'))
        total_public_holiday_hours = sum(attendances.mapped('validated_public_holidays_hours'))

        return {
            'night_hours': total_night_hours,
            'sunday_hours': total_sunday_hours,
            'public_holiday_hours': total_public_holiday_hours,
            'total_special_hours': total_sunday_hours + total_public_holiday_hours
        }
