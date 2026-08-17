from collections import OrderedDict

from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

DELIVERY_MODES = ('physical', 'electronic')
_ITEMS_PER_PAGE = 10


class PortalDocsRequest(CustomerPortal):

    def _docreq_get_own_requests_domain(self, employee):
        return [('employee_id', '=', employee.id)]

    def _docreq_get_searchbar_filters(self):
        return OrderedDict([
            ('all', {'label': _('Toutes'), 'domain': []}),
            ('draft', {'label': _('Brouillon'), 'domain': [('state', '=', 'draft')]}),
            ('in_progress', {'label': _('En cours'), 'domain': [('state', '=', 'in_progress')]}),
            ('done', {'label': _('Traité'), 'domain': [('state', '=', 'done')]}),
        ])

    def _docreq_get_searchbar_groupby(self):
        return OrderedDict([
            ('none', {'label': _('Aucun')}),
            ('state', {'label': _('Statut')}),
            ('year', {'label': _('Année')}),
        ])

    def _docreq_get_group_label(self, doc_request, groupby):
        if groupby == 'state':
            return dict(doc_request._fields['state'].selection).get(doc_request.state)
        if groupby == 'year':
            return str(doc_request.request_date.year) if doc_request.request_date else _('Sans date')
        return _('Toutes')

    @http.route(['/my/documents', '/my/documents/page/<int:page>'], type='http', auth="user", website=True)
    def documents_home(self, page=1, filterby=None, groupby=None, error=None, **kw):
        values = self._prepare_portal_layout_values()
        employee = values.get('employee_id') or request.env.user.employee_id
        DocumentType = request.env['hr.document.type'].sudo()
        DocumentRequest = request.env['hr.document.request'].sudo()

        document_types = DocumentType.search([])
        own_domain = self._docreq_get_own_requests_domain(employee)

        searchbar_filters = self._docreq_get_searchbar_filters()
        searchbar_groupby = self._docreq_get_searchbar_groupby()
        if filterby not in searchbar_filters:
            filterby = 'all'
        if groupby not in searchbar_groupby:
            groupby = 'none'

        domain = own_domain + searchbar_filters[filterby]['domain']
        filtered_count = DocumentRequest.search_count(domain)

        state_counts = dict(DocumentRequest._read_group(own_domain, groupby=['state'], aggregates=['__count']))

        pager = portal_pager(
            url='/my/documents',
            url_args={'filterby': filterby, 'groupby': groupby},
            total=filtered_count,
            page=page,
            step=_ITEMS_PER_PAGE,
        )
        requests = DocumentRequest.search(
            domain, order='request_date desc', limit=_ITEMS_PER_PAGE, offset=pager['offset'],
        )

        grouped_requests = []
        if groupby != 'none':
            buckets = OrderedDict()
            for doc_request in requests:
                buckets.setdefault(self._docreq_get_group_label(doc_request, groupby), []).append(doc_request)
            grouped_requests = list(buckets.items())

        values.update({
            'employee': employee,
            'page_name': 'docs_request',
            'document_types': document_types,
            'requests': requests,
            'grouped_requests': grouped_requests,
            'has_grouping': groupby != 'none',
            'stats_total': sum(state_counts.values()),
            'stats_in_progress': state_counts.get('in_progress', 0),
            'stats_done': state_counts.get('done', 0),
            'default_url': '/my/documents',
            'pager': pager,
            'searchbar_filters': searchbar_filters,
            'searchbar_groupby': searchbar_groupby,
            'filterby': filterby,
            'groupby': groupby,
            'error': error,
        })
        return request.render('etech_doc_request_portal.portal_docs_request', values)

    @http.route(['/my/documents/new'], type='http', auth="user", methods=['POST'], website=True)
    def documents_new(self, **post):
        employee = request.env.user.employee_id
        document_type_ids = [int(doc_id) for doc_id in request.httprequest.form.getlist('document_type_id')]
        valid_type_ids = set(request.env['hr.document.type'].sudo().search([
            ('id', 'in', document_type_ids),
        ]).ids)

        line_vals = []
        for type_id in document_type_ids:
            if type_id not in valid_type_ids:
                continue
            delivery_mode = post.get(f'delivery_mode_{type_id}')
            if delivery_mode not in DELIVERY_MODES:
                continue
            line_vals.append((0, 0, {
                'document_type_id': type_id,
                'delivery_mode': delivery_mode,
            }))

        if not line_vals:
            return self.documents_home(error=_('Please select at least one document with a valid delivery mode.'))

        request.env['hr.document.request'].sudo().create({
            'employee_id': employee.id,
            'company_id': employee.company_id.id,
            'line_ids': line_vals,
        })
        return request.redirect('/my/documents')

    def _docreq_get_own_request(self, request_id):
        doc_request = request.env['hr.document.request'].sudo().browse(request_id)
        if not doc_request.exists() or doc_request.employee_id.user_id != request.env.user:
            raise MissingError(_('This request does not exist.'))
        return doc_request

    @http.route(['/my/documents/<int:request_id>'], type='http', auth="user", website=True)
    def documents_detail(self, request_id, **kw):
        values = self._prepare_portal_layout_values()
        try:
            doc_request = self._docreq_get_own_request(request_id)
        except (AccessError, MissingError):
            return request.redirect('/my/documents')

        values.update({
            'employee': values.get('employee_id') or request.env.user.employee_id,
            'page_name': 'docs_request',
            'doc_request': doc_request,
        })
        return request.render('etech_doc_request_portal.portal_docs_request_detail', values)

    @http.route(['/my/documents/<int:request_id>/line/<int:line_id>/download'], type='http', auth="user")
    def documents_download(self, request_id, line_id, **kw):
        try:
            doc_request = self._docreq_get_own_request(request_id)
        except (AccessError, MissingError):
            return request.redirect('/my/documents')

        line = doc_request.line_ids.filtered(lambda l: l.id == line_id)
        if not line or line.state != 'done' or line.delivery_mode != 'electronic' or not line.document:
            return request.redirect(f'/my/documents/{request_id}')

        stream = request.env['ir.binary']._get_stream_from(
            line, 'document', filename_field='document_filename',
        )
        return stream.get_response(as_attachment=True)
