# -*- coding: utf-8 -*-

from openerp import models, fields, api

class lubon_ir_mail_server(models.Model):
	_name = "ir.mail_server"
 	_inherit = ["ir.mail_server"]
 	smtp_pass = fields.Char(size=120)
