from openerp import tools, models, fields, api, _
import pdb
import openerp.addons.decimal_precision as dp
import openerp
from datetime import datetime,timedelta

class lubon_qlan_licenses(models.Model):
	_name = 'lubon_qlan.licenses'
	_description = 'License contracts'


	name=fields.Char(string="License name")
	reference=fields.Char(help="License nr, contract info, vendor ...")
	responsible_person=fields.Many2one('res.partner')
	members=fields.One2many('lubon_qlan.assets','licenses_id')


