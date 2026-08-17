from collections import OrderedDict
from dateutil.relativedelta import relativedelta

from odoo import fields, http, _
from odoo.http import request
from odoo.tools import date_utils
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

_ITEMS_PER_PAGE = 30


class AttendancePortal(CustomerPortal):

    def _get_employee_ids(self, employee):
        """The employee's own id, plus their direct reports if they manage
        anyone — a manager should still see their own attendance here, not
        only their team's."""
        if not employee:
            return []
        subordinates = request.env['hr.employee'].sudo().search([('parent_id', '=', employee.id)])
        return (employee | subordinates).ids

    def _get_searchbar_input(self):
        return {
            'all': {'input': 'all', 'label': _('Search in All')},
            'reg.number': {'input': 'number', 'label': _('Search in Re. Number')},
            'employee': {'input': 'employee_name', 'label': _('Search in Employee')},
            'check_in': {'input': 'check_in', 'label': _('Search in Check In')},
            'check_out': {'input': 'check_out', 'label': _('Search in Check Out')},
        }

    def _get_searchbar_groupby(self):
        return {
            'none': {'input': 'none', 'label': _('None')},
            'employee_id': {'input': 'employee_id', 'label': _('Employee')},
            'registration_number': {'input': 'registration_number', 'label': _('Registration Number')},
            'department_id': {'input': 'department_id', 'label': _('Department')},
            'state': {'input': 'state', 'label': _('Status')},
        }

    def _get_date_filters(self):
        today = fields.Date.today()
        quarter_start, quarter_end = date_utils.get_quarter(today)
        last_week = today + relativedelta(weeks=-1)
        last_month = today + relativedelta(months=-1)
        last_year = today + relativedelta(years=-1)
        return {
            'all': {'label': _('All'), 'domain': []},
            'today': {'label': _('Today'), 'domain': [('date', '=', today)]},
            'week': {
                'label': _('This week'),
                'domain': [('date', '>=', date_utils.start_of(today, 'week')),
                           ('date', '<=', date_utils.end_of(today, 'week'))],
            },
            'month': {
                'label': _('This month'),
                'domain': [('date', '>=', date_utils.start_of(today, 'month')),
                           ('date', '<=', date_utils.end_of(today, 'month'))],
            },
            'year': {
                'label': _('This year'),
                'domain': [('date', '>=', date_utils.start_of(today, 'year')),
                           ('date', '<=', date_utils.end_of(today, 'year'))],
            },
            'quarter': {
                'label': _('This Quarter'),
                'domain': [('date', '>=', quarter_start), ('date', '<=', quarter_end)],
            },
            'last_week': {
                'label': _('Last week'),
                'domain': [('date', '>=', date_utils.start_of(last_week, 'week')),
                           ('date', '<=', date_utils.end_of(last_week, 'week'))],
            },
            'last_month': {
                'label': _('Last month'),
                'domain': [('date', '>=', date_utils.start_of(last_month, 'month')),
                           ('date', '<=', date_utils.end_of(last_month, 'month'))],
            },
            'last_year': {
                'label': _('Last year'),
                'domain': [('date', '>=', date_utils.start_of(last_year, 'year')),
                           ('date', '<=', date_utils.end_of(last_year, 'year'))],
            },
        }

    def _get_search_domain(self, search_in, search):
        if search_in == 'employee_name':
            return [('employee_id.name', 'ilike', search)]
        if search_in == 'number':
            return [('employee_id.registration_number', 'ilike', search)]
        if search_in == 'check_in':
            return [('check_in', 'ilike', search)]
        if search_in == 'check_out':
            return [('check_out', 'ilike', search)]
        return ['|', '|', ('check_in', 'ilike', search), ('check_out', 'ilike', search), ('worked_hours', 'ilike', search)]

    def _get_state_label(self, state):
        return {'late': _('Late'), 'on_time': _('On Time')}.get(state, _('Unknown'))

    def _get_group_label(self, record, groupby):
        if groupby == 'employee_id':
            return '%s (%s)' % (record.employee_id.name or _('Unknown'),
                                 record.employee_id.registration_number or _('No Registration Number'))
        if groupby == 'registration_number':
            return record.employee_id.registration_number or _('No Registration Number')
        if groupby == 'department_id':
            return record.employee_id.department_id.name or _('No Department')
        if groupby == 'state':
            return self._get_state_label(record.state)
        return _('Ungrouped')

    @http.route(['/my/attendance', '/my/attendance/page/<int:page>'], type='http', auth="user", website=True)
    def list_method(
            self, page=1, sortby=None, filterby=None, search=None, search_in='all', groupby='employee_id', **kw
            ):
        values = self._prepare_portal_layout_values()
        employee = request.env.user.employee_id
        employee_ids = self._get_employee_ids(employee)

        searchbar_inputs = self._get_searchbar_input()
        searchbar_groupby = self._get_searchbar_groupby()
        searchbar_filters = self._get_date_filters()

        if filterby not in searchbar_filters:
            filterby = 'all'
        if groupby not in searchbar_groupby:
            groupby = 'employee_id'
        search_in = search_in or 'all'

        domain = [('employee_id', 'in', employee_ids)] + searchbar_filters[filterby]['domain']
        if search and search_in:
            domain += self._get_search_domain(search_in, search)

        Attendance = request.env['hr.attendance'].sudo()

        # Stats reflect the whole filtered set (not just the current pager
        # page), computed with two aggregate queries instead of looping over
        # every attendance record — this used to fetch and iterate the
        # *entire* unpaginated result set in Python (and again in QWeb) just
        # to count "late"/"on time" rows.
        total_count = Attendance.search_count(domain)
        state_rows = Attendance._read_group(domain, groupby=['state'], aggregates=['__count'])
        state_counts = dict(state_rows)
        [(total_hours,)] = Attendance._read_group(domain, aggregates=['worked_hours:sum']) or [(0,)]

        pager = portal_pager(
            url='/my/attendance',
            url_args={
                'filterby': filterby, 'search_in': search_in, 'search': search,
                'groupby': groupby, 'sortby': sortby,
            },
            total=total_count,
            page=page,
            step=_ITEMS_PER_PAGE,
        )
        records = Attendance.search(domain, order='check_in desc', limit=_ITEMS_PER_PAGE, offset=pager['offset'])

        grouped_records = []
        if groupby != 'none':
            buckets = OrderedDict()
            for record in records:
                buckets.setdefault(self._get_group_label(record, groupby), []).append(record)
            grouped_records = list(buckets.items())

        values.update(
            {
                'records': records,
                'grouped_records': grouped_records,
                'has_grouping': groupby != 'none',
                'total_count': total_count,
                'on_time_count': state_counts.get('on_time', 0),
                'late_count': state_counts.get('late', 0),
                'total_hours': total_hours or 0,
                'page_name': 'attendance',
                'default_url': '/my/attendance',
                'pager': pager,
                'search_in': search_in,
                'search': search,
                'sortby': sortby,
                'searchbar_inputs': searchbar_inputs,
                'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
                'searchbar_groupby': searchbar_groupby,
                'filterby': filterby,
                'groupby': groupby,
            }
        )
        return request.render('etech_attendance_portal.attendance_list_view', values)
