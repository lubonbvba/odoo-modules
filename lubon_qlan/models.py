# -*- coding: utf-8 -*-

from openerp import models, fields, api,_
import csv,os,string
from path import path
import pdb


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
	_sql_constraints = [('name_unique','UNIQUE(name)','Name has to be unique')]
	name=fields.Char(required=True)
	samaccountname=fields.Char()
	logonname=fields.Char()

	ad_enabled=fields.Boolean(string="Enabled",default=True)
	tenant_id=fields.Many2one('lubon_qlan.tenants', required=True)
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
	def schedule_import(self, cr, user, context={}):
		self.importadaccounts(self)
	@api.one
	def importadaccounts(self, cr=None, uid=None, context=None, arg5=None):
		table_import=self.env['lubon_qlan.adaccounts_import']
		basepath='/mnt/general/odoo/adaccounts'
		destpath=basepath + '/hist'
		p = path(basepath)
		for f in p.files(pattern='Daily-2*.csv'):
			s=f.stripext().basename().lstrip('Daily-')
			fi = open(f, 'rb')
			data = fi.read()
			fi.close()
			fo = open('/mnt/general/odoo/adaccounts/Daily-clean.csv', 'wb')
			fo.write(data.replace('\x00', ''))
			fo.close()


			with open ('/mnt/general/odoo/adaccounts/Daily-clean.csv', 'rb') as cleanfile:
				reader = csv.DictReader(cleanfile, delimiter=';')
				for row in reader:
	#					print (s, row['Samaccountname'],row['Displayname'],row['Tenant-01'],row['Qlan Product-9'],row['enabled'])
					table_import.create({'importref':s, 
					'samaccountname':row['Samaccountname'],
					'logonname':row['userprincipalname'],
					'tenant':row['Tenant-01'],
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
					})
				cleanfile.close()
				q=path(f)
				q.move(destpath)




class lubon_qlan_vlan(models.Model):
	_name='lubon_qlan.vlan'
	name=fields.Char()
	sequence=fields.Integer()
	vlan_tag=fields.Integer()
	ipv4=fields.Char(string="IPv4 Net")
	ipv6=fields.Char(string="IPv6 Net")
	ipv4_gw=fields.Char(string="IPv4 GW")
	ipv6_gw=fields.Char(string="IPv6 GW")
	dns=fields.Char(string="DNS",help="DNS Servers, comma separated")
	site_id=fields.Many2one('lubon_qlan.sites')
	tenant_id=fields.Many2one('lubon_qlan.tenants')
	ip_ids=fields.One2many('lubon_qlan.ip','site_id')


class lubon_qlan_ip(models.Model):
	_name='lubon_qlan.ip'
	name=fields.Char()
	vlan_id=fields.Many2one('lubon_qlan.vlan') 
	mac=fields.Char()
	ip_type=fields.Selection([("fixed","Fixed"),("dhcp","DHCP Reservation")])
	ip=fields.Integer()
	site_id=fields.Many2one('lubon_qlan.sites')
	tenant_id=fields.Many2one('lubon_qlan.tenants')




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


class lubon_qlan_sites(models.Model):
	_name='lubon_qlan.sites'
	name=fields.Char(string="Site name")
	alfacode=fields.Char(string="Site Code")
	filemaker_site_id=fields.Char(string='Filemaker site')
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

	@api.one
#	@api.returns('ir.actions.act_window')
	def show_site_quantszz(self):
		mod_obj=self.env['ir.model.data'].search([('name', '=', 'lubon_qlan_show_quants')])
		action=self.env['ir.actions.act_window'].search([('name', '=', 'SiteAssets001')])
		action.name=_('Site quants')
		pdb.set_trace()
		result={
		'name': action.name,
		'type': action.type,
		'view_type': action.view_type,
		'view_mode': action.view_mode,
		'res_model': action.res_model,
		'views': action.views,
		'view_id': action.view_id.id,
		'target': 'new',
		'context': None,
		}
		pdb.set_trace()
		return result
	#		return action

	def show_site_quants(self, cr, uid, ids, context=None):
		data = self.read(cr, uid, ids, context=context)[0]
			# Create an invoice based on selected timesheet lines
		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')
		mod_ids = mod_obj.search(cr, uid, [('name', '=', 'lubon_qlan_show_quants')], context=context)
		res_id = mod_obj.read(cr, uid, mod_ids, ['res_id'], context=context)[0]['res_id']
		act_win = act_obj.read(cr, uid, [res_id], context=context)[0]
		act_win['domain'] = [('location_id', 'in', data['location_ids'])]
		act_win['name'] = _('Site quants')
		return act_win


class stock_location(models.Model):
	_inherit="stock.location"
	site_id=fields.Many2one('lubon_qlan.sites')


class lubon_qlan_assets(models.Model):
	_inherits={'stock.quant': 'quant_id'}
	_name="lubon_qlan.assets"
	quant_id=fields.Many2one('stock.quant', required=True, ondelete="cascade")
	site_id=fields.Many2one('lubon_qlan.sites')
	asset_name=fields.Char()
        #@api.onchange('location_id')
#	@api.one
        #def _get_site_id(self):
		#self.site_id=self.location_id.site_id
