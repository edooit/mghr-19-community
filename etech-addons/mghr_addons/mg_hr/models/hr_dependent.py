from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models


class HrDependent(models.Model):
    _name = 'hr.dependent'
    _description = 'Employee dependent'

    employee_id = fields.Many2one('hr.employee')
    registration_number = fields.Char(
        related='employee_id.registration_number',
        store='True'
    )
    firstname = fields.Char(required=True)
    lastname = fields.Char(required=True)
    birthdate = fields.Date(required=True)
    age = fields.Float('Age num', compute='_compute_age', store='True')
    age_txt = fields.Char('Age', compute='_compute_age', store='True')
    is_handicap = fields.Boolean(default=False)
    cnaps = fields.Boolean(default=False)
    gender = fields.Selection(
        [
            ('male', _('male')),
            ('female', _('female')),
            ('other', _('Other'))
        ],
        default='male'
    )

    @api.depends('birthdate')
    def _compute_age(self):
        """
        Compute children's age and format it
        """
        for rec in self:
            if rec.birthdate:
                today = date.today()
                diff = relativedelta(today, rec.birthdate)
                years = _('%(years)d year(s)') % {'years': diff.years} if diff.years else ''
                months = _('%(months)d month(s)') % {'months': diff.months} if diff.months else ''
                days = _('%(days)d day(s)') % {'days': diff.days} if diff.days else ''

                rec.age = int(diff.years + (diff.months / 12))
                rec.age_txt = ' '.join(filter(None, [years, months, days]))
            else:
                rec.age = 0
                rec.age_txt = ''
