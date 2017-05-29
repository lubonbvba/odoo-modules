# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api, _
import csv,os,string,pdb
#from path import path
import openerp.addons.decimal_precision as dp

class res_partner(models.Model):
	_inherit= "res.partner"

	site_responsible=fields.One2many('lubon_qlan.sites','main_contact', domain=[("active","=",True)])
