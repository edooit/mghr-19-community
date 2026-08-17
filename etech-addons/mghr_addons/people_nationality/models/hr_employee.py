from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    nationality_id = fields.Many2one(
        'people.nationality',
        groups="hr.group_hr_user"
    )
