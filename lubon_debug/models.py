# -*- coding: utf-8 -*-

from openerp import models, fields, api

# class lubon_debug(models.Model):
#     _name = 'lubon_debug.lubon_debug'

#     name = fields.Char()


class account_invoice(models.Model):
	_inherit='account.invoice'
	analyticlines = fields.One2many('account.analytic.line','invoice_id')	
