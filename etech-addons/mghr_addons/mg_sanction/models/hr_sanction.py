from odoo import fields, models


class HrSanction(models.Model):
    _name = 'hr.sanction'
    _description = 'HR Sanction'

    name = fields.Char(required=True)
    motif = fields.Text(required=True)
    type_id = fields.Many2one(
        comodel_name="hr.sanction.type",
        string="Type",
        required=True,
        default=lambda self: self.env.ref(
            'mg_sanction.sanction_information'
            '').id)
    delivery_date = fields.Date(
        required=True,
        default=fields.Date.context_today
    )
    end_date = fields.Date(required=True)
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        related="employee_id.company_id",
        store=True
    )
    department_id = fields.Many2one(
        comodel_name="hr.department",
        string="Service",
        related="employee_id.department_id",
        store=True
    )
    department_parent_id = fields.Many2one(
        comodel_name="hr.department",
        string="Parent department",
        related="employee_id.department_id.parent_id",
        store=True
    )
