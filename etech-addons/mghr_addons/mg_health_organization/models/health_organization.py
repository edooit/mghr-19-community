from odoo import fields, models


class MedicalFund(models.Model):
    _name = 'health.organization'
    _description = 'Health organization'
    _rec_name = 'name'

    code = fields.Char()
    name = fields.Char()
    work_location_id = fields.Many2one(
        'hr.work.location',
        domain=lambda self: [
            ('company_id', '=', self.env.company.id)
        ]
    )
    work_zone_id = fields.Many2one(
        'hr.work.zone',
        related='work_location_id.zone_id',
        store=True
    )

    employer_rate = fields.Float()
    employee_rate = fields.Float()
    is_capped = fields.Boolean(default=False)
