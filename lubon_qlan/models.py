# -*- coding: utf-8 -*-

from openerp import models, fields, api,exceptions,_
import csv,os,string,datetime,logging
from path import path
import pdb
from os.path import expanduser

logger = logging.getLogger(__name__)

class lubon_qlan_tenants(models.Model):
	_name = 'lubon_qlan.tenants'
	_rec_name = 'code'
	_sql_constraints = [('code_unique','UNIQUE(code)','Code has to be unique')]
	code = fields.Char(oldname='name', required=True, help='Tenant code', index=True )
	tenant_name = fields.Char(string='Name', required=True, oldname='descript_name', help="Descriptive name of the tenant")
	qadm_password = fields.Char(help="Password for qadm@upn user")
	qtest_password = fields.Char()
	upn = fields.Char()
	ip = fields.Char(string='DC IP', help='Datacenter IP range')
	is_telephony=fields.Boolean()
	is_citrix=fields.Boolean()
	is_mailonly=fields.Boolean()
	is_qfilteronly=fields.Boolean()
	pbx_password=fields.Char(string="Pbx password")
	ip_ids=fields.One2many('lubon_qlan.ip','tenant_id')
	vlan_ids=fields.One2many('lubon_qlan.vlan','tenant_id')
	contract_ids=fields.Many2many('account.analytic.account', String="Contracts")
	adaccounts_ids=fields.One2many('lubon_qlan.adaccounts', 'tenant_id')
	assets_ids=fields.One2many('lubon_qlan.assets', 'tenant_id')

	credential_ids=fields.One2many('lubon_credentials.credentials','tenant_id')

	filemaker_site_id=fields.Char(string='Filemaker site')
	validcustomers_ids=fields.Many2many('res.partner', string="Customers", compute="_getvalidcustomer_ids")
	main_contact=fields.Many2one('res.partner', string="Main contact", domain="[['type','=','contact'],['is_company','=',False]]")
	tel_dedicated=fields.Char(string='Incoming tel',help="Number that is dedicated to the customer, with respect to SLA")
#	qlan_adaccounts_import_ids=fields.One2many('lubon_qlan_adaccounts_import','tenant')
	def _getvalidcustomer_ids(self):
		for rec in self.contract_ids:
			self.validcustomers_ids=self.validcustomers_ids + rec.partner_id

class lubon_qlan_adaccounts(models.Model):
	_name='lubon_qlan.adaccounts'
	_sql_constraints = [('guid_unique','UNIQUE(objectguid)','objectguid has to be unique')]
	name=fields.Char()
	samaccountname=fields.Char()
	logonname=fields.Char()
	product=fields.Char()
	objectguid=fields.Char(required=True)
	date_first=fields.Datetime(help="Date of first import")
	date_last=fields.Datetime(help="Date last seen")
	ad_enabled=fields.Boolean(string="Enabled",default=True)
	tenant_id=fields.Many2one('lubon_qlan.tenants') #, required=True)
	person_id=fields.Many2one('res.partner', string="Related person")

	validcustomers_ids=fields.Many2many('res.partner', compute='_getvalidcustomer_ids',)

	@api.onchange('tenant_id')
	@api.one
	def _getvalidcustomer_ids(self):
		self.validcustomers_ids=self.tenant_id.validcustomers_ids

	@api.onchange('person_id')
	@api.one
	def _getpersonname(self):
		self.name=self.person_id.name

class lubon_qlan_adaccounts_import(models.TransientModel):
	_name='lubon_qlan.adaccounts_import'
	importref=fields.Char(help="Reference to the import")
	processed=fields.Boolean(default=False)
	samaccountname=fields.Char(required=True)
	logonname=fields.Char()
	tenant=fields.Char()
	product=fields.Char()
	smspasscode=fields.Char()
	exchange=fields.Char()
	citrix=fields.Char()
	rdp=fields.Char()
	office=fields.Char()
	msofficestd=fields.Char()
	msofficeproplus=fields.Char()
	msexchstd=fields.Char()
	msexchplus=fields.Char()
	enabled=fields.Boolean()
	objectguid=fields.Char()
	def schedule_import(self, cr, user, context={}):
		self.importadaccounts(self)
	
	@api.multi
 	def importadaccounts(self): # , cr=None, uid=None, context=None, arg5=None):
		logger.info('Importing ad accounts')
		table_import=self.env['lubon_qlan.adaccounts_import']
		basepath=expanduser("~")
		basepath +='/odoo-imports/adaccounts'
		destpath=basepath + '/hist'
		p = path(basepath)
		for f in p.files(pattern='Daily-2*.csv'):
			
			s=f.stripext().basename().lstrip('Daily-')
			logger.info('Processing file: ' + f.name)
			fi = open(f, 'rb')
			data = fi.read()
			fi.close()
			fo = open(basepath + '/Daily-clean.csv', 'wb')
			fo.write(data.replace('\x00', ''))
			fo.close()


			with open (basepath + '/Daily-clean.csv', 'rb') as cleanfile:
				reader = csv.DictReader(cleanfile, delimiter=';')
				for row in reader:
	#					print (s, row['Samaccountname'],row['Displayname'],row['Tenant-01'],row['Qlan Product-9'],row['enabled'])
					table_import.create({'importref':s, 
					'samaccountname':row['Samaccountname'],
					'logonname':row['userprincipalname'],
					'tenant':row['Tenant-01'].upper(),
					'product':row['Qlan Product-9'],
					'smspasscode':row['SMS Passcode-8'],
					'exchange':row['Exchange-10'],
					'citrix':row['Citrix-11'],
					'rdp':row['RDP-12'],
					'office':row['Office-13'],
					'msofficestd':row['MS Office STD'],
					'msofficeproplus':row['MS Office ProPlus'],
					'msexchstd':row['MS Exch Std'],
					'msexchplus':row['MS Exch Plus'],
					'enabled':row['enabled'],
					'objectguid':row['objectguid'],
					}).process_import()
				cleanfile.close()
				q=path(f)
				q.move(destpath)
		
	@api.one		
	def process_import(self):
		
		table_accounts=self.env['lubon_qlan.adaccounts']
		account=table_accounts.search([('objectguid', '=', self.objectguid)])
		if not account:
			account=table_accounts.create({'objectguid': self.objectguid,
											'date_first': datetime.datetime.now(),
											})

		account.update({'samaccountname': self.samaccountname,
						'logonname': self.logonname,	
						'date_last':datetime.datetime.now(),
						'product': self.product,
						'tenant_id': self.env['lubon_qlan.tenants'].search([('code','=', self.tenant)])
						})






class lubon_qlan_vlan(models.Model):
	_name='lubon_qlan.vlan'
	name=fields.Char(required=True)
	sequence=fields.Integer()
	vlan_tag=fields.Integer(required=True)
	ipv4=fields.Char(string="IPv4 Net name")
	ipv4_net=fields.Char(string="IPv4 Net")
	ipv4_mask=fields.Selection([("32","/32"),("30","/30"),("29","/29"),("28","/28"),("27","/27"),("26","/26"),("25","/25"),("24","/24"),("16","/16"),("12","/12"),("8","/8")])
	ipv6=fields.Char(string="IPv6 Net")
	ipv4_gw=fields.Char(string="IPv4 GW")
	ipv4_dhcp=fields.Char(string="IPv4 DHCP server")
	ipv6_gw=fields.Char(string="IPv6 GW")
	dns=fields.Char(string="DNS",help="DNS Servers, comma separated")
	site_id=fields.Many2one('lubon_qlan.sites')
	tenant_id=fields.Many2one('lubon_qlan.tenants')
	ip_ids=fields.One2many('lubon_qlan.ip','site_id')

	@api.one
	@api.onchange('ipv4_net','ipv4_mask')
	def calculate_ipv4(self):
		if self.ipv4_net and self.ipv4_mask:
			self.ipv4=self.ipv4_net + '/' + self.ipv4_mask
	@api.multi
	def name_get(self):
		res=[]
		for line in self:
			text=''
			if line.name:
				text=line.name
			if line.vlan_tag:
				text+='(' + str(line.vlan_tag) + ')'
			res.append((line.id,text ))
		return res 	

class lubon_qlan_ip(models.Model):
	_name='lubon_qlan.ip'
	
	name=fields.Char(string="IP Address", help="Auto calculated, do not modify")
	vlan_id=fields.Many2one('lubon_qlan.vlan', string="Vlan", help="Vlan this IP address belongs to") 
	mac=fields.Char(help="Mac Address")
	ip_type=fields.Selection([("fixed","Fixed"),("dhcp","DHCP Reservation")])
	ip=fields.Integer(string="Host Address", help="Host part of the IP Address")
	tenant_id=fields.Many2one('lubon_qlan.tenants', help="Optional tenant this ip belongs to")
	asset_id=fields.Many2one('lubon_qlan.assets')
	site_id=fields.Many2one('lubon_qlan.sites')
	memberships_id=fields.Many2one('lubon_qlan.memberships', string="Membership", help="Description of vlan membership")
	interface_id=fields.Many2one('lubon_qlan.interfaces', help="Interface this ip belongs to.")
	@api.onchange('memberships_id')
	@api.multi
	def compute_related_fields(self):
		vlan_id=self.memberships_id.vlan_id
		site_id=self.memberships_id.vlan_id.site_id

	@api.onchange('ip')
	def _compute_name(self):
		#pdb.set_trace()
		if not (self.ip):
			self.name=""
		else:
			if self.vlan_id:
				if  (not self.vlan_id.ipv4_net):
					raise exceptions.Warning(
						_("VLAN '%s' is not properly configured ") % self.vlan_id.name)
				else:
					self.name=self.vlan_id.ipv4_net + '.' +str(self.ip)

class lubon_qlan_isp(models.Model):
	_name='lubon_qlan.isp'
	name=fields.Char(string="Provider")
	ip_type=fields.Selection([("fixed","Fixed"),("var","variable")])
	ip_address=fields.Char(string="WAN ip")
	ip_login=fields.Char(help="Login to establish connection")
	ip_password=fields.Char(help="Password to establish connection")
	ip_dns=fields.Char(help="Dynamic dns entry")
	ip_dns_reverse=fields.Char(string="Reverse dns")
	account=fields.Char(string="ISP account n°",help="Account number @ ISP")
	account_login=fields.Char(help="ISP controlpanel login")
	account_password=fields.Char()
	site_id=fields.Many2one('lubon_qlan.sites')
	tenant_id=fields.Many2one('lubon_qlan.tenants')


class lubon_qlan_credentials(models.Model):
	_inherit='lubon_credentials.credentials'
	site_id=fields.Many2one('lubon_qlan.sites')
	tenant_id=fields.Many2one('lubon_qlan.tenants')
	asset_id=fields.Many2one('lubon_qlan.assets')


class lubon_qlan_sites(models.Model):
	_name='lubon_qlan.sites'
	_inherit='pad.common'
	name=fields.Char(string="Site name")
	alfacode=fields.Char(string="Site Code")
	filemaker_site_id=fields.Char(string='Filemaker site')
	partner_id=fields.Many2one('res.partner', string="Address", domain="[('is_company','=',True)]")
	code=fields.Char()
	ipv4=fields.Char(string="IPv4 net")
	ipv6=fields.Char(string="IPv6 net")
	ssid_private=fields.Char(string="Private SSID", help="SSID for use by employees")
	ssid_public=fields.Char(string="Public SSID", help="SSID for use by guests")
	wifikey_private=fields.Char(string="Private key", help="Key private network")
	wifikey_public=fields.Char(string="Public key", help="Key public network")

	vlan_ids=fields.One2many('lubon_qlan.vlan','site_id')
	isp_ids=fields.One2many('lubon_qlan.isp','site_id')
	ip_ids=fields.One2many('lubon_qlan.ip','site_id')
	credential_ids=fields.One2many('lubon_credentials.credentials','site_id')
	main_contact=fields.Many2one('res.partner', string="Main contact", domain="[['type','=','contact'],['is_company','=',False]]")
	contract_ids=fields.Many2many('account.analytic.account', String="Contracts")
	location_ids=fields.One2many('stock.location', 'site_id')
	asset_ids=fields.One2many('lubon_qlan.assets','site_id')
	notes=fields.Html()
	site_pad=fields.Char(pad_content_field='notes')
	
	@api.one
	def _vlan_count(self):
		self.vlan_count=len(self.vlan_ids)
	vlan_count=fields.Integer(compute=_vlan_count)
	@api.one
	def _assets_count(self):
		self.assets_count=len(self.asset_ids)
	assets_count=fields.Integer(compute=_assets_count)
	@api.one
	def _ip_count(self):
		self.ip_count=len(self.ip_ids)
	ip_count=fields.Integer(compute=_ip_count)


	@api.multi
	def search_quants(self):
		
		model_data_obj = self.env['ir.model.data']
		context = self.env.context.copy()
		model_datas = model_data_obj.search(
        	[('model', '=', 'ir.ui.view'),
        	('name', '=', 'lubon_qlan_add_quants_wizard')])
		line_obj = self.env['stock.quant']
		location_ids=[]
		for l in self.env['lubon_qlan.sites'].browse(context['active_site_id']).location_ids:
			location_ids.append(l.id) 
		search_domain=[('location_id', 'in', location_ids)]
		quants=line_obj.search(search_domain)
		quant_ids=[]
		for q in quants:
			quant_ids.append(q.id)
		context['line_ids']=quant_ids 	
		return {'name': _('Asset candidates'),'context': context,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'add_quant_to_site.wizard',
			'views': [(model_datas[0].res_id, 'form')],
			'type': 'ir.actions.act_window',
			'target': 'new',
			}
		# line_obj = self.env['account.move.line']

  #       model_data_obj = self.env['ir.model.data']
  #       payment = self.env['payment.order'].browse(
  #           self.env.context['active_id'])
  #       domain = [('move_id.state', '=', 'posted'),
  #                 ('reconcile_id', '=', False),
  #                 ('company_id', '=', payment.mode.company_id.id),
  #                 '|',
  #                 ('date_maturity', '<=', self.duedate),
  #                 ('date_maturity', '=', False)]
  #       self.extend_payment_order_domain(payment, domain)
  #       lines = line_obj.search(domain)
  #       context = self.env.context.copy()
  #       context['line_ids'] = self.filter_lines(lines)
  #       context['populate_results'] = self.populate_results
  #       if payment.payment_order_type == 'payment':
  #           context['display_credit'] = True
  #           context['display_debit'] = False
  #       else:
  #           context['display_credit'] = False
  #           context['display_debit'] = True
        
  #       model_datas = model_data_obj.search(
  #       	[('model', '=', 'ir.ui.view'),
  #       	('name', '=', 'lubon_qlan_add_quants_wizard')])   
        
  #       return {'name': _('Asset candidates'),'context': context,
  #       'view_type': 'form',
  #       'view_mode': 'form',
  #       'res_model': 'add_quant_to_site.wizard',
  #       'views': [(model_datas[0].res_id, 'form')],
  #       'type': 'ir.actions.act_window',
  #       'target': 'new',
  #       }



class stock_location(models.Model):
	_inherit="stock.location"
	site_id=fields.Many2one('lubon_qlan.sites')

class stock_quant(models.Model):
	_inherit="stock.quant"
	@api.one
	def addtosite(self):
		pdb.set_trace()

	
class lubon_qlan_assets(models.Model):
#	_inherits={'stock.quant': 'quant_id'}
	_name="lubon_qlan.assets"
	_rec_name="asset_name"
	parent_id=fields.Many2one('lubon_qlan.assets', string="Part of")

	child_ids=fields.One2many('lubon_qlan.assets','parent_id')
	is_container=fields.Boolean(string="Container", help="Can contain other devices")
	show_in_site=fields.Boolean(string="Show", help="Show in sites", default=True)
	quant_id=fields.Many2one('stock.quant')
	product_id=fields.Many2one('product.product')
	site_id=fields.Many2one('lubon_qlan.sites', required=True, help="Readonly if part of another eqpt or has parts.")
	tenant_id=fields.Many2one('lubon_qlan.tenants', string="Tenant")
	asset_name=fields.Char(required=True)
	asset_type=fields.Selection([('switch','switch'),('server','server'),('firewall','firewall')])
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






class lubon_qlan_interfaces(models.Model):
#	_inherits={'stock.quant': 'quant_id'}
	_name="lubon_qlan.interfaces"
	_order="name"
	name=fields.Char(required=True, help="eth=Ethernet, gi=Gigabit, Fi=Fiber, pwr=power")
#	display_name=fields.Char()
	sequence=fields.Integer()
	asset_id=fields.Many2one('lubon_qlan.assets')
	connected_to=fields.Many2one('lubon_qlan.interfaces',domain="[('site_id','=',parent.site_id)]")
	site_id=fields.Many2one('lubon_qlan.sites',required=True) 
	memberships_ids=fields.One2many('lubon_qlan.memberships','interface_id')
	mac=fields.Char()
	interface_type_id=fields.Many2one("lubon_qlan.interface_type", string="Type")
	
	@api.one
	@api.onchange('name')
	def compute_display_name(self):
		self.display_name=self.asset_id.asset_name 
		if self.name:
			self.display_name += "/" + self.name 
	@api.one
	@api.onchange('asset_id')
	def compute_site_id(self):
		#pdb.set_trace()
		self.site_id=self.asset_id.site_id
		return self.asset_id.site_id

	@api.one
#	@api.onchange('memberships_ids')
	def compute_vlan_string(self):
		vlan_string=""
		for m in self.memberships_ids:
			if vlan_string:
				vlan_string+= ","
			vlan_string+= str(m.vlan_id.vlan_tag) 
			if m.member_type == 'u':
				vlan_string+='(u)' 
		#pdb.set_trace()	
		self.vlan_string=vlan_string

	vlan_string=fields.Char(string="Vlan", compute="compute_vlan_string")

	@api.multi
	def name_get(self):
		#pdb.set_trace()
		res=[]
		for line in self:
			text=''
			if line.asset_id.asset_name:
				text=line.asset_id.asset_name + '/'
			if line.name:
				text+=line.name
			res.append((line.id,text ))
		return res 		
	
	@api.one
	@api.onchange('connected_to')
	def set_connected_to(self):
		#self.connected_to.connected_to=self.env.context['interface_id']
		if 'interface_id' in self.env.context.keys():
			if self.connected_to:
				other_itf=self.env['lubon_qlan.interfaces'].browse(self.connected_to.id)
				other_itf.write({'connected_to': self.env.context['interface_id']})
			else:
				other_itf=self.env['lubon_qlan.interfaces'].browse(self.env.context['interface_id']).connected_to
				other_itf.write({'connected_to': False})
#		pdb.set_trace()

class lubon_qlan_interface_type(models.Model):
	_name="lubon_qlan.interface_type"
	name=fields.Char()

class lubon_qlan_memberships(models.Model):
#	_inherits={'stock.quant': 'quant_id'}
	_name="lubon_qlan.memberships"
	
	name=fields.Char()
	display_name=fields.Char()
	interface_id=fields.Many2one('lubon_qlan.interfaces', string="Interface")
	vlan_id=fields.Many2one('lubon_qlan.vlan', string="Vlan")
	ip_ids=fields.One2many('lubon_qlan.ip','memberships_id')
	member_type=fields.Selection([('u','Untagged'),('t','Tagged')], default='u', required=True)
	site_id=fields.Many2one('lubon_qlan.sites', required=True)
	asset_id=fields.Many2one('lubon_qlan.assets')

	@api.onchange('vlan_id','interface_id','member_type')
	@api.one
	def _compute_name(self):
		name=""
		if self.interface_id.name:
			name= name + self.interface_id.name +  "/"
		if 	self.vlan_id.name:
			name= name + self.vlan_id.name
		self.name=name + '('+self.member_type+')'
		self.display_name=self.interface_id.asset_id.asset_name  +  "/" + name 
		

class add_quant_to_site_wizard(models.TransientModel):
	_name="add_quant_to_site.wizard"
	entries=fields.Char()
	@api.model
	def default_get(self, field_list):
		res = super(add_quant_to_site_wizard, self).default_get(field_list)
		context=self.env.context
		if ('entries' in field_list and context.get('line_ids')):
			res.update({'entries': context['line_ids']})
		#pdb.set_trace()
		return res

	def _default_site(self):
#		pdb.set_trace() 
		return self.env['lubon_qlan.sites'].browse(self.env['lubon_qlan.sites']._context.get('active_id')).id
	site_id=fields.Many2one('lubon_qlan.sites', default=_default_site)

	def _default_location_ids(self):
		return self.env['lubon_qlan.sites'].browse(self._context.get('active_id')).location_ids

	location_ids=fields.One2many('stock.location', 'site_id')

	def _default_quant_ids(self):
		location_ids=[]
		for l in self.env['lubon_qlan.sites'].browse(self._context.get('active_id')).location_ids:
			location_ids.append(l.id) 
		search_domain=[('location_id', 'in', location_ids)]
		#self.location_ids=self.env['lubon_qlan.sites'].browse(self._context.get('active_id')).location_ids
		return self.env['stock.quant'].search(search_domain)

	quant_ids=fields.Many2many('stock.quant')
	@api.one
	def add_quants_to_site(self):
		for q in self.quant_ids:
			self.env['lubon_qlan.assets'].new_asset(self.site_id,q)

class add_interfaces_to_asset_wizard(models.TransientModel):
	_name="add_interfaces_to_asset.wizard"
	assets_id=fields.Many2one("lubon_qlan.assets")
	start=fields.Char(String="Start string", placeholder="eth", help="eth=Ethernet, gi=Gigabit, Fi=Fiber, pwr=power")
	number=fields.Integer(String="Number", help="Number of interfaces", default=1)
	start_number=fields.Integer(String="Start Number", help="Number of interfaces", default=1)
	width=fields.Integer(String="Number width", placeholder="2")
	fill=fields.Char(String="Fill character", default="0")
	interface_type_id=fields.Many2one("lubon_qlan.interface_type", string="Type", required="True")
	@api.one
	@api.onchange('number')
	def calculate_width(self):
		self.width=1
		if self.number + self.start_number > 9:
			self.width=2
	@api.one
	def add_interfaces_to_assets(self):
		for x in xrange(self.start_number, self.start_number +  self.number):
			appendix=str(x)
			while len(appendix)<self.width:
				appendix=str(self.fill)+appendix
			name=str(self.start) + appendix
			self.env['lubon_qlan.interfaces'].create({
				'asset_id': self.assets_id.id,
				'name': name,
				'site_id': self.assets_id.site_id.id,
				'interface_type_id': self.interface_type_id.id,
				})
			
