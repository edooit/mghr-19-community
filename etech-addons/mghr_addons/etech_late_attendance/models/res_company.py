from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    minutes_late = fields.Float(string="Minute late")
