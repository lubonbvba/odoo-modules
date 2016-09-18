from openerp.osv import osv
from openerp import tools, models, fields, api, _
import csv,os,string,pdb
from path import path
import openerp.addons.decimal_precision as dp
import openerp
from datetime import datetime,timedelta

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
	def check_all_restorepoints(self):
		for instance in self.restorepoints_instances_ids:
			instance.find_restorepoints()

		self.number_succeeded=self.env['lubon_qlan.restorepoints_instances'].search_count([('stats_id','=',self.id),('number_found',">",0)])

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
	number_found=fields.Integer()
	result_code=fields.Integer()
	result_response=fields.Text()
	result_href=fields.Char()
	@api.multi
	def find_restorepoints(self):
		self.asset_id.get_restorepoints(self)
		self.number_found=len(self.restorepoints_ids)

	@api.multi		
	def generate_restorepoints_instance(self, stats_id, asset_id):
		if not self.search( [ ('stats_id','=',stats_id.id) , ('asset_id','=', asset_id.id) ]):
			self.env['lubon_qlan.restorepoints_instances'].create({
				'stats_id': stats_id.id,
				'asset_id': asset_id.id,
				})



class lubon_qlan_restorepoints_instances_report(models.Model):
	_name='lubon_qlan.restorepoints_instances.report'
	_rec_name='date'
	_auto = False
	_order = 'date desc'

	date=fields.Date(readonly=True)
	stats_id=fields.One2many('lubon_qlan.restore_points_stats',readonly=True)
	asset_id=fields.One2many('lubon_qlan.assets', readonly=True)
	number_found=fields.Integer(readonly=True)
	asset_name=fields.Char(readonly=True)

	def sevendaysearlier():
		pdb.set_trace()

	def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
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
			select
			l.id as id,
			s.date as date,
			l.number_found as number_found,
			s.id as stats_id,
			a.id as asset_id,
			a.asset_name as asset_name
			from
			lubon_qlan_restorepoints_instances l
			left join lubon_qlan_assets a on (l.asset_id = a.id)
			left join lubon_qlan_restore_points_stats s on (l.stats_id=s.id)
			)
			""")
