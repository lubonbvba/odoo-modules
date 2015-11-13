# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from openerp.http import request



# class lubon_base(models.Model):
#     _name = 'lubon_base.lubon_base'

#     name = fields.Char()
class account_statement_operation_template(models.Model):
	_inherit = 'account.statement.operation.template'
	company_id=fields.Many2one('res.company')

