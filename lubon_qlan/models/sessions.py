from openerp import tools, models, fields, api, _
import csv,os,string,pdb
import openerp.addons.decimal_precision as dp
import openerp
from datetime import datetime,timedelta

class lubon_qlan_xasessions(models.Model):
	_name = 'lubon_qlan.xasessions'
	_description = 'Xenapp Sessions'
	
	date_start=fields.Char()





class lubon_qlan_xasessions_details(models.TransientModel):
	_name = 'lubon_qlan.xasessions_details'
	_description = 'Xenapp Session details'
	
	date_start=fields.Char()

	def cmd_execute_method(self,cmd_execute):
		result=cmd_execute.execute({})
		pdb.set_trace()