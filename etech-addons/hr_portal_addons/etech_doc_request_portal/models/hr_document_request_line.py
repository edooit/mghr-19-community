import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HrDocumentRequestLine(models.Model):
    _name = 'hr.document.request.line'
    _description = 'HR Document Request Line'
    _order = 'request_id desc, id'

    _request_document_type_uniq = models.Constraint(
        'unique(request_id, document_type_id)',
        'This document type was already requested in this request.',
    )

    request_id = fields.Many2one('hr.document.request', required=True, ondelete='cascade')
    document_type_id = fields.Many2one('hr.document.type', string='Document', required=True)
    delivery_mode = fields.Selection(
        [('physical', 'Physique'), ('electronic', 'Électronique')], required=True,
    )
    state = fields.Selection(
        [('draft', 'Brouillon'), ('in_progress', 'En cours'), ('done', 'Traité')],
        default='draft', required=True,
    )
    document = fields.Binary(string='File', attachment=True)
    document_filename = fields.Char()
    pickup_date = fields.Datetime(string='Pickup date')

    employee_id = fields.Many2one('hr.employee', related='request_id.employee_id', store=True)
    company_id = fields.Many2one('res.company', related='request_id.company_id', store=True)
    request_date = fields.Datetime(related='request_id.request_date', store=True)

    display_name = fields.Char(compute='_compute_display_name')

    @api.depends('request_id.name', 'document_type_id.name')
    def _compute_display_name(self):
        for line in self:
            line.display_name = f'{line.request_id.name} - {line.document_type_id.name}'

    def action_start(self):
        self.filtered(lambda line: line.state == 'draft').write({'state': 'in_progress'})

    def action_done(self):
        requests_before = {req.id: req.state for req in self.mapped('request_id')}
        self.filtered(lambda line: line.state == 'in_progress').write({'state': 'done'})
        for req in self.mapped('request_id'):
            if req.state == 'done' and requests_before.get(req.id) != 'done' and not req.employee_notified:
                req._notify_employee_done()

    @api.constrains('state', 'delivery_mode', 'pickup_date', 'document')
    def _check_delivery_requirements(self):
        for line in self:
            if line.state != 'done':
                continue
            if line.delivery_mode == 'electronic' and not line.document:
                raise ValidationError(
                    _('Cannot mark "%s" as done: no electronic document has been uploaded.', line.display_name)
                )
            if line.delivery_mode == 'physical' and not line.pickup_date:
                raise ValidationError(
                    _('Cannot mark "%s" as done: no pickup date has been set.', line.display_name)
                )
