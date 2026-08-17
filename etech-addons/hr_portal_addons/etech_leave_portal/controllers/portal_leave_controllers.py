import logging
from collections import OrderedDict
from operator import itemgetter
from datetime import datetime
from odoo import _, http, SUPERUSER_ID
from odoo.http import request
from odoo.osv.expression import OR
from odoo.tools import groupby as groupbyelem
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

_logger = logging.getLogger(__name__)


class UnifiedLeavePortal(CustomerPortal):

    def _is_leave_manager(self, user_id):
        """Whether this user is the portal-side (first-level) approver of at
        least one employee — i.e. their hierarchical manager (parent_id).
        This is deliberately not hr.employee.leave_manager_id: that native
        field is the backend/HR second-level approver, who may not have any
        need to act from the portal at all."""
        return bool(request.env['hr.employee'].sudo().search_count(
            [('parent_id.user_id', '=', user_id.id)]
        ))

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        user_id = request.env.user
        employee_id = user_id.employee_id

        if not employee_id:
            return values
        domain_my_leaves = [('employee_id', '=', employee_id.id)]
        values['leave_count'] = request.env['hr.leave'].sudo().search_count(domain_my_leaves)
        domain_team_leaves = [
            ('state', '=', 'confirm'),
            ('employee_id.parent_id.user_id', '=', user_id.id),
        ]
        values['team_leave_count'] = request.env['hr.leave'].sudo().search_count(domain_team_leaves)

        return values

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        user_id = request.env.user
        if not user_id.employee_id:
            return values
        # Cheap check only: the leave balance itself is only needed on the
        # leave portal pages, so it's computed there (see portal_unified_leaves)
        # instead of on every single portal page load.
        values['is_leave_manager'] = self._is_leave_manager(user_id)
        return values

    def _get_searchbar_inputs(self):
        return {
            'all': {'input': 'all', 'label': _('Search in All')},
            'employee': {'input': 'employee', 'label': _('Search in Employee')},
            'registration_number': {'input': 'registration_number', 'label': _('Search in Registration Number')},
            'leave_type': {'input': 'leave_type', 'label': _('Search in Leave Type')},
            'reason': {'input': 'reason', 'label': _('Search in Reason')},
        }

    def _get_search_domain(self, search_in, search):
        search_domain = []
        if search_in in ('employee', 'all'):
            search_domain = OR([search_domain, [('employee_id.name', 'ilike', search)]])
        if search_in in ('registration_number', 'all'):
            search_domain = OR([search_domain, [('employee_id.registration_number', 'ilike', search)]])
        if search_in in ('leave_type', 'all'):
            search_domain = OR([search_domain, [('holiday_status_id.name', 'ilike', search)]])
        if search_in in ('reason', 'all'):
            search_domain = OR([search_domain, [('name', 'ilike', search)]])
        return search_domain

    def _get_searchbar_sortings_leave(self):
        return {
            'date_from': {'label': _('Start Date'), 'order': 'date_from desc', 'sequence': 1},
            'date_to': {'label': _('End Date'), 'order': 'date_to desc', 'sequence': 2},
            'leave_type': {'label': _('Leave Type'), 'order': 'holiday_status_id', 'sequence': 3},
            'status': {'label': _('Status'), 'order': 'state', 'sequence': 4},
            'employee': {'label': _('Employee'), 'order': 'employee_id', 'sequence': 5},
        }

    def _get_searchbar_groupby_leave(self):
        values = {
            'none': {'input': 'none', 'label': _('None'), 'order': 1},
            'leave_type': {'input': 'leave_type', 'label': _('Leave Type'), 'order': 2},
            'status': {'input': 'status', 'label': _('Status'), 'order': 3},
            'employee': {'input': 'employee', 'label': _('Employee'), 'order': 4},
            'department': {'input': 'department', 'label': _('Department'), 'order': 5},
        }
        return dict(sorted(values.items(), key=lambda item: item[1]["order"]))

    def _get_groupby_mapping(self):
        return {
            'leave_type': 'holiday_status_id',
            'status': 'state',
            'employee': 'employee_id',
            'department': 'department_id',
        }

    def _get_order(self, order, groupby):
        groupby_mapping = self._get_groupby_mapping()
        field_name = groupby_mapping.get(groupby, '')
        if not field_name:
            return order
        return '%s, %s' % (field_name, order)

    def _get_leave_domain(self, view_type='my_leaves', filters=None):
        """Get domain based on view type"""
        user_id = request.env.user
        employee_id = user_id.employee_id
        filters = filters or {}

        if not employee_id:
            return []

        if view_type == 'team_leaves':
            if not self._is_leave_manager(user_id):
                return [('id', '=', False)]
            base_domain = [('employee_id.parent_id.user_id', '=', user_id.id)]
        else:
            base_domain = [('employee_id', '=', employee_id.id)]
        state_filter = filters.get('state')
        if state_filter and state_filter != 'all':
            base_domain.append(('state', '=', state_filter))

        return base_domain

    def _get_dashboard_stats(self, view_type):
        """Get dashboard statistics based on view type (single grouped query)"""
        user_id = request.env.user
        employee_id = user_id.employee_id

        if not employee_id:
            return {}

        if view_type == 'team_leaves':
            if not self._is_leave_manager(user_id):
                return {}
            domain = [('employee_id.parent_id.user_id', '=', user_id.id)]
            state_to_key = {
                'confirm': 'to_approve_count',
                'validate': 'approved_count',
                'validate1': 'pending_count',
                'refuse': 'refused_count',
            }
            stats = {key: 0 for key in state_to_key.values()}
            total_key = 'total_team_leaves'
        else:
            domain = [('employee_id', '=', employee_id.id)]
            state_to_key = {
                'draft': 'draft_count',
                'confirm': 'to_approve_count',
                'validate': 'approved_count',
                'validate1': 'pending_count',
                'refuse': 'refused_count',
            }
            stats = {key: 0 for key in state_to_key.values()}
            total_key = 'total_my_leaves'

        stats[total_key] = 0
        for state, count in request.env['hr.leave'].sudo()._read_group(
            domain, groupby=['state'], aggregates=['__count']
        ):
            stats[total_key] += count
            if state in state_to_key:
                stats[state_to_key[state]] = count

        return stats

    def _prepare_calendar_data(self, leaves):
        """Prepare data for calendar view"""
        events = []
        for leave in leaves:
            try:
                event_data = {
                    'id': leave.id,
                    'title': f"{leave.employee_id.name or ''} - {leave.holiday_status_id.name}",
                    'start': leave.date_from.strftime('%Y-%m-%dT%H:%M:%S'),
                    'end': leave.date_to.strftime('%Y-%m-%dT%H:%M:%S'),
                    'color': self._get_leave_color(leave.state),
                    'textColor': '#ffffff',
                    'extendedProps': {
                        'employee': leave.employee_id.name,
                        'type': leave.holiday_status_id.name,
                        'status': leave.state,
                        'duration': leave.duration_display,
                        'description': leave.reason or '',
                    }
                }
                events.append(event_data)

            except Exception:
                # Keep building the calendar for the other leaves, but log
                # this one instead of silently dropping it — a swallowed
                # exception here previously made a leave "disappear" from
                # the calendar with no way to tell why.
                _logger.exception("Could not build calendar event for leave %s", leave.id)
        return events

    def _get_leave_color(self, state):
        """Get color based on leave status (kept in sync with the JS
        _decorateEvent fallback colors in leave_portal_unified.js)"""
        colors = {
            'draft': '#6c757d',  # Gray
            'confirm': '#0dcaf0',  # Info blue
            'validate1': '#f0ad4e',  # Warning yellow
            'validate': '#198754',  # Success green
            'refuse': '#dc3545',  # Danger red
        }
        return colors.get(state, '#6c757d')

    def _get_searchbar_filters(self, view_type):
        """Get search filters based on view type"""
        if view_type == 'team_leaves':
            return {
                'all': {'label': _('All'), 'domain': []},
                'confirm': {'label': _('To Approve'), 'domain': [('state', '=', 'confirm')]},
                'validate1': {'label': _('To Validate'), 'domain': [('state', '=', 'validate1')]},
                'validate': {'label': _('Approved'), 'domain': [('state', '=', 'validate')]},
                'refuse': {'label': _('Refused'), 'domain': [('state', '=', 'refuse')]},
            }
        else:
            return {
                'all': {'label': _('All'), 'domain': []},
                'draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
                'confirm': {'label': _('To Approve'), 'domain': [('state', '=', 'confirm')]},
                'validate1': {'label': _('To Validate'), 'domain': [('state', '=', 'validate1')]},
                'validate': {'label': _('Approved'), 'domain': [('state', '=', 'validate')]},
                'refuse': {'label': _('Refused'), 'domain': [('state', '=', 'refuse')]},
            }

    @http.route(
        [
            '/my/leaves',
            '/my/leaves/page/<int:page>',
            '/my/leaves/<string:view_type>',
            '/my/leaves/<string:view_type>/page/<int:page>'
        ], type='http', auth="user", website=True
    )
    def portal_unified_leaves(
            self, page=1, view_type='my_leaves', view_display='cards',
            sortby=None, filterby=None, search=None, search_in='all',
            groupby=None, **kw
    ):
        """Main unified leaves portal route"""
        values = self._prepare_portal_layout_values()
        Leave = request.env['hr.leave']
        _items_per_page = 20

        if view_type not in ['my_leaves', 'team_leaves']:
            view_type = 'my_leaves'

        if view_type == 'team_leaves' and not values.get('is_leave_manager'):
            view_type = 'my_leaves'  # Fallback to my_leaves if not manager

        searchbar_sortings = self._get_searchbar_sortings_leave()
        searchbar_inputs = self._get_searchbar_inputs()
        searchbar_filters = self._get_searchbar_filters(view_type)
        searchbar_groupby = self._get_searchbar_groupby_leave()
        sortby = sortby or 'date_from'
        filterby = filterby or 'all'
        groupby = groupby or 'none'
        view_display = view_display or 'cards'
        domain = self._get_leave_domain(view_type, {'state': filterby if filterby != 'all' else None})
        if search and search_in:
            domain += self._get_search_domain(search_in, search)
        leave_count = Leave.sudo().search_count(domain)
        pager = portal_pager(
            url=f"/my/leaves/{view_type}",
            url_args={
                'view_display': view_display,
                'search_in': search_in, 'search': search,
                'groupby': groupby, 'filterby': filterby, 'sortby': sortby
            },
            total=leave_count,
            page=page,
            step=_items_per_page
        )
        order = searchbar_sortings[sortby]['order']
        order = self._get_order(order, groupby)

        # Prepare data based on view display
        if view_display == 'calendar':
            # The calendar has no pager of its own and must show every
            # matching leave regardless of date, not just the current
            # pager page (a leave further down the sort order than
            # _items_per_page would otherwise silently never appear on it).
            leaves = Leave.sudo().search(domain, order=order)
            values.update({'calendar_data': self._prepare_calendar_data(leaves)})
        else:
            leaves = Leave.sudo().search(domain, order=order, limit=_items_per_page, offset=pager['offset'])
            groupby_mapping = self._get_groupby_mapping()
            group_field = groupby_mapping.get(groupby)

            if group_field and groupby != 'none':
                sorted_leaves = leaves.sorted(key=itemgetter(group_field))
                grouped_data = []
                for key, group_leaves in groupbyelem(sorted_leaves, itemgetter(group_field)):
                    grouped_data.append((key, list(group_leaves)))
                values.update({'grouped_leaves': grouped_data})
            else:
                grouped_leaves = [('All Leaves', leaves)]
                values.update({'grouped_leaves': grouped_leaves})

        # Get dashboard statistics
        dashboard_stats = self._get_dashboard_stats(view_type)
        values.update(dashboard_stats)
        # Leave balance is only displayed on this page (balance modal), so it
        # is computed here rather than on every portal page.
        values.update(request.env.user.employee_id._get_portal_leave_balance())
        values['team_to_approve_count'] = (
            request.env['hr.leave'].sudo().search_count([
                ('state', '=', 'confirm'),
                ('employee_id.parent_id.user_id', '=', request.env.user.id),
            ]) if values.get('is_leave_manager') else 0
        )
        default_url = f'/my/leaves/{view_type}'

        # Update template values
        values.update(
            {
                'leaves': leaves,
                'page_name': 'leaves',
                'pager': pager,
                'view_type': view_type,
                'view_display': view_display,
                'search_in': search_in,
                'search': search,
                'sortby': sortby,
                'groupby': groupby,
                'searchbar_inputs': searchbar_inputs,
                'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
                'filterby': filterby,
                'searchbar_sortings': searchbar_sortings,
                'searchbar_groupby': searchbar_groupby,
                'current_date': datetime.now().strftime('%d/%m/%y'),
                'default_url': default_url,
            }
        )

        template = "etech_leave_portal.portal_unified_leaves"
        return request.render(template, values)

    @http.route(['/my/leave/details/<int:leave_id>'], type='http', auth="user", website=True)
    def portal_leave_details(self, leave_id, **kw):
        """Leave details page"""
        values = self._prepare_portal_layout_values()
        leave = request.env['hr.leave'].sudo().browse(leave_id)

        # Check access rights
        user_id = request.env.user
        employee_id = user_id.employee_id
        is_own_leave = bool(employee_id) and leave.employee_id == employee_id
        is_leave_manager_of_employee = leave.employee_id.parent_id.user_id == user_id

        if not leave.exists() or not (is_own_leave or is_leave_manager_of_employee):
            return request.redirect('/my/leaves')

        values.update(
            {
                'leave': leave,
                'page_name': 'leave_details',
                'is_own_leave': is_own_leave,
                'can_approve': is_leave_manager_of_employee,
            }
        )

        return request.render("etech_leave_portal.portal_leave_details", values)

    # Approval routes (for team leaves)
    @http.route(['/confirm/<int:leave_id>'], type='http', auth="user", website=True)
    def confirm_leave_request(self, leave_id, **kw):
        """Approve a leave request"""
        user_id = request.env.user
        leave = request.env['hr.leave'].sudo().browse(leave_id)

        if leave.exists() and leave.employee_id.parent_id.user_id == user_id:
            leave.action_approve()

        return request.redirect('/my/leaves/team_leaves')

    @http.route(['/refuse/<int:leave_id>'], type='http', auth="user", website=True)
    def refuse_leave_request(self, leave_id, **kw):
        """Refuse a leave request"""
        user_id = request.env.user
        leave = request.env['hr.leave'].sudo().browse(leave_id)

        if leave.exists() and leave.employee_id.parent_id.user_id == user_id:
            leave.action_refuse()

        return request.redirect('/my/leaves/team_leaves')

    @http.route(['/edit/leave/<int:leave_id>'], type='http', auth="user", website=True)
    def edit_leave_request(self, leave_id, **kw):
        """Redirect to leave edit form"""
        return request.redirect(f'/my/leaves/edit/{leave_id}')

    @http.route(['/leave/cancel/<int:leave_id>'], type='http', auth="user", website=True)
    def cancel_leave_request(self, leave_id, **kw):
        """Cancel a leave request"""
        user_id = request.env.user
        leave = request.env['hr.leave'].sudo().browse(leave_id)
        employee_id = user_id.employee_id

        # Check if user can cancel this leave (only their own leaves in draft/confirm state)
        if (leave.exists() and
                leave.employee_id == employee_id and
                leave.state in ['draft', 'confirm']):
            # hr.leave.action_cancel() just opens the backend "cancel" wizard
            # (hr.holidays.cancel.leave) — it doesn't do anything by itself here,
            # and that wizard only allows cancelling leaves already in
            # validate1/validate/refuse state anyway. For a draft/to-approve
            # leave the correct action is simply to delete it.
            # unlink() is run as the superuser: hr.leave.unlink() cascades to
            # archiving the linked ir.attachment/documents.document records
            # (when the Documents app is installed), and documents_document.write()
            # unconditionally blocks archiving for portal/share users
            # (env.user.share) regardless of sudo() — sudo() bypasses ACL
            # checks but doesn't change which user env.user resolves to.
            leave.with_user(SUPERUSER_ID).unlink()

        return request.redirect('/my/leaves')
