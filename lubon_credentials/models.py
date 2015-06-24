# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from openerp.http import request

# class lubon_partners(models.Model):
#     _name = 'lubon_partners.lubon_partners'

#     name = fields.Char()
# -*- coding: utf-8 -*-
#from openerp import fields, models

class Partner(models.Model):
        _inherit = 'res.partner'
        credential_ids=fields.One2many('lubon_credentials.credentials','partner_id',string='credentials')
	masterkey=fields.Char()


class Users(models.Model):
        _inherit = 'res.users'
	pin=fields.Char()




class lubon_qlan_credentials(models.Model):
	_name='lubon_credentials.credentials'
	_rec_name = 'description'

	description = fields.Char(string="Description", required=True)
        user = fields.Char(string="User")
        password = fields.Char(string="Password", type='password')
	partner_id = fields.Many2one('res.partner',  ondelete='set null', string="Partner", index=True)
	
	@api.one
	def show_password(self):
	    raise exceptions.ValidationError(self.password)
	    return True


	def _get_ipaddress(self, cr, uid, context=None):
        	return request.httprequest.environ['REMOTE_ADDR'] 
