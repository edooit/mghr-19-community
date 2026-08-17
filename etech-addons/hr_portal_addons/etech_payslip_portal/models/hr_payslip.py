from odoo import _, models


class HrPayslip(models.Model):
    _name = 'hr.payslip'
    _inherit = ['hr.payslip', 'portal.mixin']

    def _compute_access_url(self):
        res = super(HrPayslip, self)._compute_access_url()
        for payslip in self:
            payslip.access_url = '/my/payslip/%s' % (payslip.id)
        return res

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % (_('Payslip'), self.registration_number or self.employee_id.name or self.name)
