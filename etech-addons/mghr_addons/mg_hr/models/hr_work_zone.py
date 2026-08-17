from odoo import _, api, fields, models


class HrWorkZone(models.Model):
    _name = 'hr.work.zone'
    _description = 'Hr work location zone'

    name = fields.Char(
        string="Work zone",
        required=True
    )
