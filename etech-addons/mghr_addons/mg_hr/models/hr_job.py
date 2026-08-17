from odoo import fields, models


class HrJobInherit(models.Model):
    _inherit = 'hr.job'

    job_code = fields.Char()
