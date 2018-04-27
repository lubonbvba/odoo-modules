from openerp import tools, models, fields, api, _
import csv,os,string,pdb
import openerp.addons.decimal_precision as dp
import openerp
from datetime import datetime,timedelta

class lubon_qlan_events(models.Model):
	_name = 'lubon_qlan.events'
	_description = 'Events'
	_order = "createtime desc"

	_sql_constraints = [
    
        ('external_id_asset_id_unique',
         'UNIQUE(asset_id,external_id )',
         "Combination asset_id and external_id needs to be unique"),
    ]

	asset_id=fields.Many2one('lubon_qlan.assets', help="Event Source", required=True)
	createtime = fields.Datetime(index=True)
	name=fields.Char(string="Event name")
	event_full=fields.Char(string="Full event")
	external_id=fields.Char(string="External event ID", help="Event ID as defined by the generating system")
	event_type=fields.Char(help="External event_type", index=True)
	event_source_type=fields.Selection([('vc','vcenter'),('2FA','SMS Passcode')],help="Source type of the event")
	model=fields.Char(index=True)
	related_id=fields.Integer(index=True)



