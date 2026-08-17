from odoo import api, fields, models


class PayslipResume(models.Model):
    _name = "payslip.resume"
    _description = "HR Payslip Report"
    _order = 'start_date desc, employee_name'

    payslip_config_id = fields.Many2one(
        'hr.payslip.config',
        'Payslip Configuration',
        readonly=True,
        index=True,
    )
    payslip_reference = fields.Char(readonly=True)
    group = fields.Char(readonly=True)
    category = fields.Char(readonly=True)
    label = fields.Char(readonly=True)
    employee_name = fields.Char(readonly=True)
    job_position = fields.Char('Job Position', readonly=True)
    employee_id = fields.Many2one('hr.employee', readonly=True, index=True)
    registration_number = fields.Char(readonly=True)
    department_id = fields.Many2one('hr.department', readonly=True, index=True)
    parent_department_id = fields.Many2one('hr.department', readonly=True, index=True)
    gender = fields.Selection(
        [
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        readonly=True
    )
    cnaps_number = fields.Char(readonly=True)
    id_card_number = fields.Char(readonly=True)
    payslip_batch_name = fields.Char(readonly=True)
    start_date = fields.Date(readonly=True, index=True)
    end_date = fields.Date(readonly=True, index=True)

    payment_mode = fields.Char(readonly=True)
    payslip_state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('verify', 'Verify'),
            ('done', 'Done'),
            ('paid', 'Paid'),
            ('cancel', 'Cancel')
        ],
        'State',
        readonly=True,
        index=True,
    )
    payslip_run_id = fields.Many2one(
        'hr.payslip.run', string='Payslip Batch', readonly=True, index=True
    )
    bank_name = fields.Char(readonly=True)
    bank_code = fields.Char(readonly=True)
    branch_code = fields.Char(readonly=True)
    account_number = fields.Char(readonly=True)

    company_id = fields.Many2one('res.company', readonly=True, index=True)

    work_days = fields.Float()
    work_hours = fields.Float()
    net_salary = fields.Float()
    work_zone_id = fields.Many2one('hr.work.zone', index=True)
    work_location_id = fields.Many2one('hr.work.location', index=True)
    properties = fields.Properties(
        string='Dynamic Columns',
        definition='payslip_config_id.payslip_resume_properties_definition',
    )

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Hides certain fields from being sortable."""
        hidden_fields = [
            'group', 'employee_id', 'create_uid', 'create_date', 'payslip_config_id',
            'payslip_run_id', 'write_date', 'write_uid',
            'category', 'payslip_batch_name'
        ]
        fields_metadata = super(PayslipResume, self).fields_get(allfields, attributes)
        for field in hidden_fields:
            if field in fields_metadata:
                fields_metadata[field]['sortable'] = False
        return fields_metadata
