from odoo import fields, models, _


class HrContractGroup(models.Model):
    _name = 'hr.contract.group'
    _description = 'Hr Contract Group'

    name = fields.Char(
        required=True,
        translate=True
    )
    month = fields.Float(
        string="Duration",
        required=True
    )
    index_ids = fields.One2many(
        'hr.contract.index',
        'group_id',
        string="Indexes"
    )
    index = fields.Char()
