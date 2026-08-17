from odoo import _, models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    is_imported = fields.Boolean(
        string="Importation",
        default=False,
        related='input_line_ids.is_imported'
    )

    def _get_payslip_input(self):
        payslip_input = self.env['hr.payslip.input']
        for rec in self:
            number = rec.employee_id.registration_number
            search_criteria = [
                ('number', '=', number),
                ('date', '=', rec.date_from),
                ('date_to', '=', rec.date_to),
                ('company_id', '=', rec.company_id.id),
                ('is_imported', '=', False)
            ]
            payslip_inputs = payslip_input.search(search_criteria)
            payslip_inputs.write({'payslip_id': rec.id})

    def import_payslip_input(self):
        """Import payslip input values from employee"""
        self._get_payslip_input()
        self._update_is_imported_values()

    def _update_is_imported_values(self):
        for rec in self:
            rec.input_line_ids.write({'is_imported': True})

    @api.model
    def create(self, vals):
        """Override the create method to import payslip input after creation"""
        payslip = super(HrPayslip, self).create(vals)
        payslip.import_payslip_input()
        payslip._update_is_imported_values()
        return payslip
