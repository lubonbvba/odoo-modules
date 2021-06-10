# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime
import pdb,logging
import ast
logger = logging.getLogger(__name__)

class glacier_archives(models.Model):
	_inherit = 'aws.glacier_vault_archives'
	tenant_id = fields.Many2one('lubon_qlan.tenants')
	asset_id = fields.Many2one('lubon_qlan.assets')
	backup_type = fields.Selection([('W','Weekly'),('M','Monthly'),('S', 'System file'),('U','Unknown backup'),('X','TBD')])
	backup_date = fields.Datetime(help='Backup period identifier')
	last_update = fields.Datetime(help='Date the backup was synthesized')

	@api.multi
	def process_payload(self):
		archive_id=super(glacier_archives, self).process_payload()
		for a in self:
			payload=ast.literal_eval(a.archivedescription)
			if "UTCDateModified" in payload.keys():
				a.last_update=fields.Datetime.to_string(datetime.strptime(payload['UTCDateModified'].replace('T', ' ').replace('Z',''),"%Y%m%d %H%M%S"))
			if "Path" in payload.keys():
				a.backup_type='X'
				try:
					path=payload['Path']
					if '.vbk' in path:
						a.backup_type='U'
						filename=path[path.rfind('/')+1:]
						dotvmpos=filename.find('.vm')
						vmname=filename[:dotvmpos]
						backup_type=path[path.rfind('.')-1]
						if backup_type in ['W',"M"]:
							a.backup_type=backup_type
						#a.backup_type=path[path.rfind('.')-1]
	#					backupdate=filename[filename.rfind('-')-17:len(filename)-6].replace('T',' ')
						backupdate=filename[filename.rfind('T')-10:filename.rfind('T')+7].replace('T',' ')
	#					pdb.set_trace()
						a.backup_date=fields.Datetime.to_string(datetime.strptime(backupdate,"%Y-%m-%d %H%M%S"))
						asset_id=self.env['lubon_qlan.assets'].search([('asset_name','=',vmname),('asset_type','=','vm')])
						if len(asset_id)==1:
							a.asset_id=asset_id
							a.tenant_id=asset_id.tenant_id
				except:
					logging.error("Unable to process payload on archive %s" % (path))
				if '.vbm' in path or 'settings.list' in path:
					a.backup_type="S"
			#pdb.set_trace()		

	@api.multi
	def checkarchive(self,vault=None,archive=None):
		archive_id=super(glacier_archives, self).checkarchive(vault,archive)
		if not archive_id.backup_type:#pdb.set_trace()
			archive_id.process_payload()
		return archive_id

		