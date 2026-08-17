from odoo import fields, models


class HrPayrollStructure(models.Model):
    _inherit = "hr.payroll.structure"

    show_leave_allocation = fields.Boolean(
        string="Show leave allocation",
        default=False,
        store='True'
    )
    show_work100 = fields.Boolean(string="Show WORK100", default=False)
