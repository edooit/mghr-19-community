from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    night_start = fields.Float(
        default=22.0, help="Night hours start time (eg: 22.0 for 10 p.m.)"
    )
    night_end = fields.Float(
        default=5.0, help="End of night hours (eg 5.0 for 5h)"
    )
