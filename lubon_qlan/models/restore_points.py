from openerp.osv import osv
from openerp import tools, models, fields, api, _
import csv,os,string,pdb
#from path import path
import openerp.addons.decimal_precision as dp
import openerp
from datetime import datetime,timedelta
from veeam import get_all_points

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
	veeamtype=fields.Selection([('VmRestorePoint','Restore point'),('VmReplicaPoint','Replica point')], default='VmRestorePoint')
	restorepoints_instances_id=fields.Many2one('lubon_qlan.restorepoints_instances')

	_sql_constraints = [
    
        ('UID_unique',
         'UNIQUE(uid)',
         "UID needs to be unique"),
    ]
class lubon_qlan_restore_points_stats(models.Model):
	_name='lubon_qlan.restore_points_stats'
	_description="Restore points stats"
	_order='date desc'
	_rec_name='date'


	_sql_constraints = [
    
        ('date_unique',
         'UNIQUE(date)',
         "Date needs to be unique"),
    ]

	date=fields.Date(required=True, help="Date is date displayed 12:00 to next day 12:00")
	restorepoints_instances_ids=fields.One2many('lubon_qlan.restorepoints_instances',"stats_id")
	number_succeeded=fields.Integer(help="Number of backups where a restore point is found")
	number_target=fields.Integer()
	rate_succeeded=fields.Integer(string="Succeeded (%)")
	number_requests_failed=fields.Integer(help="Number of requests where the veeam api returned an error result. The backup result is unknown.")
	re_evaluate=fields.Boolean(help="Refresh in next batch job?")
	@api.multi
	def process_restorepoints_stats(self,dummy=None):
		date=datetime.strptime(fields.Date.today(), "%Y-%m-%d").date() + timedelta(days=-1)
		date=datetime.strftime(date, "%Y-%m-%d")
		self.generate_restorepoints_instances(date).re_evaluate=True
		for stats in self.search([('re_evaluate','=', True)]):
			stats.check_all_restorepoints()



	@api.multi
	def generate_restorepoints_instances(self, targetdate=None):

		if self:
			targetdate=self.date
		if not targetdate:
			targetdate=fields.Date.today()

		stats_id=self.search([('date',"=",targetdate)])	
		if not stats_id:
			stats_id=self.create({'date': targetdate})
		vms=self.env['lubon_qlan.assets'].search([("vm_check_backup","=",True),("asset_type","=",'vm')])
		for vm in vms:
			self.env['lubon_qlan.restorepoints_instances'].generate_restorepoints_instance(stats_id,vm)
		stats_id.number_target=len(vms)
		return stats_id

	@api.multi
	def check_incomplete_restorepoints(self):
		self.check_all_restorepoints(True)

	@api.multi
	def check_all_restorepoints(self,failedonly=False):
		for q in ['VmRestorePoint', 'VmReplicaPoint']:
			points = get_all_points(self.date, q)
			for point in points:
				self.addpoint(point)
		self.update_rate_stats()
		#pdb.set_trace()

	@api.multi
	def addpoint(self,point):
		p=self.env['lubon_qlan.restorepoints'].search([('uid','=',point['UID'])])
		if not p:
			p=self.env['lubon_qlan.restorepoints'].create({'uid':point['UID']})
		p.asset_id=self.env['lubon_qlan.assets'].search([('asset_name','=',point['Name'])])
		p.creationtimeutc=point['Date']
		p.algorithm=point['algorithm']
		p.pointtype=point['pointtype']
#		p.hierarchyobjref=point['hierarchyobjref']
		p.veeamtype=point['Type']
		if not p.restorepoints_instances_id:
			search_date=fields.Date.to_string(fields.Datetime.from_string(p.creationtimeutc) - timedelta(hours=12))
			instance=self.env['lubon_qlan.restorepoints_instances'].search([('date',"=",search_date),('asset_id','=',p.asset_id.id)])
			p.restorepoints_instances_id=instance
		#instance.update_stats()

#		pdb.set_trace()





	@api.one
	def update_rate_stats(self):

#		self.number_succeeded=self.env['lubon_qlan.restorepoints_instances'].search_count([('stats_id','=',self.id),('number_restore',">",0)])
		
		for instance in self.restorepoints_instances_ids:
			instance.update_stats()
	
		self.number_succeeded=self.env['lubon_qlan.restorepoints_instances'].search_count([('stats_id','=',self.id),('stat_general',">",0)])

		self.number_requests_failed=self.env['lubon_qlan.restorepoints_instances'].search_count([('stats_id','=',self.id),('result_code',"!=",200)])

		self.rate_succeeded=int(self.number_succeeded*100/len(self.restorepoints_instances_ids))
		self.re_evaluate=False
		#pdb.set_trace()	

	def init(self,cr):
		self._migrate(cr, openerp.SUPERUSER_ID,[],{})
		# cr.execute("SELECT id, datum, departure_time FROM hertsens_rit"
  #       	     " WHERE departure_time IS NULL")
		# for datum, departure_time 
		#pdb.set_trace()
	@api.multi	
	def _migrate(self):
		if 1==12:
	# update vm's
			vmlist=self.env['lubon_qlan.assets'].search([('asset_name', 'like', 'replica'),('asset_type',"=",'vm')])
			for vm in vmlist:
				vm.vm_check_backup=False
		if 1==12:		
	# create older restore points
			date ="2016-08-01"
			while date < fields.Date.today():
				self.generate_restorepoints_instances(date)
				date=datetime.strptime(date, "%Y-%m-%d").date() + timedelta(days=1)
				date=datetime.strftime(date, "%Y-%m-%d")




class lubon_qlan_restorepoints_instances(models.Model):
	_name='lubon_qlan.restorepoints_instances'
	_rec_name='stats_id'
	_order='asset_id'
	_sql_constraints = [
    
        ('stats_id_asset_id_unique',
         'UNIQUE(stats_id,asset_id)',
         "Combination stats_id and asset_id needs to be unique"),
    ]


	stats_id = fields.Many2one('lubon_qlan.restore_points_stats', ondelete='cascade', required=True)
	asset_id = fields.Many2one('lubon_qlan.assets', ondelete='cascade', required=True)
	date=fields.Date()
	restorepoints_ids=fields.One2many('lubon_qlan.restorepoints','restorepoints_instances_id')
	number_restore=fields.Integer(help="Number of restore points")
	number_replica=fields.Integer(help="Number of replica points")
	number_vsphere_replica=fields.Integer(help="Number of vsphere replicas")
	stat_general=fields.Integer(help="General backup status")
	stat_restore_points=fields.Integer(help="Restorepoints status")
	stat_vsphere_replicas=fields.Integer("Vsphere replica status")
	stat_veeam_replicas=fields.Integer("Veeam replica status")

	result_code=fields.Integer()
	result_response=fields.Text()
	result_href=fields.Char()

	@api.one
	def update_stats(self):
		self.number_restore=len(self.restorepoints_ids.search([('veeamtype','=','VmRestorePoint'),('restorepoints_instances_id','=',self.id)]))
		self.number_replica=0 or len(self.restorepoints_ids.search([('veeamtype','=','VmReplicaPoint'),('restorepoints_instances_id','=',self.id)]))
		datetime_begin=fields.Datetime.from_string(self.stats_id.date)
		datetime_end=fields.Datetime.from_string(self.stats_id.date)+timedelta(hours=+24)
		datetime_begin=fields.Datetime.to_string(datetime_begin)
		datetime_end=fields.Datetime.to_string(datetime_end)
		self.number_vsphere_replica=self.env['lubon_qlan.events'].search_count([
			('related_id','=',self.asset_id.id),
			('model','=','lubon_qlan.assets'),
			('createtime','>=',datetime_begin),
			('createtime','<',datetime_end),
			('event_type','=','hbr.primary.DeltaCompletedEvent'),
			])


		if self.number_restore >= self.asset_id.vm_backup_req_restorepoints:
			self.stat_restore_points=1
		else:
			self.stat_restore_points=0
		if self.number_replica >= self.asset_id.vm_backup_req_veeam_replicas:
			self.stat_veeam_replicas=1
		else:
			self.stat_veeam_replicas=0
		if self.number_vsphere_replica >= self.asset_id.vm_backup_req_vsphere_replicas:
			self.stat_vsphere_replicas=1
		else:
			self.stat_vsphere_replicas=0

		self.stat_general=self.stat_restore_points * self.stat_veeam_replicas * self.stat_vsphere_replicas 



	@api.multi
	def find_restorepoints(self,failedonly=False):
		if not failedonly or (self.stat_general==0):
			self.asset_id.get_restorepoints(self,'VmRestorePoint')
			self.number_restore=len(self.restorepoints_ids.search([('veeamtype','=','VmRestorePoint'),('restorepoints_instances_id','=',self.id)]))
			self.asset_id.get_restorepoints(self,'VmReplicaPoint')
			self.number_replica=0 or len(self.restorepoints_ids.search([('veeamtype','=','VmReplicaPoint'),('restorepoints_instances_id','=',self.id)]))
			if self.number_restore >= self.asset_id.vm_backup_req_restorepoints:
				self.stat_restore_points=1
			else:
				self.stat_restore_points=0
			if self.number_replica >= self.asset_id.vm_backup_req_veeam_replicas:
				self.stat_veeam_replicas=1
			else:
				self.stat_veeam_replicas=0
			if self.number_vsphere_replica >= self.asset_id.vm_backup_req_vsphere_replicas:
				self.stat_vsphere_replicas=1
			else:
				self.stat_vsphere_replicas=0

			self.stat_general=self.stat_restore_points * self.stat_veeam_replicas * self.stat_vsphere_replicas 	
		#pdb.set_trace()
	@api.multi		
	def generate_restorepoints_instance(self, stats_id, asset_id):
		if not self.search( [ ('stats_id','=',stats_id.id) , ('asset_id','=', asset_id.id) ]):
			self.env['lubon_qlan.restorepoints_instances'].create({
				'stats_id': stats_id.id,
				'asset_id': asset_id.id,
				'date': stats_id.date,
				})



class lubon_qlan_restorepoints_instances_report(models.Model):
	_name='lubon_qlan.restorepoints_instances.report'
	_rec_name='date'
	_auto = False
	_order = 'date desc'

	date=fields.Date(readonly=True)
	max_date=fields.Date(readonly=True)

	stats_id=fields.One2many('lubon_qlan.restore_points_stats',readonly=True)
	asset_id=fields.One2many('lubon_qlan.assets', readonly=True)
	number_restore=fields.Integer(readonly=True)
	number_replica=fields.Integer(readonly=True)
	number_vsphere_replica=fields.Integer(readonly=True)
	backup_ok=fields.Integer(readonly=True)
	result_code=fields.Integer(readonly=True)
	asset_name=fields.Char(readonly=True)

	def sevendaysearlier():
		pdb.set_trace()

	def zzsearch(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
		pdb.set_trace()
		fiscalyear_obj = self.pool.get('account.fiscalyear')
		period_obj = self.pool.get('account.period')
		for arg in args:
		    if arg[0] == 'period_id' and arg[2] == 'current_period':
		        current_period = period_obj.find(cr, uid, context=context)[0]
		        args.append(['period_id','in',[current_period]])
		        break
		    elif arg[0] == 'period_id' and arg[2] == 'current_year':
		        current_year = fiscalyear_obj.find(cr, uid)
		        ids = fiscalyear_obj.read(cr, uid, [current_year], ['period_ids'])[0]['period_ids']
		        args.append(['period_id','in',ids])
		for a in [['period_id','in','current_year'], ['period_id','in','current_period']]:
		    if a in args:
		        args.remove(a)
		return super(account_entries_report, self).search(cr, uid, args=args, offset=offset, limit=limit, order=order,
		    context=context, count=count)

    # def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False,lazy=True):
    #     if context is None:
    #         context = {}
    #     fiscalyear_obj = self.pool.get('account.fiscalyear')
    #     period_obj = self.pool.get('account.period')
    #     if context.get('period', False) == 'current_period':
    #         current_period = period_obj.find(cr, uid, context=context)[0]
    #         domain.append(['period_id','in',[current_period]])
    #     elif context.get('year', False) == 'current_year':
    #         current_year = fiscalyear_obj.find(cr, uid)
    #         ids = fiscalyear_obj.read(cr, uid, [current_year], ['period_ids'])[0]['period_ids']
    #         domain.append(['period_id','in',ids])
    #     else:
    #         domain = domain
    #     return super(account_entries_report, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby,lazy)
	def init(self, cr):
		tools.drop_view_if_exists(cr, 'lubon_qlan_restorepoints_instances_report')
		cr.execute("""



			create or replace view lubon_qlan_restorepoints_instances_report as (
select l.id as id, s.date as date,l.number_restore as number_restore, l.number_replica as number_replica,l.number_vsphere_replica as number_vsphere_replica, l.stat_general as backup_ok, l.result_code as result_code, s.id as stats_id,a.id  as asset_id,	a.asset_name as asset_name, x.max_date as max_date from lubon_qlan_restorepoints_instances l
left join lubon_qlan_assets a on (l.asset_id = a.id)
left join lubon_qlan_restore_points_stats s on (l.stats_id=s.id)
left join (select aa.id, aa.asset_name, max(ss.date) as max_date from lubon_qlan_assets aa
left join lubon_qlan_restorepoints_instances ii on ii.asset_id=aa.id
left join lubon_qlan_restore_points_stats ss on ii.stats_id=ss.id
where ii.stat_general > 0
group by aa.id,aa.asset_name) x on x.id=a.id
where a.vm_check_backup = 't'
			)
			""")






			# select
			# l.id as id,
			# s.date as date,
			# l.number_restore as number_restore,
			# s.id as stats_id,
			# a.id as asset_id,
			# a.asset_name as asset_name
			# from
			# lubon_qlan_restorepoints_instances l
			# left join lubon_qlan_assets a on (l.asset_id = a.id)
			# left join lubon_qlan_restore_points_stats s on (l.stats_id=s.id)