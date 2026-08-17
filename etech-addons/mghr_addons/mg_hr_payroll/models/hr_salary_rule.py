from odoo import fields, models


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    is_rate = fields.Boolean(default=False)
    rate_id = fields.Many2one(
        'hr.salary.rule',
        domain=[('is_rate', '=', True)]
    )
