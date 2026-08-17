from odoo import fields, models


class HrWorkLocationInherit(models.Model):
    _inherit = 'hr.work.location'

    zone_id = fields.Many2one(
        'hr.work.zone',
        'Work location zone'
    )
