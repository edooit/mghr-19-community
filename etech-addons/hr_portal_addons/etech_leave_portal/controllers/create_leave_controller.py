import base64
from datetime import datetime
from pytz import UTC, timezone
from odoo.tools.date_utils import float_to_time
from odoo import http, _, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class CreateLeaveCustomerPortal(CustomerPortal):

    def _get_allowed_employees(self, user_id):
        """Employees this user may create/edit a leave for: themselves, plus
        their direct reports (parent_id = hierarchical manager). This is the
        portal-side approval hierarchy — deliberately not hr.employee's
        leave_manager_id, which is the backend/HR second-level approver and
        may not even have portal access."""
        employee = user_id.employee_id
        team_employees = request.env['hr.employee'].sudo().search(
            [('parent_id.user_id', '=', user_id.id)]
        )
        return employee | team_employees

    def _get_available_leave_types(self):
        domain = [
            '|',
            ('requires_allocation', '=', 'no'),
            '&', ('has_valid_allocation', '=', True),
            '&', ('virtual_remaining_leaves', '>', 0),
            ('max_leaves', '>', 0)
        ]
        return request.env['hr.leave.type'].sudo().search(domain)

    def _prepare_create_leave_values(self):
        """Prepare values for leave creation form"""
        user_id = request.env.user
        return {
            'employees': self._get_allowed_employees(user_id),
            'leave_types': self._get_available_leave_types(),
            'default_employee_id': user_id.employee_id.id if user_id.employee_id else False,
            'page_name': 'create_leave',
            'current_date': fields.Date.today().strftime('%Y-%m-%d'),
        }

    def _prepare_edit_leave_values(self, leave_id):
        """Prepare values for leave edit form"""
        leave = request.env['hr.leave'].sudo().browse(leave_id)

        if not leave.exists():
            return {'error': _('Leave request not found.')}
        user_id = request.env.user
        employees = self._get_allowed_employees(user_id)

        if leave.employee_id not in employees:
            return {'error': _('You are not allowed to edit this leave request.')}

        balance_data = leave.employee_id._get_portal_leave_balance()

        return {
            'leave': leave,
            'employees': employees,
            'leave_types': self._get_available_leave_types(),
            'page_name': 'edit_leave',
            'current_date': fields.Date.today().strftime('%Y-%m-%d'),
            'leave_balance': balance_data.get('leave_balance', 0),
            'leave_taken': balance_data.get('leave_taken', 0),
            'leave_allocations': balance_data.get('leave_allocations', 0),
        }

    @http.route(['/my/leaves/create'], type='http', auth="user", website=True)
    def create_leave_form(self, **kwargs):
        """Display leave creation form"""
        values = self._prepare_create_leave_values()
        return request.render("etech_leave_portal.portal_create_leave", values)

    @http.route('/get_leave_details', type='json', auth='user', csrf=False)
    def get_leave_details(self, employee_id, **kw):
        """JSON endpoint to get leave balance for an employee"""
        empty = {'leave_balance': 0, 'leave_taken': 0, 'leave_allocations': 0}
        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        if not employee.exists() or employee not in self._get_allowed_employees(request.env.user):
            return empty
        return employee._get_portal_leave_balance()

    def _validate_leave_dates(self, start_date, end_date, employee_id, leave_id=None):
        """Validate leave dates and check for conflicts"""
        errors = []
        if start_date.date() > end_date.date():
            errors.append(_('The start date must be before the end date.'))
        domain = [
            ('date_from', '<', end_date),
            ('date_to', '>', start_date),
            ('employee_id', '=', employee_id),
            ('state', 'not in', ['cancel', 'refuse']),
        ]
        if leave_id:
            domain.append(('id', '!=', leave_id))

        overlapping_leaves = request.env['hr.leave'].sudo().search(domain)
        if overlapping_leaves:
            errors.append(_('You cannot set two leaves that overlap on the same day for the same employee.'))

        return errors

    def _parse_date_from_datetime_picker(self, date_string):
        """Parse date from datetime-picker format"""
        try:
            if not date_string:
                raise ValueError(_('Date is required'))
            if '-' in date_string:
                return datetime.strptime(date_string, '%Y-%m-%d')
            elif '/' in date_string:
                return datetime.strptime(date_string, '%d/%m/%Y')
            else:
                # Fallback
                return datetime.strptime(date_string, self.get_date_format())
        except (ValueError, TypeError) as e:
            raise ValueError(_('Invalid date format: %s. Please use YYYY-MM-DD format.') % date_string)

    def _prepare_leave_vals(self, post, employee):
        """Prepare values for leave creation"""
        start_date_str = post.get('start_date', '').strip()
        end_date_str = post.get('end_date', '').strip() if post.get('half_day') != 'on' else post.get(
            'start_date', ''
            ).strip()

        if not start_date_str:
            raise ValueError(_('Start date is required'))
        if not end_date_str:
            raise ValueError(_('End date is required'))

        start_date = self._parse_date_from_datetime_picker(start_date_str)
        is_half_day = post.get('half_day') == 'on'
        if is_half_day:
            end_date = start_date
        else:
            end_date = self._parse_date_from_datetime_picker(end_date_str)

        if start_date.date() > end_date.date():
            raise ValueError(_('The start date must be before the end date.'))
        start_date, end_date = self._calculate_working_hours(employee, start_date, end_date)
        vals = {
            'employee_id': employee.id,
            'holiday_status_id': int(post.get('leave_type')),
            'date_from': start_date,
            'request_date_from': start_date,
            'request_date_to': end_date if not is_half_day else start_date,
            'date_to': end_date if not is_half_day else start_date,
            'name': post.get('reason', ''),
            'reason': post.get('reason', '')
        }
        if is_half_day:
            period = post.get('period', 'am')
            vals.update(
                {
                    'request_unit_half': True,
                    'request_date_from_period': period,
                    'number_of_days': 0.5
                }
            )

        return vals, start_date, end_date

    def _calculate_working_hours(self, employee, start_date, end_date):
        """Calculate working hours based on employee's calendar"""
        resource_calendar_id = employee.resource_calendar_id
        if not resource_calendar_id:
            return start_date, end_date

        try:
            domain = [
                ('calendar_id', '=', resource_calendar_id.id),
                ('display_type', '=', False)
            ]
            attendances = request.env['resource.calendar.attendance'].sudo().read_group(
                domain,
                ['hour_from:min(hour_from)', 'hour_to:max(hour_to)', 'dayofweek'],
                ['dayofweek'],
                lazy=False
            )

            if not attendances:
                return start_date, end_date
            start_attendance = next(
                (att for att in attendances if int(att['dayofweek']) == start_date.weekday()),
                attendances[0]
            )
            end_attendance = next(
                (att for att in attendances if int(att['dayofweek']) == end_date.weekday()),
                attendances[-1]
            )
            hour_from = float_to_time(start_attendance['hour_from'])
            hour_to = float_to_time(end_attendance['hour_to'])
            tz = timezone(employee.tz or 'UTC')
            start_date = tz.localize(datetime.combine(start_date, hour_from)).astimezone(UTC).replace(tzinfo=None)
            end_date = tz.localize(datetime.combine(end_date, hour_to)).astimezone(UTC).replace(tzinfo=None)

            return start_date, end_date
        except Exception as e:
            return start_date, end_date

    def _handle_attachments(self, post, leave_id):
        """Handle file attachments"""
        file = request.httprequest.files.get('attachments')
        if file and file.filename:
            attachment = request.env['ir.attachment'].sudo().create(
                {
                    'name': file.filename,
                    'datas': base64.b64encode(file.read()),
                    'res_model': 'hr.leave',
                    'res_id': leave_id.id,
                }
            )
            leave_id.supported_attachment_ids = [(4, attachment.id)]

    @http.route(['/save/leave'], type='http', auth="user", website=True, methods=['POST'])
    def save_leave(self, **post):
        """Save leave request"""
        try:
            required_fields = [
                'emp_name',
                'leave_type',
                'start_date',
                'end_date',
                'reason'
            ]

            for field in required_fields:
                if not post.get(field):
                    if field == 'end_date' and post.get('half_day') == 'on':
                        continue
                    error_msg = _('Please fill all required fields.')
                    return self._show_form_with_error(error_msg)

            employee = request.env['hr.employee'].sudo().browse(int(post.get('emp_name')))
            if not employee.exists() or employee not in self._get_allowed_employees(request.env.user):
                error_msg = _('Invalid employee selected.')
                return self._show_form_with_error(error_msg)
            vals, start_date, end_date = self._prepare_leave_vals(post, employee)
            errors = self._validate_leave_dates(start_date, end_date, employee.id)
            if errors:
                error_msg = '\n'.join(errors)
                return self._show_form_with_error(error_msg)
            leave_id = request.env['hr.leave'].sudo().create(vals)
            self._handle_attachments(post, leave_id)
            user_id = request.env.user
            if employee.id != user_id.employee_id.id:
                return request.redirect('/my/leaves/team_leaves')
            else:
                return request.redirect('/my/leaves')

        except ValueError as e:
            return self._show_form_with_error(str(e))
        except Exception as e:
            error_message = _('An error occurred while creating the leave request: %s') % str(e)
            return self._show_form_with_error(error_message)

    def _show_form_with_error(self, error_message):
        """Show form with error message"""
        values = self._prepare_create_leave_values()
        values['error'] = error_message
        return request.render("etech_leave_portal.portal_create_leave", values)

    def get_date_format(self):
        """Get date format based on user preferences"""
        return '%Y-%m-%d'

    @http.route(['/my/leaves/edit/<int:leave_id>'], type='http', auth="user", website=True)
    def edit_leave_form(self, leave_id, **kwargs):
        """Display leave edit form"""
        values = self._prepare_edit_leave_values(leave_id)
        if 'error' in values:
            # Rediriger vers la page des congés avec message d'erreur
            return request.redirect('/my/leaves?error=' + values['error'])

        return request.render("etech_leave_portal.portal_edit_leave", values)

    @http.route(['/update/leave/<int:leave_id>'], type='http', auth="user", website=True, methods=['POST'])
    def update_leave(self, leave_id, **post):
        """Update leave request"""
        try:
            leave = request.env['hr.leave'].sudo().browse(leave_id)

            if not leave.exists():
                error_msg = _('Leave request not found.')
                return self._show_edit_form_with_error(leave_id, error_msg)
            user_id = request.env.user
            if leave.employee_id not in self._get_allowed_employees(user_id):
                error_msg = _('You are not allowed to edit this leave request.')
                return self._show_edit_form_with_error(leave_id, error_msg)
            if leave.state not in ['draft', 'confirm']:
                error_msg = _('You can only edit leave requests that are in draft or to approve state.')
                return self._show_edit_form_with_error(leave_id, error_msg)
            required_fields = [
                'emp_name',
                'leave_type',
                'start_date',
                'end_date',
                'reason'
            ]

            for field in required_fields:
                if not post.get(field):
                    if field == 'end_date' and post.get('half_day') == 'on':
                        continue
                    error_msg = _('Please fill all required fields.')
                    return self._show_edit_form_with_error(leave_id, error_msg)

            employee = request.env['hr.employee'].sudo().browse(int(post.get('emp_name')))
            if not employee.exists() or employee not in self._get_allowed_employees(user_id):
                error_msg = _('Invalid employee selected.')
                return self._show_edit_form_with_error(leave_id, error_msg)

            vals, start_date, end_date = self._prepare_leave_vals(post, employee)
            errors = self._validate_leave_dates(start_date, end_date, employee.id, leave_id=leave_id)
            if errors:
                error_msg = '\n'.join(errors)
                return self._show_edit_form_with_error(leave_id, error_msg)
            leave.write(vals)
            self._handle_attachments(post, leave)
            user_id = request.env.user
            success_message = _('Leave request updated successfully.')
            if employee.id != user_id.employee_id.id:
                return request.redirect('/my/leaves/team_leaves?success=' + success_message)
            else:
                return request.redirect('/my/leaves?success=' + success_message)

        except ValueError as e:
            return self._show_edit_form_with_error(leave_id, str(e))
        except Exception as e:
            error_message = _('An error occurred while updating the leave request: %s') % str(e)
            return self._show_edit_form_with_error(leave_id, error_message)

    def _show_edit_form_with_error(self, leave_id, error_message):
        """Show edit form with error message"""
        values = self._prepare_edit_leave_values(leave_id)
        if 'error' in values:
            return request.render("etech_leave_portal.portal_edit_leave", values)
        values['error'] = error_message
        return request.render("etech_leave_portal.portal_edit_leave", values)