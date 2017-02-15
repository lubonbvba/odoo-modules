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

class lubon_qlan_portgroups(models.Model):
	_name = 'lubon_qlan.portgroups'
	_description = 'Portgroups'

	_sql_constraints = [
    
        ('UUID_unique',
         'UNIQUE(uuid,asset_id)',
         "UUID needs to be unique"),
    ]


	asset_id=fields.Many2one('lubon_qlan.assets')
	name=fields.Char(string="Portgroup description")
	uuid=fields.Char(string="UUID")

class lubon_qlan_datastores(models.Model):
	_name = 'lubon_qlan.datastores'
	_description = 'Datastores'

	_sql_constraints = [
    
        ('URL_unique',
         'UNIQUE(url,asset_id)',
         "url needs to be unique"),
    ]

	asset_id=fields.Many2one('lubon_qlan.assets')
	name=fields.Char(string="Datastore description")
	url=fields.Char(string="url")
	free=fields.Float()
	capacity=fields.Float()
	rate_free=fields.Float()



