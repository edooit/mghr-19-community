# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from pytz import timezone, UTC, utc
import logging

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    expected_arrival = fields.Float(
        string="Expected Arrival",
        help="Expected arrival time in float format (e.g., 8.5 for 08:30)"
    )
    state = fields.Selection(
        [
            ('on_time', 'On time'),
            ('late', 'Late')
        ],
        string="Status",
        default='on_time'
    )
    delay_time = fields.Float(
        string="Delay Time",
        readonly=True,
        help="Delay in hours if the employee is late."
    )

    @api.model_create_multi
    def create(self, vals_list):
        # Decide, per vals, whether lateness should be checked, based on
        # attendance already existing *before* this batch is created.
        should_check_list = []
        for vals in vals_list:
            check_in = vals.get('check_in')
            should_check = False
            if check_in:
                check_in_date = fields.Datetime.from_string(check_in).date()
                existing_attendance = self.search(
                    [
                        ('employee_id', '=', vals.get('employee_id')),
                        ('check_in', '>=', datetime.combine(check_in_date, datetime.min.time())),
                        ('check_in', '<=', datetime.combine(check_in_date, datetime.max.time())),
                    ]
                )
                should_check = not existing_attendance
            should_check_list.append(should_check)

        records = super().create(vals_list)

        for record, should_check in zip(records, should_check_list):
            if should_check:
                record._check_late_or_on_time()

        return records

    def write(self, vals):
        res = super().write(vals)

        # _check_late_or_on_time() writes back expected_arrival/state/delay_time,
        # which would re-enter write() and call _check_late_or_on_time() again
        # (infinite recursion). The context flag marks that recompute as
        # internal so it doesn't trigger itself.
        if {'check_in', 'expected_arrival'} & set(vals) and not self.env.context.get('skip_late_recompute'):
            self._check_late_or_on_time()

        return res

    def _get_employee_planning_slot(self, employee, check_in_datetime):
        """
        Find the planning slot closest to this check-in: fetch every slot
        within a day and a half around check-in, then keep the one whose
        scheduled start is nearest to check_in_datetime. This single rule
        covers on-time, late, early and overnight (night shift) check-ins
        without a cascade of special-cased searches.

        Args:
            employee: hr.employee record
            check_in_datetime: datetime of check-in (naive)

        Returns:
            planning.slot record or None
        """
        if not check_in_datetime:
            return None

        check_in_date = check_in_datetime.date()
        window_start = datetime.combine(check_in_date - timedelta(days=1), datetime.min.time())
        window_end = datetime.combine(check_in_date + timedelta(days=1), datetime.max.time())

        slots = self.env['planning.slot'].search(
            [
                ('resource_id.employee_id', '=', employee.id),
                ('start_datetime', '>=', window_start),
                ('start_datetime', '<=', window_end),
            ]
        )

        if not slots:
            _logger.warning(
                _("    ⚠️ No planning slot found for employee %s around %s"),
                employee.name, check_in_datetime
                )
            return None

        slot = min(slots, key=lambda s: abs(s.start_datetime - check_in_datetime))

        _logger.info(
            _("    📅 Slot found: %s -> %s for check-in %s"),
            slot.start_datetime, slot.end_datetime, check_in_datetime
            )
        return slot

    def _check_late_or_on_time(self):
        """
        Check if employee is late or on time based on planning slot

        Improved logic:
        - Uses the new _get_employee_planning_slot method
        - Handles timezone conversion properly
        - Handles edge cases (late, no slot, etc.)
        """
        for rec in self:
            if not rec.check_in or not rec.employee_id:
                _logger.warning(_("    ⚠️ No check_in or employee_id for attendance %s"), rec.id)
                continue

            employee = rec.employee_id

            # Get check-in datetime (naive)
            check_in_dt = rec.check_in
            if isinstance(check_in_dt, str):
                check_in_dt = fields.Datetime.from_string(check_in_dt)

            _logger.info(_("    🕐 Checking lateness for %s - check_in: %s"), employee.name, check_in_dt)

            # Find the corresponding planning slot
            planning_slot = self._get_employee_planning_slot(employee, check_in_dt)

            if not planning_slot:
                # No slot found - cannot determine lateness
                _logger.warning(_("    ⚠️ Cannot determine lateness for %s - no planning slot found"), employee.name)
                rec.with_context(skip_late_recompute=True).write({
                    'expected_arrival': 0.0,
                    'state': 'on_time',  # Default to on_time when no slot
                    'delay_time': 0.0,
                })
                continue

            # Get company lateness tolerance
            company = employee.company_id or self.env.company
            lateness_tolerance = company.minutes_late if hasattr(company, 'minutes_late') else 0.0
            lateness_tolerance_hours = lateness_tolerance

            # Get employee timezone
            employee_tz = timezone(employee.tz or 'UTC')

            # ============================================================
            # Calculate expected arrival time
            # ============================================================
            # planning_slot.start_datetime is already in UTC (Odoo stores UTC)
            slot_start_utc = planning_slot.start_datetime

            # Convert slot start to employee's timezone
            if slot_start_utc.tzinfo is None:
                slot_start_utc = utc.localize(slot_start_utc)

            slot_start_local = slot_start_utc.astimezone(employee_tz)

            # Expected arrival in float format (e.g., 8.5 for 08:30)
            expected_arrival = slot_start_local.hour + slot_start_local.minute / 60.0

            _logger.info(
                _("    📅 Expected arrival: %s (float: %s)"),
                slot_start_local.strftime('%H:%M'), expected_arrival
                )

            # ============================================================
            # Calculate actual check-in time
            # ============================================================
            # rec.check_in is naive, assume UTC
            check_in_utc = check_in_dt
            if check_in_utc.tzinfo is None:
                check_in_utc = utc.localize(check_in_utc)

            check_in_local = check_in_utc.astimezone(employee_tz)
            check_in_float = check_in_local.hour + check_in_local.minute / 60.0

            _logger.info(
                _("    🕐 Actual check-in: %s (float: %s)"),
                check_in_local.strftime('%H:%M'), check_in_float
                )

            # ============================================================
            # Determine if late or on time
            # ============================================================
            threshold = expected_arrival + lateness_tolerance_hours

            _logger.info(
                _("    ⚖️ Threshold: %s (expected: %s + tolerance: %s hours)"),
                threshold, expected_arrival, lateness_tolerance_hours
                )

            if check_in_float <= threshold:
                state = 'on_time'
                delay_time = 0.0
                _logger.info(_("    ✅ Employee %s is ON TIME"), employee.name)
            else:
                state = 'late'
                delay_time = check_in_float - threshold
                _logger.info(_("    ❌ Employee %s is LATE by %s hours"), employee.name, delay_time)

            rec.with_context(skip_late_recompute=True).write({
                'expected_arrival': expected_arrival,
                'state': state,
                'delay_time': delay_time,
            })