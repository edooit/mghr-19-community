from odoo import fields, models, _


class HrContractCategory(models.Model):
    _name = 'hr.contract.category'
    _description = 'HR Contract category'

    name = fields.Char()
    group_id = fields.Many2one('hr.contract.group')
    description = fields.Text()
    is_manager = fields.Boolean(default=False)
