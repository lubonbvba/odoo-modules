# -*- coding: utf-8 -*-

from openerp import models, fields, api

class lubon_hr_employee(models.Model):
	_name = "hr.employee"
 	_inherit = ["hr.employee",'pad.common']
 	user_pad_data = fields.Char()
 	user_pad = fields.Char(pad_content_field='user_pad_data')




# from openerp.tools.translate import _
# from openerp.osv import fields, osv

# class lubon_hr_employee(osv.osv):
#     _name = "hr.employee"
#     _inherit = ["hr.employee",'pad.common']
#     _columns = {
#         'user_pad_data': fields.char('User PAD data'),
#         'user_pad': fields.char('User PAD', pad_content_field='user_pad_data')
#     }
