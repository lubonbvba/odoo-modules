# -*- coding: utf-8 -*-

from openerp import models, fields, api

class lubon_qlan_tenants(models.Model):
	_name = 'lubon_qlan.tenants'
	_rec_name = 'code'
	_sql_constraints = [('code_unique','UNIQUE(code)','Code has to be unique')]
	code = fields.Char(oldname='name', required=True, help='Tenant code')
	qadm_password = fields.Char(help="Password for qadm@upn user")
	qtest_password = fields.Char()
	upn = fields.Char()
	ip = fields.Char()

