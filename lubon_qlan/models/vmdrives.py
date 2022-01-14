from openerp.osv import osv
from openerp import tools, models, fields, api, _
import csv,os,string,pdb, logging
from path import Path
import openerp.addons.decimal_precision as dp
import openerp
from datetime import datetime,timedelta
from os.path import expanduser
import codecs,json

logger = logging.getLogger(__name__)


class lubon_qlan_drives(models.Model):
	_name = 'lubon_qlan.drives'
	_description = 'Disk drives'
	_order = 'name'
	asset_id=fields.Many2one('lubon_qlan.assets')
	name=fields.Char(string="Drive name")
	last_changed=fields.Datetime(help='When was the last change')
	last_updated=fields.Datetime(help='When was the info refreshed')
	drivetype=fields.Char()
	uniqueid=fields.Char()
	friendlyname=fields.Char()
	healthstatus=fields.Char()
	drive_size_bytes=fields.Float()
	drive_size_giga_bytes=fields.Float()
	contract_line_id=fields.Many2one('account.analytic.invoice.line', domain="[('analytic_account_id','in', valid_contract_ids[0][2])]")
	valid_contract_ids=fields.Many2many('account.analytic.account', compute='_get_valid_contract_ids')

	@api.one
	def _get_valid_contract_ids(self):
		self.valid_contract_ids=self.asset_id.tenant_id.contract_ids

	@api.multi
	def update_drives(self,asset_name,drivedata):
		logger.info ("Start update drive for: %s" % asset_name)
		asset_id=self.env['lubon_qlan.assets'].search([('asset_name','=', asset_name)])
		if len(asset_id) ==1:
			for drive in drivedata['drivedata']:
				if drive['DriveType']=="Fixed":
					drive_id=self.search([("asset_id","=",asset_id.id),("uniqueid","=",drive['Uniqueid'])])
					if not drive_id:
						drive_id=self.create({
							'asset_id': asset_id.id,
							'uniqueid': drive['Uniqueid'],
							'drivetype': drive['DriveType']
						})
					if drive_id.drive_size_bytes != drive['Size']:
						drive_id.drive_size_bytes = drive['Size']
						drive_id.drive_size_giga_bytes = drive['Size'] / (1024*1024*1024)
						drive_id.last_changed=fields.Datetime.now()
					if drive_id.contract_line_id:
						if drive_id.contract_line_id.current_usage != drive_id.drive_size_giga_bytes:	
							drive_id.contract_line_id.current_usage=drive_id.drive_size_giga_bytes
					
					drive_id.name=drive['DriveLetter']
					drive_id.friendlyname=drive['FriendlyName']
					drive_id.healthstatus=drive['HealthStatus']
					drive_id.last_updated=fields.Datetime.now()


					
		else:
			logger.error ("Asset not found, or not unique: %s" % asset_name)
			



	@api.multi
	def read_drives(self,dummy=None):
		logger.info('drives')
		basepath=expanduser("~")
		basepath +='/odoo-imports/ShadowCopies'
		destpath=basepath + '/hist'
		p = Path(basepath)
		for f in p.files(pattern='Daily-2*.json'):
			
#			s=f.stripext().basename().lstrip('Daily-')
			logger.info('Processing file: ' + f.name)

			with codecs.open(f, encoding='utf-16') as fi:
				reader = json.load(fi)
				for a in reader:
					self.updatedrive(a)
			q=Path(f)
			q.move(destpath)		
			# fi = open(f, 'rb')
			# data = fi.read()
			# fi.close()
			# fo = open(basepath + '/Daily-clean.csv', 'wb')
			# fo.write(data.replace('\x00', ''))
			# fo.close()


#			with open (basepath + '/Daily-clean.csv', 'rb') as cleanfile:
#				reader = csv.DictReader(cleanfile, delimiter=';')
	def updatedrive(self,driveinfo):
		asset=self.env["lubon_qlan.assets"].search([('asset_name','=',driveinfo['ComputerName']),('asset_type','=','vm')])
		asset.ensure_one()
	#	for d in asset.vm_drives_ids:
	#		d.unlink()
		drive=self.env["lubon_qlan.drives"].search([('name', 'ilike', driveinfo['VolumeName'].replace('\\','')),('asset_id','=',asset.id)])

		last_snapshot=datetime.strptime(driveinfo['Date'], "%Y%m%d%H%M")
		#pdb.set_trace()
		if not drive:
			drive=self.env["lubon_qlan.drives"].create({
				'asset_id':asset.id,
				'name':driveinfo['VolumeName'],
				})
		drive.write({
				'number_snapshots':driveinfo['ShadowCopyCount'],
				'oldest_snapshot': fields.Datetime.to_string(last_snapshot),
				})
		#pdb.set_trace()