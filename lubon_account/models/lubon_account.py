# -*- coding: utf-8 -*-

from openerp import models, fields, api
import pdb

class account_account(models.Model):
	_inherit = 'account.account'
	name = fields.Char(translate=False)
