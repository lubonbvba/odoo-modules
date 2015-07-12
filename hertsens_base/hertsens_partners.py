# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from openerp.http import request



# class lubon_base(models.Model):
#     _name = 'lubon_base.lubon_base'

#     name = fields.Char()
class Partner(models.Model):
        _inherit = 'res.partner'

    # Add a new column to the res.partner model, by default partners are not
    # instructors
        mail_invoice = fields.Char(string="Invoice e-mail", help="e-mail adress used to send invoices")
        mail_reminder = fields.Char(string="Reminder e-mail", help="e-mail used to send reminders")
	mail_planning = fields.Char(string="Planning e-mail", help="e-mail used for planning")

