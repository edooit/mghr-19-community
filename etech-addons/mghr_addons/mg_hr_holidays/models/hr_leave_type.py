from odoo import api, fields, models


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    weekend_consideration = fields.Boolean(
        default=False,
        help='Check this field to consider weekends when calculating leave duration.',
    )
