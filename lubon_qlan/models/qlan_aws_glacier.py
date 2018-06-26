# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime
import pdb
import ast

class glacier_archives(models.Model):
	_inherit = 'aws.glacier_vault_archives'
	tenant_id = fields.Many2one('lubon_qlan.tenants')
	asset_id = fields.Many2one('lubon_qlan.assets')
	backup_type = fields.Selection([('W','Weekly'),('M','Monthly'),('S', 'System file')])
	backup_date = fields.Datetime(help='Backup period identifier')
	last_update = fields.Datetime(help='Date the backup was synthesized')

	@api.multi
	def process_payload(self):
		payload=ast.literal_eval(self.archivedescription)
		if "UTCDateModified" in payload.keys():
			self.last_update=fields.Datetime.to_string(datetime.strptime(payload['UTCDateModified'].replace('T', ' ').replace('Z',''),"%Y%m%d %H%M%S"))
		if "Path" in payload.keys():
			path=payload['Path']
			if '.vbk' in path:
				filename=path[path.rfind('/')+1:]
				dotvmpos=filename.find('.vm')
				vmname=filename[:dotvmpos]
				self.backup_type=path[path.rfind('.')-1]
				backupdate=filename[filename.rfind('+AF8')-17:len(filename)-10].replace('T',' ')
				self.backup_date=fields.Datetime.to_string(datetime.strptime(backupdate,"%Y-%m-%d %H%M%S"))
				asset_id=self.env['lubon_qlan.assets'].search([('asset_name','=',vmname),('asset_type','=','vm')])
				if len(asset_id)==1:
					self.asset_id=asset_id
					self.tenant_id=asset_id.tenant_id
			if '.vbm' in path or 'settings.list' in path:
				self.backup_type="S"

