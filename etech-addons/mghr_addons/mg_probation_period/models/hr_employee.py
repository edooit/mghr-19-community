from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

# (start field, end field) per trial period, most recently signed last
_TRIAL_PERIOD_FIELDS = (
    (1, 'trial_period_1_start', 'trial_period_1_end'),
    (2, 'trial_period_2_start', 'trial_period_2_end'),
)
_REMINDER_DAYS_BEFORE = (14, 7)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    trial_period_1_start = fields.Date(string="1ère période d'essai - Début")
    trial_period_1_end = fields.Date(string="1ère période d'essai - Fin")
    trial_period_2_start = fields.Date(string="2ème période d'essai - Début")
    trial_period_2_end = fields.Date(string="2ème période d'essai - Fin")

    @api.constrains('trial_period_1_start', 'trial_period_1_end', 'trial_period_2_start', 'trial_period_2_end')
    def _check_trial_period_dates(self):
        for employee in self:
            if employee.trial_period_1_start and employee.trial_period_1_end \
                    and employee.trial_period_1_end < employee.trial_period_1_start:
                raise ValidationError(_('The end date of the 1st trial period must be after its start date.'))
            if employee.trial_period_2_start and employee.trial_period_2_end \
                    and employee.trial_period_2_end < employee.trial_period_2_start:
                raise ValidationError(_('The end date of the 2nd trial period must be after its start date.'))

    @api.model
    def _cron_notify_trial_period_ending(self):
        today = fields.Date.today()
        for period_number, start_field, end_field in _TRIAL_PERIOD_FIELDS:
            ordinal = _('1st') if period_number == 1 else _('2nd')
            for days_before in _REMINDER_DAYS_BEFORE:
                target_date = today + relativedelta(days=days_before)
                employees = self.search([
                    (start_field, '!=', False),
                    (end_field, '=', target_date),
                ])
                for employee in employees:
                    employee.with_context(mail_activity_quick_update=True).activity_schedule(
                        'mail.mail_activity_data_todo', employee[end_field],
                        _("The %(ordinal)s trial period of %(name)s ends in %(days)s days.",
                          ordinal=ordinal, name=employee.name, days=days_before),
                        user_id=employee.hr_responsible_id.id or self.env.uid)
        return True
