from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


def get_date_format(self):
    """ This function get date format depending on the lang used on website from cookies """
    lang = request.httprequest.cookies.get('frontend_lang')
    if lang == 'fr_FR':
        return "%d/%m/%Y"
    else:
        return "%m/%d/%Y"

CustomerPortal.get_date_format = get_date_format


class HrPortalHome(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        # sudo: several hr.employee fields shown on the portal home (seniority,
        # hiring_date, ...) are restricted to hr.group_hr_user and would raise
        # an AccessError for a portal user reading their own record otherwise.
        employee_id = request.env.user.employee_id.sudo()
        values['employee_id'] = employee_id
        return values