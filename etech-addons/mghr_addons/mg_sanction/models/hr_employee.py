from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    sanction_count = fields.Integer(
        string="Sanction",
        compute="_compute_get_sanction_count"
    )

    def _compute_get_sanction_count(self):
        self.sanction_count = self.env['hr.sanction'].search_count(
            [('employee_id', '=', self.id)]
        )

    def get_sanction_active_id(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.sanction',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
            'view_mode': 'list,form',
            'target': 'current',
            'name': 'sanction',
        }
