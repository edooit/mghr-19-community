from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PayslipResumeColumn(models.Model):
    _name = "payslip.resume.column"
    _description = "Hr Payslip Report dynamic column"
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char(required=True, help="Technical key used to store this column's value.")
    hr_salary_rule_ids = fields.Many2many(
        'hr.salary.rule',
        column1='payslip_resume_column_id',
        column2='hr_salary_rule_id',
        string='Salary Rules',
        required=True
    )
    appears_in_payslip_resume = fields.Boolean(default=False)

    @api.constrains('code')
    def _check_code_unique(self):
        for column in self:
            duplicate = self.search(
                [('id', '!=', column.id), ('code', '=ilike', column.code)]
            )
            if duplicate:
                raise ValidationError(
                    _("The code \"%(code)s\" is already used by another column.", code=column.code)
                )
