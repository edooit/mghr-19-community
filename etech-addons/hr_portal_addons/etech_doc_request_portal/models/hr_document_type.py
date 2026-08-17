from odoo import fields, models


class HrDocumentType(models.Model):
    _name = 'hr.document.type'
    _description = 'HR Document Type'
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
