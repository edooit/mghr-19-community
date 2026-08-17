from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    notice = fields.Float(
        compute="_compute_get_notice"
    )
    category_id = fields.Many2one(
        'hr.contract.category',
        string="Professional category",
        required=True
    )
    group_id = fields.Many2one(
        'hr.contract.group',
        related="category_id.group_id",
        store=True
    )

    index_id = fields.Many2one(
        'hr.contract.index',
        string="Index",
        domain="[('group_id', '=', group_id)]"
    )

    @api.depends('hiring_date')
    def _compute_get_notice(self):
        notice = 0
        if self.hiring_date:
            days = (fields.Datetime.now().date() - self.hiring_date).days

            day_ranges = [
                (0, 8),
                (8, 90),
                (90, 365),
                (365, 1095),
                (1095, 1825),
                (1825, float('inf'))
            ]

            group_notices = {
                'group1': [1, 3, 8, 10, 10, 30],
                'group2': [2, 8, 15, 30, 30, 45],
                'group3': [3, 15, 30, 45, 45, 60],
                'group4': [4, 30, 45, 75, 75, 90],
                'group5': [5, 30, 90, 120, 120, 180]
            }

            group_id = self.group_id.id
            group_code = None
            for code, group in group_notices.items():
                if group_id == self.env.ref(f'mg_hr_category.{code}').id:
                    group_code = code
                    break

            if group_code:
                for i, (start, end) in enumerate(day_ranges):
                    if start <= days < end:
                        notice = group_notices[group_code][i]
                        if start == 1095:
                            notice += 2 * (days // 365)
                        break
        self.notice = notice
