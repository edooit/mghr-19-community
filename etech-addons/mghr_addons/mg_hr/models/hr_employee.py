import logging
from datetime import date, datetime, time
from dateutil import relativedelta
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    seniority = fields.Char(
        compute='_compute_seniority',
        groups="hr.group_hr_user"
    )
    cnaps_number = fields.Char(groups="hr.group_hr_user")
    years = fields.Integer(groups="hr.group_hr_user")
    months = fields.Integer(groups="hr.group_hr_user")
    days = fields.Integer(groups="hr.group_hr_user")
    hiring_date = fields.Date(
        string="Hiring date",
        groups="hr.group_hr_user",
        default=lambda self: fields.Datetime.now()
    )
    cin_validity_date = fields.Date(groups="hr.group_hr_user")
    cin_date_of_issue = fields.Date(groups="hr.group_hr_user")
    cin_place_of_issue = fields.Char(groups="hr.group_hr_user")
    cin_duplicate_date = fields.Date(groups="hr.group_hr_user")
    cin_duplicate_place = fields.Char(groups="hr.group_hr_user")

    passport_validity_date = fields.Date(groups="hr.group_hr_user")
    internal_classification = fields.Many2one(
        comodel_name="hr.internal.classification",
        groups="hr.group_hr_user"
    )
    dependent_ids = fields.One2many(
        'hr.dependent',
        'employee_id',
        'Dependent lines',
        groups="hr.group_hr_user"
    )
    children = fields.Integer(
        compute='_compute_children_number',
        store=True,
        groups="hr.group_hr_user"
    )

    job_code = fields.Char(related="job_id.job_code")
    work_zone_id = fields.Many2one(
        'hr.work.zone', string="Work location zone",
        related='work_location_id.zone_id',
        store=True,
        readonly=True,
        groups="hr.group_hr_user"
    )
    spouse_gender = fields.Selection(
        [
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ]
    )

    def _compute_seniority(self):
        for rec in self:
            rec.seniority = ''
            if not rec.hiring_date:
                continue

            date_start = datetime.combine(self.hiring_date, time.min)
            date_end = datetime.combine(self.departure_date or date.today(), time.min)
            diff = relativedelta.relativedelta(date_end, date_start)
            if diff.years:
                rec.years = diff.years
            if diff.months:
                rec.months = diff.months

            rec.seniority = rec._get_formatted_seniority(diff)

    def _get_formatted_seniority(self, diff):
        parts = []
        if diff.years:
            years = _("year") if diff.years == 1 else _("years")
            parts.append(f"{diff.years} {years}")

        if diff.months:
            months = _("month") if diff.months == 1 else _("months")
            if parts:
                parts.append(_("and"))
            parts.append(f"{diff.months} {months}")

        if diff.days:
            days = _("day") if diff.days == 1 else _("days")
            if parts:
                parts.append(_("and"))
            parts.append(f"{diff.days} {days}")

        if not parts:
            return f"0 {_('day')}"

        return ' '.join(parts)

    @api.depends('dependent_ids')
    def _compute_children_number(self):
        """
        Compute children number
        :return:
        """
        for rec in self:
            rec.children = rec.get_employees_dependent_age(date.today())

    def get_employees_dependent_age(self, date_from):
        self.ensure_one()
        dt_from = datetime.strptime(str(date_from), "%Y-%m-%d")
        dependent_count = 0
        for dependent_id in self.dependent_ids:
            birthdate = dependent_id.birthdate
            dt_birthdate = datetime.strptime(str(birthdate), "%Y-%m-%d")
            diff = relativedelta.relativedelta(date_from, birthdate)
            years = int(diff.years)
            if (years <= 21 and dt_from.month != dt_birthdate.month
                    or years < 21 and dt_from.month == dt_birthdate.month
                    or dependent_id.is_handicap):
                dependent_count += 1
        return dependent_count

    def get_seniority_in_months(self):
        self.ensure_one()
        if not self.hiring_date:
            return 0

        end_date = self.departure_date or date.today()
        diff = relativedelta.relativedelta(end_date, self.hiring_date)
        total_months = (diff.years * 12) + diff.months
        return total_months

    def get_seniority_in_years_decimal(self):
        self.ensure_one()
        if not self.hiring_date:
            return 0.0

        end_date = self.departure_date or date.today()
        diff = relativedelta.relativedelta(end_date, self.hiring_date)
        years_decimal = diff.years + (diff.months / 12.0)
        return round(years_decimal, 2)

    def get_seniority_details(self):
        self.ensure_one()
        if not self.hiring_date:
            return {
                'years': 0,
                'months': 0,
                'total_months': 0,
                'years_decimal': 0.0
            }

        end_date = self.departure_date or date.today()
        diff = relativedelta.relativedelta(end_date, self.hiring_date)
        total_months = (diff.years * 12) + diff.months
        years_decimal = diff.years + (diff.months / 12.0)

        return {
            'years': diff.years,
            'months': diff.months,
            'total_months': total_months,
            'years_decimal': round(years_decimal, 2)
        }
