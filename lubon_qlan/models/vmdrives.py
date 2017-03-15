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
	number_snapshots=fields.Integer(string="Number of snapshots")
	oldest_snapshot=fields.Datetime()

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
			q=path(f)
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