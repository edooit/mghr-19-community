from collections import Counter

from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.tools.date_utils import get_timedelta


class AccrualPlan(models.Model):
    _inherit = 'hr.leave.accrual.plan'

    @api.constrains('level_ids')
    def _check_start_timedelta(self):
        """ Check that acrrual plan hasn't duplicate value in level start duration """
        for plan in self:
            level_start_durations = [get_timedelta(
                level.start_count,
                level.start_type) for level in plan.level_ids]

            if len(level_start_durations) != len(set(level_start_durations)):
                duplicate_durations = plan.get_duplicate_value(level_start_durations)

                result = {}
                for value in duplicate_durations:
                    result[value] = plan.get_levels_of_value(level_start_durations, value)

                raise ValidationError(plan.get_validator_message(result))

    def get_duplicate_value(self, list_values):
        return [item for item, count in Counter(list_values).items() if count > 1]

    def get_levels_of_value(self, list_values, value):
        return [i for i, x in enumerate(list_values, 1) if x == value]

    def _convert_relativedelta_to_string(self, duration):
        if duration.years:
            return str(duration.years) + _(" year(s)")
        elif duration.months:
            return str(duration.months) + _(" month(s)")
        elif duration.days:
            return str(duration.days) + _(" day(s)")
        return _("immediately")

    def get_validator_message(self, result):
        message = _("The number of days, months or years to start the"
                    " accumulation must be different for each level!\n")

        for key, value in result.items():
            message += ("\n " + self._convert_relativedelta_to_string(key)
                        + _(" appears ")
                        + str(len(value)) + _(" time (Level ")
                        + _(", Level ").join(map(str, value)) + ")")
        return message
