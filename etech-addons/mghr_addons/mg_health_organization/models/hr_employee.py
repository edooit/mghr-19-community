from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    health_organization_id = fields.Many2one(
        'health.organization',
        tracking=True,
        groups="hr.group_hr_user"
    )
