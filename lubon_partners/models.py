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
#	credential_ids=fields.One2many('lubon_credentials.credentials','partner_id',string='credentials')
	formal_communication = fields.Boolean(String="Formal", help="Tick to use formal communication")
	updateswindows = fields.Boolean(String="Windows Updates", help="Get notified of windows updates")
        updateskluwer = fields.Boolean(String="Kluwer Updates", help="Get notified of kluwer updates")
        updatestelephony = fields.Boolean(String="Telephony Updates", help="Get notified of telephony updates")


class partner_title(models.Model):
	_inherit = "res.partner.title"
	formal_saluation = fields.Char(string="Formal saluation", help="Saluation on formal letter", translate=True)
	casual_saluation = fields.Char(string="Casual saluation", help="Saluation on casual letter", translate=True)


class Credentials(models.Model):
	_inherit='lubon_credentials.credentials'
	partner_id = fields.Many2one('res.partner',  ondelete='set null', string="Partner", index=True)
	
