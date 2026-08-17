import logging

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.tools.misc import format_date

_logger = logging.getLogger(__name__)


class HrPayslipConfig(models.Model):
    _name = 'hr.payslip.config'
    _description = 'HR Payslip Configuration'
    _order = 'date_from desc'

    name = fields.Char(string='Name', required=True, default='Payslip State')
    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)
    payslip_resume_ids = fields.One2many(
        'payslip.resume',
        'payslip_config_id',
        string='Payslip Resumes'
    )
    payslip_resume_count = fields.Integer(
        string='Payslip Resume Count',
        compute='_compute_payslip_resume_count'
    )
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company
    )
    department_id = fields.Many2one('hr.department')
    work_zone_id = fields.Many2one('hr.work.zone')
    work_location_id = fields.Many2one(
        'hr.work.location',
        domain='[("zone_id", "=", "work_zone_id")]'
    )
    payslip_resume_properties_definition = fields.PropertiesDefinition(
        compute='_compute_payslip_resume_properties_definition',
    )

    _date_to_after_date_from = models.Constraint(
        'CHECK (date_to >= date_from)',
        "The end date must be on or after the start date.",
    )

    @api.depends('date_from', 'date_to')
    def _compute_display_name(self):
        for config in self:
            if config.date_from and config.date_to:
                config.display_name = _(
                    'Payslip State from %(start)s to %(end)s',
                    start=format_date(self.env, config.date_from),
                    end=format_date(self.env, config.date_to),
                )
            else:
                config.display_name = config.name

    def _compute_payslip_resume_properties_definition(self):
        columns = self.env['payslip.resume.column'].search(
            [('appears_in_payslip_resume', '=', True)]
        )
        definition = [
            {
                'name': column.code.lower(),
                'string': column.name,
                'type': 'float',
            }
            for column in columns
        ]
        for config in self:
            config.payslip_resume_properties_definition = definition

    @api.onchange('date_from')
    def _onchange_date_from(self):
        if self.date_from:
            self.date_to = self.date_from + relativedelta(day=31)

    @api.depends('payslip_resume_ids')
    def _compute_payslip_resume_count(self):
        for record in self:
            record.payslip_resume_count = len(record.payslip_resume_ids)

    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        if self.date_from and self.date_to and self.date_to < self.date_from:
            self.date_to = self.date_from

    def mg_generate_payslip_resume(self):
        """Generate the payroll report with the configured columns."""
        self.ensure_one()
        self.payslip_resume_ids.unlink()

        # Define domain for filtering payslips
        domain = [
            ('date_from', '>=', self.date_from),
            ('date_to', '<=', self.date_to),
            ('company_id', '=', self.company_id.id)
        ]
        if self.work_location_id:
            domain.append(('work_location_id', '=', self.work_location_id.id))
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        if self.work_zone_id:
            domain.append(('work_zone_id', '=', self.work_zone_id.id))

        payslips = self.env['hr.payslip'].sudo().search(domain)
        if not payslips:
            _logger.info(
                "Payslip config %s: no payslip matched the filters, nothing generated.",
                self.id,
            )
            return

        # Map each dynamic column code to the salary rule codes that feed it,
        # computed once for the whole batch instead of once per payslip.
        columns = self.env['payslip.resume.column'].search(
            [('appears_in_payslip_resume', '=', True)]
        )
        column_rule_codes = {
            column.code.lower(): set(column.hr_salary_rule_ids.mapped('code'))
            for column in columns
        }

        # Create payslip resume records
        new_payslip_data = []
        for payslip in payslips:
            worked_days = payslip.mapped('worked_days_line_ids')
            leave_days = sum(
                line.number_of_days for line in worked_days.filtered(
                    lambda l: l.work_entry_type_id.is_leave
                )
            )
            number_of_days = 30 - leave_days if leave_days else 30
            number_of_hours = (173.33 * number_of_days) / 30

            values = {
                'payslip_config_id': self.id,
                'group': payslip.employee_id.group_id.name or '',
                'category': payslip.employee_id.category_id.name or '',
                'label': ','.join(payslip.employee_id.category_ids.mapped('name')) or False,
                'payslip_reference': payslip.name,
                'employee_id': payslip.employee_id.id,
                'registration_number': payslip.employee_id.registration_number or '',
                'department_id': payslip.employee_id.department_id.id if payslip.employee_id else False,
                'parent_department_id': (
                    payslip.employee_id.department_id.parent_id.id
                    if payslip.employee_id and payslip.employee_id.department_id and payslip.employee_id.department_id.parent_id
                    else False
                ),
                'gender': payslip.employee_id.sex or '',
                'cnaps_number': payslip.employee_id.cnaps_number or '',
                'id_card_number': payslip.employee_id.identification_id or '',
                'payslip_batch_name': payslip.payslip_run_id.name if payslip.payslip_run_id else '',
                'payslip_run_id': payslip.payslip_run_id.id if payslip.payslip_run_id else False,
                'bank_name': payslip.employee_id.primary_bank_account_id.bank_id.name or '',
                'bank_code': payslip.employee_id.primary_bank_account_id.bank_id.bic or '',
                'branch_code': payslip.employee_id.primary_bank_account_id.agency_code or '',
                'account_number': payslip.employee_id.primary_bank_account_id.acc_number or '',
                'company_id': payslip.company_id.id,
                'employee_name': payslip.employee_id.name or '',
                'job_position': (
                    payslip.employee_id.job_id.name
                    if payslip.employee_id and payslip.employee_id.job_id
                    else ''
                ),
                'start_date': payslip.date_from,
                'end_date': payslip.date_to,
                'work_days': number_of_days,
                'work_hours': number_of_hours,
                'net_salary': sum(
                    line.total for line in payslip.line_ids.filtered(lambda l: l.code == 'SNET')
                ),
                'payment_mode': (
                    payslip.employee_id.payslip_payment_mode_id.name
                    if payslip.employee_id.payslip_payment_mode_id
                    else ''
                ),
                'payslip_state': payslip.state,
                'work_zone_id': payslip.work_zone_id.id if payslip.work_zone_id else False,
                'work_location_id': payslip.work_location_id.id if payslip.work_location_id else False,
                'properties': {
                    code: sum(
                        line.total for line in payslip.line_ids if line.code in rule_codes
                    )
                    for code, rule_codes in column_rule_codes.items()
                },
            }

            new_payslip_data.append(values)

        self.env['payslip.resume'].create(new_payslip_data)
        _logger.info(
            "Payslip config %s: generated %d pay state line(s).",
            self.id, len(new_payslip_data),
        )

    def view_payslip_resume(self):
        self.ensure_one()
        tree_view_id = self.env.ref(
            'mg_generate_pay_state.detailed_payslip_resume_view_list2'
        ).id
        return {
            'name': self.display_name,
            'res_model': 'payslip.resume',
            'view_mode': 'list,form,pivot,graph',
            'views': [
                (tree_view_id, 'list'),
                (False, 'form'),
                (False, 'pivot'),
                (False, 'graph'),
            ],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('payslip_config_id', '=', self.id)]
        }