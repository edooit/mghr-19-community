from odoo import fields, models


class HrSanctionType(models.Model):
    _name = 'hr.sanction.type'
    _description = 'HR Sanction type'

    name = fields.Char(required=True, translate=True)
    type = fields.Selection(
        [
            ('caution', 'Warning'),
            ('layoff', 'Layoff')
        ],
        default='caution'
    )
