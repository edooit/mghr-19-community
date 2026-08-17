from odoo import fields, models, _


class HrContractIndex(models.Model):
    _name = 'hr.contract.index'
    _description = "HR Contract Index"
    _rec_name = 'index'

    index = fields.Integer()
    group_id = fields.Many2one('hr.contract.group')
