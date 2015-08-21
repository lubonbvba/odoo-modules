# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from openerp.http import request



# class lubon_base(models.Model):
#     _name = 'lubon_base.lubon_base'

#     name = fields.Char()
class Partner(models.Model):
	_inherit = 'res.partner'
	mail_invoice = fields.Char(string="Invoice e-mail", help="e-mail adress used to send invoices")
	mail_reminder = fields.Char(string="Reminder e-mail", help="e-mail used to send reminders")
	mail_planning = fields.Char(string="Planning e-mail", help="e-mail used for planning")
	on=fields.Char(required=True,default="on")

class User(models.Model):
        _inherit = 'res.users'
#        operational_mode=fields.Boolean(string="Operational mode", help="When ticked customers of both companies are shown. No accounting possible")
        operational_mode=fields.Selection([('off','off'),('on','on')], required=True, default="off", string="Operational mode", help="If operational mode is on, customers and invoices of all the companies are shown. No accounting actions are possible.")
