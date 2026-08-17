import logging
from datetime import datetime, date

import pytz

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

_logger = logging.getLogger(__name__)


class PlanningPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'planning_count' in counters:
            employee = self._planning_get_current_employee()
            if employee:
                domain = self._planning_get_domain(employee)
                values['planning_count'] = request.env['planning.slot'].sudo().search_count(domain)
        return values

    def _planning_get_current_employee(self):
        return request.env.user.employee_id

    def _planning_get_user_timezone(self):
        return request.env.user.tz or 'UTC'

    def _planning_convert_to_utc(self, datetime_str):
        try:
            user_tz = pytz.timezone(self._planning_get_user_timezone())
            fmt = '%Y-%m-%d %H:%M:%S' if len(datetime_str) == 19 else '%Y-%m-%d %H:%M'
            local_dt = datetime.strptime(datetime_str, fmt)
            local_dt = user_tz.localize(local_dt)
            utc_dt = local_dt.astimezone(pytz.UTC)
            return utc_dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            _logger.exception("Could not convert datetime '%s' to UTC.", datetime_str)
            return datetime_str

    def _planning_convert_from_utc(self, datetime_str):
        if not datetime_str:
            return None
        try:
            user_tz = pytz.timezone(self._planning_get_user_timezone())
            utc_dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            utc_dt = pytz.UTC.localize(utc_dt)
            local_dt = utc_dt.astimezone(user_tz)
            return local_dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            _logger.exception("Could not convert datetime '%s' from UTC.", datetime_str)
            return datetime_str

    def _planning_get_subordinates(self, employee):
        return request.env['hr.employee'].sudo().search([
            ('parent_id', '=', employee.id),
            ('id', '!=', employee.id),
        ])

    def _planning_get_domain(self, employee, subordinate_ids=None):
        if not employee:
            return []
        if subordinate_ids is None:
            subordinate_ids = self._planning_get_subordinates(employee).ids
        if subordinate_ids:
            return ['|', ('employee_id', '=', employee.id), ('employee_id', 'in', subordinate_ids)]
        return [('employee_id', '=', employee.id)]

    def _planning_can_create_slot(self, employee, subordinate_ids, target_employee):
        return target_employee.id == employee.id or target_employee.id in subordinate_ids

    def _planning_can_modify_slot(self, employee, subordinate_ids, slot):
        return slot.employee_id.id == employee.id or slot.employee_id.id in subordinate_ids

    @http.route('/my/planning', type='http', auth="user", website=True)
    def planning_portal(self, **kwargs):
        employee = self._planning_get_current_employee()
        if not employee:
            return request.redirect('/my')

        values = {
            'page_name': 'planning',
            'employee': employee,
            'is_manager': bool(self._planning_get_subordinates(employee)),
        }
        return request.render("etech_planning_portal.planning_portal_page", values)

    @http.route('/my/planning/data', type='json', auth="user", website=True, readonly=True)
    def get_planning_data(self, start_date, end_date, **kwargs):
        employee = self._planning_get_current_employee()
        if not employee:
            return {'error': 'Employee not found'}

        subordinate_ids = self._planning_get_subordinates(employee).ids
        domain = self._planning_get_domain(employee, subordinate_ids)
        domain += [
            ('start_datetime', '>=', start_date),
            ('end_datetime', '<=', end_date),
        ]

        slots = request.env['planning.slot'].sudo().search_read(
            domain=domain,
            fields=['id', 'name', 'start_datetime', 'end_datetime', 'employee_id', 'state'],
            order='start_datetime',
        )

        formatted_slots = [{
            'id': slot['id'],
            'name': slot['name'],
            'start_datetime': self._planning_convert_from_utc(
                slot['start_datetime'].strftime('%Y-%m-%d %H:%M:%S')) if slot['start_datetime'] else None,
            'end_datetime': self._planning_convert_from_utc(
                slot['end_datetime'].strftime('%Y-%m-%d %H:%M:%S')) if slot['end_datetime'] else None,
            'employee_id': slot['employee_id'][0] if slot['employee_id'] else False,
            'employee_name': slot['employee_id'][1] if slot['employee_id'] else '',
            'state': slot['state'],
        } for slot in slots]

        return {
            'slots': formatted_slots,
            'is_manager': bool(subordinate_ids),
            'current_employee_id': employee.id,
        }

    @http.route('/my/planning/employees', type='json', auth="user", website=True, readonly=True)
    def get_employees_data(self, **kwargs):
        employee = self._planning_get_current_employee()
        if not employee:
            return []

        subordinate_ids = self._planning_get_subordinates(employee).ids
        if subordinate_ids:
            domain = ['|', ('id', '=', employee.id), ('id', 'in', subordinate_ids)]
        else:
            domain = [('id', '=', employee.id)]

        return request.env['hr.employee'].sudo().search_read(
            domain=domain,
            fields=['id', 'name', 'registration_number', 'avatar_128'],
            order='name',
        )

    @http.route('/my/planning/slot/create', type='json', auth="user", website=True)
    def create_planning_slot(self, **kwargs):
        employee = self._planning_get_current_employee()
        if not employee:
            return {'success': False, 'error': 'Employee not found'}

        target_employee_id = kwargs.get('employee_id')
        if not target_employee_id:
            return {'success': False, 'error': 'Employee ID is required'}
        try:
            target_employee_id = int(target_employee_id)
        except (TypeError, ValueError):
            return {'success': False, 'error': 'Invalid employee ID'}

        target_employee = request.env['hr.employee'].sudo().browse(target_employee_id)
        if not target_employee.exists():
            return {'success': False, 'error': 'Target employee not found'}

        subordinate_ids = self._planning_get_subordinates(employee).ids
        if not self._planning_can_create_slot(employee, subordinate_ids, target_employee):
            return {'success': False, 'error': 'Access denied'}

        start_datetime = kwargs.get('start_datetime')
        end_datetime = kwargs.get('end_datetime')
        if not start_datetime or not end_datetime:
            return {'success': False, 'error': 'Start and end date are required'}

        start_utc = self._planning_convert_to_utc(start_datetime)
        end_utc = self._planning_convert_to_utc(end_datetime)
        try:
            start_dt = datetime.strptime(start_utc, '%Y-%m-%d %H:%M:%S')
            end_dt = datetime.strptime(end_utc, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return {'success': False, 'error': 'Invalid date format'}

        if start_dt.date() < date.today():
            return {'success': False, 'error': 'Cannot create slots in the past'}
        if end_dt <= start_dt:
            return {'success': False, 'error': 'End date must be after start date'}

        try:
            slot = request.env['planning.slot'].sudo().create({
                'start_datetime': start_utc,
                'end_datetime': end_utc,
                'employee_id': target_employee.id,
                'resource_id': target_employee.resource_id.id,
            })
            return {'success': True, 'slot_id': slot.id}
        except Exception as e:
            _logger.exception("Error creating planning slot.")
            return {'success': False, 'error': str(e)}

    @http.route('/my/planning/slot/update', type='json', auth="user", website=True)
    def update_planning_slot(self, slot_id, **kwargs):
        employee = self._planning_get_current_employee()
        if not employee:
            return {'success': False, 'error': 'Employee not found'}

        try:
            slot_id = int(slot_id)
        except (TypeError, ValueError):
            return {'success': False, 'error': 'Invalid slot ID'}

        slot = request.env['planning.slot'].sudo().browse(slot_id)
        if not slot.exists():
            return {'success': False, 'error': 'Slot not found'}

        subordinate_ids = self._planning_get_subordinates(employee).ids
        if not self._planning_can_modify_slot(employee, subordinate_ids, slot):
            return {'success': False, 'error': 'Access denied'}

        update_vals = {}
        start_utc = end_utc = None
        if kwargs.get('start_datetime'):
            start_utc = self._planning_convert_to_utc(kwargs['start_datetime'])
            update_vals['start_datetime'] = start_utc
        if kwargs.get('end_datetime'):
            end_utc = self._planning_convert_to_utc(kwargs['end_datetime'])
            update_vals['end_datetime'] = end_utc

        try:
            start_dt = datetime.strptime(start_utc, '%Y-%m-%d %H:%M:%S') if start_utc else slot.start_datetime
            end_dt = datetime.strptime(end_utc, '%Y-%m-%d %H:%M:%S') if end_utc else slot.end_datetime
        except ValueError:
            return {'success': False, 'error': 'Invalid date format'}

        if start_utc and start_dt.date() < date.today():
            return {'success': False, 'error': 'Cannot modify slots in the past'}
        if end_dt <= start_dt:
            return {'success': False, 'error': 'End date must be after start date'}

        try:
            slot.write(update_vals)
            return {'success': True}
        except Exception as e:
            _logger.exception("Error updating planning slot %s.", slot_id)
            return {'success': False, 'error': str(e)}

    @http.route('/my/planning/slot/delete', type='json', auth='user', website=True)
    def delete_planning_slot(self, slot_id):
        employee = self._planning_get_current_employee()
        if not employee:
            return {'success': False, 'error': 'Employee not found'}

        try:
            slot_id = int(slot_id)
        except (TypeError, ValueError):
            return {'success': False, 'error': 'Invalid slot ID'}

        slot = request.env['planning.slot'].sudo().browse(slot_id)
        if not slot.exists():
            return {'success': False, 'error': 'Slot not found'}

        subordinate_ids = self._planning_get_subordinates(employee).ids
        if not self._planning_can_modify_slot(employee, subordinate_ids, slot):
            return {'success': False, 'error': 'Access denied'}

        try:
            slot.unlink()
            return {'success': True}
        except Exception as e:
            _logger.exception("Error deleting planning slot %s.", slot_id)
            return {'success': False, 'error': str(e)}
