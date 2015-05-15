# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from openerp.http import request

# class lubon_partners(models.Model):
#     _name = 'lubon_partners.lubon_partners'

#     name = fields.Char()
# -*- coding: utf-8 -*-
from openerp import fields, models

class Partner(models.Model):
	_inherit = 'res.partner'

    # Add a new column to the res.partner model, by default partners are not
    # instructors
	mail_invoice = fields.Char(string="Invoice e-mail", help="e-mail adress used to send invoices")
	mail_reminder = fields.Char(string="Reminder e-mail", help="e-mail used to send reminders")
	rate_hr=fields.Float(string="Hourly rate")
	rate_travel=fields.Float(string="Travel rate")
        rate_day=fields.Float(string="Daily rate")
	credential_ids=fields.One2many('lubon_partner.credentials','partner_id',string='credentials')
	formal_communication = fields.Boolean(String="Formal", help="Tick to use formal communication")

class partner_title(models.Model):
	_inherit = "res.partner.title"
	formal_saluation = fields.Char(string="Formal saluation", help="Saluation on formal letter", translate=True)
	casual_saluation = fields.Char(string="Casual saluation", help="Saluation on casual letter", translate=True)


class Credentials(models.Model):
	_name='lubon_partner.credentials'
	description = fields.Char(string="Description", required=True)
        user = fields.Char(string="User", required=True)
        password = fields.Char(string="Password", type='password')
	partner_id = fields.Many2one('res.partner',  ondelete='set null', string="Partner", index=True)
	
	@api.one
	def show_password(self):
	    raise exceptions.ValidationError(self.password)


	def _get_ipaddress(self, cr, uid, context=None):
        	return request.httprequest.environ['REMOTE_ADDR'] 
