#-*- coding: utf-8 -*-
import atexit
import ssl

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

# #import tools.cli as cli


from openerp import models, fields, api
from openerp.exceptions import Warning
import pdb, logging
from veeam import get_restorepoints
import datetime

logger = logging.getLogger(__name__)
containerView = ""

class lubon_qlan_assets(models.Model):
	_name="lubon_qlan.assets"
	_description = 'zzEquipment'
	_rec_name="asset_name"
	_inherit = ['mail.thread','ir.needaction_mixin']
	_order = 'asset_name'
	parent_id=fields.Many2one('lubon_qlan.assets', string="Part of")

	child_ids=fields.One2many('lubon_qlan.assets','parent_id')
	is_container=fields.Boolean(string="Container", help="Can contain other devices")
	show_in_site=fields.Boolean(string="Show", help="Show in sites", default=True)
	quant_id=fields.Many2one('stock.quant')
	product_id=fields.Many2one('product.product')
	site_id=fields.Many2one('lubon_qlan.sites', required=True, help="Readonly if part of another eqpt or has parts.")
	tenant_id=fields.Many2one('lubon_qlan.tenants', string="Tenant")
	asset_name=fields.Char(required=True, string="Eqpt. name")
	asset_type=fields.Selection([('switch','Switch'),('server','Physical server'),('firewall','Firewall'),('vm','Virtual machine'),('vc','Vcenter'),])
	asset_remarks=fields.Html(string="Remarks")
	lot=fields.Char(string="Serial", help="Serial Number")
	part=fields.Char(string="Part nr", help="Manufacturer part number")
	warranty_end_date=fields.Date(string="End date warranty")
	sequence=fields.Integer()
	notes=fields.Html()
	location=fields.Char(help="Where is the asset located")
	ips=fields.One2many('lubon_qlan.ip','asset_id')
	interfaces_ids=fields.One2many('lubon_qlan.interfaces','asset_id')
	credentials_ids=fields.One2many('lubon_credentials.credentials','asset_id')

	assigned_events_ids=fields.One2many('lubon_qlan.events', 'related_id',	domain=lambda self: [('model', '=', self._name)],auto_join=True,string='Assignedevents' ,help="Events assigned to this asset")
	asset_event_last_check=fields.Datetime(help="Time of the latest event")

	licenses_id=fields.Many2one('lubon_qlan.licenses')

	vm_memory=fields.Char(track_visibility='onchange')
	vm_cpu=fields.Integer(track_visibility='onchange', string="Virtual CPU", help="Number of virtual cpus. (Socket * number of cores per socket")
	vm_guestos=fields.Char(track_visibility='onchange')
	vm_cores_per_socket=fields.Integer(track_visibility='onchange', string="Cores/Socket", help='Number of cores per socket' )
	vm_sockets=fields.Integer(track_visibility='onchange', string="Sockets", help='Number of sockets' )
	vm_uuid_instance=fields.Char(track_visibility='onchange')
	vm_uuid_bios=fields.Char(track_visibility='onchange')
	vm_path_name=fields.Char(track_visibility='onchange')
	vm_power_state=fields.Char(track_visibility='onchange')
	vm_check_backup=fields.Boolean(track_visibility='onchange', default=True)
	vm_restorepoints_ids=fields.One2many('lubon_qlan.restorepoints',"asset_id")
	vm_latest_restore_point=fields.Datetime()

	vm_restorepoints_instances_ids=fields.One2many('lubon_qlan.restorepoints_instances',"asset_id")
	vm_snapshots_ids=fields.One2many("lubon_qlan.snapshots","asset_id")
	vm_drives_ids=fields.One2many("lubon_qlan.drives","asset_id")

	vm_snapshots_count=fields.Integer()
	vm_date_last=fields.Datetime(help="Date last inventoried")
	vm_backup_req_restorepoints=fields.Integer(help="Min restorepoints required", string="Min req restore points" )
	vm_backup_req_veeam_replicas=fields.Integer(help="Min veeam replicas required", string="Min req veeam replicas")
	vm_backup_req_vsphere_replicas=fields.Integer(help="Min vsphere replicas required", string="Min req vsphere replicas")
	#vcenter fields
	vc_dns=fields.Char(string="vcenter dns")
	vc_port=fields.Integer(string="vcenter tcp port", default=443)
	vc_password_id=fields.Many2one('lubon_credentials.credentials')
	vc_check=fields.Boolean(string="Include in schedule?" )
	vc_portgroups_ids=fields.One2many("lubon_qlan.portgroups","asset_id")
	vc_datastores_ids=fields.One2many("lubon_qlan.datastores","asset_id")
	vc_events_ids=fields.One2many("lubon_qlan.events","asset_id")
	@api.multi
	def new_asset(self,site_id,quant_id):
		asset = self.create({
			'site_id': site_id.id,
			'quant_id': quant_id.id,
			'asset_name': quant_id.product_id.name + '-' + quant_id.name,
			'lot':quant_id.lot_id.name,
			'product_id': quant_id.product_id.id,
			})
		#pdb.set_trace()
	@api.one
	@api.depends('ips')
	def _calculate_ip_display(self):
		self.ip_display=""
		for ip in self.ips:
			if ip.name:
				if self.ip_display:
					self.ip_display+=","
				self.ip_display+=ip.name
	ip_display=fields.Char(string="IP", compute="_calculate_ip_display", store=True)
		
	@api.one
	@api.onchange('site_id')
	def manage_site_id(self):
		#pdb.set_trace()
#		if self.child_ids:
#			return {'title': 'Fout', 'message': "Heeft childs"}
		for interface in self.interfaces_ids:
			interface.site_id=self.site_id
		for credential in self.credentials_ids:
			credential.site_id=self.site_id
			#pdb.set_trace()
		for ip in self.ips:
			ip.site_id=self.site_id
	# @api.one
	# def write(self,vals):
	# 	pdb.set_trace()
	# 	super(lubon_qlan_assets,self).write(vals)
	@api.one
	def _vc_login(self):
		try:
			context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
			context.verify_mode = ssl.CERT_NONE
			service_instance = connect.SmartConnect(host=self.vc_dns,
				user=self.vc_password_id.user,
				pwd=self.vc_password_id.decrypt()[0],
				port=self.vc_port,
				sslContext=context)

#			atexit.register(connect.Disconnect, service_instance)
#			pdb.set_trace()
#			raise Warning ("Login OK")
			return service_instance 
		except vmodl.MethodFault as error:
			raise Warning ("Caught vmodl fault :",  error.msg)   
	@api.one	
	def vc_test_login(self):
		session=self._vc_login()

	@api.multi
	def vc_inventory(self,dummy=None):
		for vc in self.search([('vc_check','=',True)]):
			logger.info("Run vc_inventory: %s" % vc.asset_name)
			vc.vc_get_all()
	@api.one
	def _vc_get_containerview(self,viewType):
		context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
		context.verify_mode = ssl.CERT_NONE
		global containerView
		global content
		service_instance = connect.SmartConnect(host=self.vc_dns,
				user=self.vc_password_id.user,
				pwd=self.vc_password_id.decrypt()[0],
				port=self.vc_port,
				sslContext=context)
		atexit.register(connect.Disconnect, service_instance)
		content = service_instance.RetrieveContent()

		container = content.rootFolder  # starting point to look into
#		viewType = [vim.VirtualMachine]  # object types to look for
		viewType = viewType  # object types to look for
		recursive = True  # whether we should look into it recursively
		containerView = content.viewManager.CreateContainerView(
			container, viewType, recursive)

	@api.one
	def vc_get_all(self):
		logger.info("Start vc_get_all %s" % self.asset_name)
		self.vc_get_networks()
		self.vc_get_datastores()
		self.vc_get_vms()
		self.vc_get_events()


	@api.one
	def vc_get_vms(self):
		logger.info("Start vc_get_vms %s" % self.asset_name)
		self._vc_get_containerview([vim.VirtualMachine])
		for child in containerView.view:
			if '_replica_' not in child.summary.config.name:
				self.vc_check_vm(child)

	@api.one
	def vc_get_networks(self):
		logger.info("Start vc_get_networks %s" % self.asset_name)
		self._vc_get_containerview([vim.DistributedVirtualPortgroup])
		for child in containerView.view:
			#logger.info("Portgroup: %s " %  child.config.name)
			logger.info("Portgroup: %s " %  child.key)
			portgroup=self.vc_portgroups_ids.search([('uuid','=',child.key),('asset_id','=',self.id)])
			if not portgroup:
				self.vc_portgroups_ids.create(
					{'uuid': child.key,
					'name':child.config.name,
					'asset_id': self.id,
					})
			#pdb.set_trace()
	@api.one
	def vc_get_datastores(self):
		logger.info("Start vc_get_datastores %s" % self.asset_name)

		self._vc_get_containerview([vim.Datastore])
		for child in containerView.view:
			#logger.info("Portgroup: %s " %  child.config.name)
			logger.info("Datastore: %s " %  child.info.name)
			datastore=self.vc_datastores_ids.search([('url','=',child.info.url),('asset_id','=',self.id)])
			if not datastore:
				datastore=self.vc_datastores_ids.create(
					{'url': child.info.url,
					'name':child.info.name,
					'asset_id': self.id,
					})
			datastore.free=child.info.freeSpace/(1024*1024*1024)
			datastore.capacity=child.summary.capacity/(1024*1024*1024)
			datastore.rate_free=int(10000*datastore.free/datastore.capacity)/100
			#pdb.set_trace()
	@api.multi
	def vc_get_events(self,context=None,eventTypeId='hbr.primary.DeltaCompletedEvent'):
		logger.info("Start vc_get_events %s" % self.asset_name)
		self._vc_get_containerview([vim.HostSystem])
		eMgrRef = content.eventManager
		filter_spec = vim.event.EventFilterSpec()
		filter_spec.eventTypeId = eventTypeId
		oldevents=self.env['lubon_qlan.events'].search([('asset_id','=',self.id),('event_type','=',eventTypeId)])
		oldevents.sorted(key=lambda r: r.createtime,reverse=True)
		if oldevents:
			newest=fields.Datetime.from_string(oldevents[0].createtime) 
			time_filter=vim.event.EventFilterSpec.ByTime(beginTime=newest + datetime.timedelta(seconds=1))
			filter_spec.time=time_filter                

		while True:
			event_res = eMgrRef.QueryEvents(filter_spec)
			if len(event_res) ==1:
				break
			logger.info("vc_get_events: Number of events: %d" % len(event_res))
			for e in event_res:
				#pdb.set_trace()
				if not self.env['lubon_qlan.events'].search([('asset_id','=',self.id),('external_id',"=",e.key)]):
					vm=self.env['lubon_qlan.assets'].search([('asset_name','=',e.vm.name),('parent_id','=',self.id)])
					evt=self.env['lubon_qlan.events'].create({
						'asset_id': self.id,
						'external_id': e.key,
						'event_type': e.eventTypeId,
						'event_source_type':'vc',
						'event_full': e.fullFormattedMessage,
						'createtime': fields.Datetime.to_string(e.createdTime), 
						'model': 'lubon_qlan.assets',
						'related_id': vm.id,
						})
			time_filter=vim.event.EventFilterSpec.ByTime(beginTime=e.createdTime)
			filter_spec.time=time_filter  
			#pdb.set_trace()


	@api.one
	def vc_check_vm(self,child):
		asset=self.env['lubon_qlan.assets'].search([('asset_name','=',child.name)])
		virtual_machine=child
		if len(asset)>1:
			raise Warning ("Duplicate VM found :",  asset[0].asset_name)
		if not asset:
			asset=self.env['lubon_qlan.assets'].create({
				'asset_name': virtual_machine.summary.config.name,
				'vm_uuid_instance': virtual_machine.summary.config.instanceUuid,
				'vm_uuid_bios': virtual_machine.summary.config.uuid,
				'parent_id': self.id,
				'site_id': self.site_id.id,
				'asset_type': 'vm',
				})
		else:
			if not asset.asset_type:
				asset.asset_type='vm'
			if not asset.vm_uuid_bios:
				asset.vm_uuid_bios=virtual_machine.summary.config.uuid
			if not asset.vm_uuid_instance:
				asset.vm_uuid_instance=virtual_machine.summary.config.instanceUuid
			if not asset.parent_id:
				asset.parent_id=self.id
		asset.vm_memory=virtual_machine.summary.config.memorySizeMB
		asset.vm_cpu=virtual_machine.summary.config.numCpu
		asset.vm_guestos=virtual_machine.summary.config.guestFullName
		#pdb.set_trace()
		asset.vm_cores_per_socket=virtual_machine.config.hardware.numCoresPerSocket
		asset.vm_sockets=asset.vm_cpu/asset.vm_cores_per_socket
		asset.vm_path_name=virtual_machine.summary.config.vmPathName
		asset.vm_power_state=virtual_machine.runtime.powerState
		asset.vm_date_last=fields.Datetime.now()
		for snapshot in asset.vm_snapshots_ids:
			snapshot.unlink()
		asset.vm_snapshots_count=0	
		if virtual_machine.snapshot:
			for snapshot in virtual_machine.snapshot.rootSnapshotList:
				self.env["lubon_qlan.snapshots"].create({
					'asset_id': asset.id,
					'name': snapshot.name,
					'createTime': snapshot.createTime,
					})
				logger.info("Name: %s " %  snapshot.name)
				asset.vm_snapshots_count+=1
		#if virtual_machine.tag:		
		#	pdb.set_trace()
		#for network in virtual_machine.network:
			#pdb.set_trace()
	@api.multi
	def get_vm_drives(self):
		self.env['lubon_qlan.drives'].read_drives()
				
	@api.multi
	def get_restorepoints(self,instance_id=None,querytype=None):
		if instance_id:
			target_date=instance_id.stats_id.date

		
		result = get_restorepoints(self.asset_name, target_date, querytype)
#		pdb.set_trace()
		points=result['res']
		newest = ""
		for point in points:
			rec=self.env['lubon_qlan.restorepoints'].search([('uid','like',point['uid'])])
			if not rec:
				newrec={
					'uid':point['uid'],
					'asset_id': self.id,
					'creationtimeutc': point['creationtimeutc'],
					'BackupServerReference': point['BackupServerReference'],
					'algorithm':point['algorithm'],
					'pointtype':point['pointtype'],
					'veeamtype':querytype,
#					'hierarchyobjref':point['hierarchyobjref'],
					}
				#pdb.set_trace()
				rec=self.env['lubon_qlan.restorepoints'].create(newrec)
			if point['creationtimeutc'] > newest:
				newest=point['creationtimeutc']
			if instance_id:
				rec.restorepoints_instances_id=instance_id
		instance_id.result_href=result['href']	
		instance_id.result_code=result['response'].status_code	
		instance_id.result_response=result['response'].content
		#pdb.set_trace()
		datetime_begin=fields.Datetime.from_string(instance_id.stats_id.date)
		datetime_end=fields.Datetime.from_string(instance_id.stats_id.date)+datetime.timedelta(hours=+24)
		datetime_begin=fields.Datetime.to_string(datetime_begin)
		datetime_end=fields.Datetime.to_string(datetime_end)
		#pdb.set_trace()
		instance_id.number_vsphere_replica=self.env['lubon_qlan.events'].search_count([
			('related_id','=',self.id),
			('model','=','lubon_qlan.assets'),
			('createtime','>=',datetime_begin),
			('createtime','<',datetime_end),
			('event_type','=','hbr.primary.DeltaCompletedEvent'),
			])
		#pdb.set_trace()

		if len(newest) > 0 and (newest.replace('T',' ') > self.vm_latest_restore_point) :
			self.vm_latest_restore_point=newest.replace('T',' ')		

				
	@api.multi			
	def get_all_restorepoints(self,fake=None):
		vms=self.search([("vm_check_backup","=",True),("asset_type","=",'vm')])
		#pdb.set_trace()
		for vm in vms:
			vm.get_restorepoints()

