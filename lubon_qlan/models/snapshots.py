from openerp.osv import osv
from openerp import tools, models, fields, api, _
import csv,os,string,pdb
from path import path
import openerp.addons.decimal_precision as dp
import openerp
from datetime import datetime,timedelta

class lubon_qlan_snapshots(models.Model):
	_name = 'lubon_qlan.snapshots'
	_description = 'Snapshots'
	asset_id=fields.Many2one('lubon_qlan.assets')
	createTime = fields.Datetime()
	name=fields.Char(string="Snapshot description")