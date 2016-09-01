from openerp.osv import osv
from openerp import models, fields, api, _
import csv,os,string,pdb
from path import path
import openerp.addons.decimal_precision as dp


class lubon_qlan_restorepoints(models.Model):
	_name = 'lubon_qlan.restorepoints'
	_description = 'Restorepoints'
	_order = 'creationtimeutc desc'
	asset_id=fields.Many2one('lubon_qlan.assets')

	uid=fields.Char(required=True, index=True)
	creationtimeutc=fields.Datetime()
	algorithm=fields.Char()
	pointtype=fields.Char()
	hierarchyobjref=fields.Char()
	BackupServerReference=fields.Char()

	_sql_constraints = [
    
        ('UID_unique',
         'UNIQUE(uid)',
         "UID needs to be unique"),
    ]
