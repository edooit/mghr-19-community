# -*- coding: utf-8 -*-

from odoo import models, fields, api


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def check(self, mode, values=None):
        if self.env.user.has_groups('base.group_portal'):
            return True
        return super().check(mode, values)
