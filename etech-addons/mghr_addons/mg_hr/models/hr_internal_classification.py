from odoo import fields, models


class HrInternalClassification(models.Model):
    _name = 'hr.internal.classification'
    _description = 'Internal classification'

    name = fields.Char(required=True)
