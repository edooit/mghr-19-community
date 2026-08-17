from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class PayslipCustomerPortal(CustomerPortal):

    @http.route(['/my/payslip', '/my/payslip/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_loan(self, page=1, filterby=None, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        Payslip = request.env['hr.payslip'].sudo()
        base_domain = [
            ('employee_id.user_id', '=', request.env.user.id),
            ('state', 'in', ['done', 'paid']),
        ]

        # only fetch the field needed to list the available years, scoped to
        # the current employee (avoids loading every payslip in the company)
        years = sorted({
            payslip.date_from.year
            for payslip in Payslip.search_fetch(base_domain, ['date_from'])
            if payslip.date_from
        }, reverse=True)

        searchbar_filters = {'all': {'label': _('All'), 'domain': []}}
        for year in years:
            searchbar_filters[str(year)] = {
                'label': str(year),
                'domain': ['&', ('date_from', '>=', '{}-01-01'.format(year)),
                                ('date_to', '<=', '{}-12-31'.format(year))],
            }

        if not filterby or filterby not in searchbar_filters:
            filterby = 'all'
        domain = base_domain + searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        # count for pager
        payslip_count = Payslip.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/payslip",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'filterby': filterby, 'sortby': sortby},
            total=payslip_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        payslip = Payslip.search(domain, order='date_from desc', limit=self._items_per_page, offset=pager['offset'])
        request.session['my_payslip_history'] = payslip.ids[:100]

        values.update(
            {
                'date': date_begin,
                'payslips': payslip.sudo(),
                'page_name': 'payslip',
                'pager': pager,
                'default_url': '/my/payslip',
                'searchbar_filters': searchbar_filters,
                'sortby': sortby,
                'filterby': filterby,
            }
        )
        return request.render("etech_payslip_portal.portal_my_payslip", values)

    @http.route(['/my/payslip/<int:order_id>'], type='http', auth="public", website=True)
    def portal_payslip_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            payslip_sudo = self._document_check_access('hr.payslip', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        return self._show_report(
            model=payslip_sudo, report_type=report_type,
            report_ref='hr_payroll.action_report_payslip', download=download
            )
