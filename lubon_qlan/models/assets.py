#-*- coding: utf-8 -*-
import atexit
import ssl

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

# #import tools.cli as cli


from openerp import models, fields, api
from openerp.exceptions import Warning
import pdb


class lubon_qlan_assets(models.Model):
	_name="lubon_qlan.assets"
	_description = 'zzEquipment'
	_rec_name="asset_name"
	_inherit = ['mail.thread','ir.needaction_mixin']
	
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
	part=fields.Char(string="Part n°", help="Manufacturer part number")
	warranty_end_date=fields.Date(string="End date warranty")
	sequence=fields.Integer()
	notes=fields.Html()
	location=fields.Char(help="Where is the asset located")
	ips=fields.One2many('lubon_qlan.ip','asset_id')
	interfaces_ids=fields.One2many('lubon_qlan.interfaces','asset_id')
	credentials_ids=fields.One2many('lubon_credentials.credentials','asset_id')
	vm_memory=fields.Char(track_visibility='onchange')
	vm_cpu=fields.Integer(track_visibility='onchange')
	vm_uuid_instance=fields.Char(track_visibility='onchange')
	vm_uuid_bios=fields.Char(track_visibility='onchange')
	vm_path_name=fields.Char(track_visibility='onchange')

	#vcenter fields
	vc_dns=fields.Char(string="vcenter dns")
	vc_port=fields.Integer(string="vcenter tcp port", default=443)
	vc_password_id=fields.Many2one('lubon_credentials.credentials')



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
			#context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
			#context.verify_mode = ssl.CERT_NONE
			service_instance = connect.SmartConnect(host=self.vc_dns,
				user=self.vc_password_id.user,
				pwd=self.vc_password_id.decrypt()[0],
				port=self.vc_port)
				#sslContext=context)

#			atexit.register(connect.Disconnect, service_instance)
#			pdb.set_trace()
#			raise Warning ("Login OK")
			return service_instance 
		except vmodl.MethodFault as error:
			raise Warning ("Caught vmodl fault :",  error.msg)   
	@api.one	
	def vc_test_login(self):
		session=self._vc_login()

	@api.one
	def vc_get_vms(self):
		context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
		context.verify_mode = ssl.CERT_NONE
		service_instance = connect.SmartConnect(host=self.vc_dns,
				user=self.vc_password_id.user,
				pwd=self.vc_password_id.decrypt()[0],
				port=self.vc_port,
				sslContext=context)
		atexit.register(connect.Disconnect, service_instance)
		content = service_instance.RetrieveContent()

		container = content.rootFolder  # starting point to look into
		viewType = [vim.VirtualMachine]  # object types to look for
		recursive = True  # whether we should look into it recursively
		containerView = content.viewManager.CreateContainerView(
			container, viewType, recursive)
		
		children = containerView.view
		for child in children:
			self.vc_check_vm(child)

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
		asset.vm_path_name=virtual_machine.summary.config.vmPathName
		#pdb.set_trace()




