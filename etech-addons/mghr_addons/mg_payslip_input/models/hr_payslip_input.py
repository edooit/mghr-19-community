from odoo import api, fields, models


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company.id
    )
    number = fields.Char()
    is_imported = fields.Boolean(default=False)
    employee_id = fields.Many2one(
        'hr.employee',
        domain="[('registration_number', '!=', False)]"
    )
    date = fields.Date('Date From')
    date_to = fields.Date('Date to')
    payslip_id = fields.Many2one(
        'hr.payslip',
        string='Pay Slip',
        required=False,
        ondelete='cascade',
        index=True
    )

    input_type_id = fields.Many2one(
        'hr.payslip.input.type',
        string='Type',
        required=True,
        domain="[]"
        )

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res._set_employee()
        return res

    def _set_employee(self):
        for rec in self:
            emp_obj = self.env['hr.employee']
            emp_id = emp_obj.search(
                [
                    ('registration_number', '=', rec.number)
                ], limit=1
            )
            rec.write({'employee_id': emp_id.id})

    @api.onchange('employee_id')
    def _onchange_employee(self):
        registration_number = self.employee_id.registration_number
        self.number = registration_number

    def import_payslip_input(self):
        for rec in self:
            if not rec.is_imported and not rec.payslip_id:
                search_criteria = [
                    ('employee_id', '=', rec.employee_id.id),
                    ('date_from', '=', rec.date),
                    ('date_to', '=', rec.date_to),
                    ('company_id', '=', rec.company_id.id)
                ]
                payslip = self.env['hr.payslip'].search(search_criteria, limit=1)
                if payslip:
                    rec.write(
                        {
                            'payslip_id': payslip.id,
                            'is_imported': True
                        }
                    )

