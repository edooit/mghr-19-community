from odoo import fields, models


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    title = fields.Char()
    show_classification = fields.Boolean(
        string="Show classification",
        default=False
    )
