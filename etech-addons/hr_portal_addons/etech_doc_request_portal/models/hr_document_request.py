import logging

from odoo import api, fields, models, _
from odoo.tools import format_datetime

_logger = logging.getLogger(__name__)


class HrDocumentRequest(models.Model):
    _name = 'hr.document.request'
    _description = 'HR Document Request'
    _order = 'request_date desc, id desc'

    name = fields.Char(required=True, readonly=True, copy=False, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', required=True, default=lambda self: self.env.user.employee_id)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    request_date = fields.Datetime(required=True, default=fields.Datetime.now)
    line_ids = fields.One2many('hr.document.request.line', 'request_id')
    state = fields.Selection(
        [('draft', 'Brouillon'), ('in_progress', 'En cours'), ('done', 'Traité')],
        compute='_compute_state', store=True,
    )
    employee_notified = fields.Boolean(copy=False)

    @api.depends('line_ids.state')
    def _compute_state(self):
        for request in self:
            states = request.line_ids.mapped('state')
            if not states:
                request.state = 'draft'
            elif all(state == 'done' for state in states):
                request.state = 'done'
            elif all(state == 'draft' for state in states):
                request.state = 'draft'
            else:
                request.state = 'in_progress'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.document.request') or _('New')
        requests = super().create(vals_list)
        for request in requests:
            if request.line_ids:
                request._notify_hr_new_request()
        return requests

    def _get_action_link(self):
        self.ensure_one()
        base_url = self.get_base_url()
        return f'{base_url}/odoo/hr.document.request/{self.id}'

    def _notify_hr_new_request(self):
        self.ensure_one()
        recipients = self.company_id.email_docs.mapped('work_email')
        recipients = [email for email in recipients if email]
        if not recipients:
            _logger.warning(
                "New document request %s from %s could not be notified: "
                "no HR recipient configured (email_docs) for company %s.",
                self.name, self.employee_id.name, self.company_id.name,
            )
            return
        body_html = _(
            '<p>%(employee)s just submitted a new document request (%(reference)s) '
            'for %(count)s document(s).</p><p><a href="%(link)s">View the request</a></p>',
            employee=self.employee_id.name, reference=self.name,
            count=len(self.line_ids), link=self._get_action_link(),
        )
        mail_values = {
            'subject': _('New document request: %s', self.name),
            'body_html': body_html,
            'email_to': ', '.join(recipients),
            'reply_to': self.employee_id.work_email or False,
        }
        mail = self.env['mail.mail'].sudo().create(mail_values)
        try:
            mail.send()
        except Exception:
            _logger.exception("Failed to send HR notification email for document request %s.", self.name)

    def _notify_employee_done(self):
        self.ensure_one()
        employee = self.employee_id
        tz = employee.tz or self.env.user.tz
        lines_html = []
        for line in self.line_ids:
            if line.delivery_mode == 'electronic':
                lines_html.append(_('%s: available for download on the portal.', line.document_type_id.name))
            else:
                pickup = format_datetime(self.env, line.pickup_date, tz=tz) if line.pickup_date else ''
                lines_html.append(_('%(doc)s: to collect on %(date)s.', doc=line.document_type_id.name, date=pickup))
        base_url = self.get_base_url()
        body_html = _(
            '<p>Your document request %(reference)s has been processed.</p>'
            '<ul><li>%(lines)s</li></ul>'
            '<p><a href="%(link)s">View my request</a></p>',
            reference=self.name, lines='</li><li>'.join(lines_html),
            link=f'{base_url}/my/documents/{self.id}',
        )
        mail_values = {
            'subject': _('Your document request %s has been processed', self.name),
            'body_html': body_html,
            'email_to': employee.work_email,
        }
        mail = self.env['mail.mail'].sudo().create(mail_values)
        try:
            mail.send()
            self.employee_notified = True
        except Exception:
            _logger.exception("Failed to send completion notification email for document request %s.", self.name)
