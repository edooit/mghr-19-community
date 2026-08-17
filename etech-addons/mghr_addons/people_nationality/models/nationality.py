from odoo import fields, models


class PeopleNationality(models.Model):
    _name = 'people.nationality'
    _description = 'People nationality'

    name = fields.Char()
