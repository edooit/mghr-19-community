from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        domain = args + ['|', ('registration_number', operator, name), ('name', operator, name)]
        employees = self.search(domain, limit=limit)
        result = [
            (employee.id,
             f"{f'[{employee.registration_number}] ' if employee.registration_number else ''}{employee.name}")
            for employee in employees
        ]
        return result