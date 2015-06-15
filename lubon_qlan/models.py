# -*- coding: utf-8 -*-

from openerp import models, fields, api

class lubon_qlan_tenants(models.Model):
	_name = 'lubon_qlan.tenants'
	_rec_name = 'code'
	_sql_constraints = [('code_unique','UNIQUE(code)','Code has to be unique')]
	code = fields.Char(oldname='name', required=True, help='Tenant code')
	tenant_name = fields.Char(string='Name', required=True, oldname='descript_name', help="Descriptive name of the tenant")
	qadm_password = fields.Char(help="Password for qadm@upn user")
	qtest_password = fields.Char()
	upn = fields.Char()
	ip = fields.Char(string='DC IP', help='Datacenter IP range')
	is_telephony=fields.Boolean()
	pbx_password=fields.Char(string="Pbx password")
       	ip_ids=fields.One2many('lubon_qlan.ip','tenant_id')
        vlan_ids=fields.One2many('lubon_qlan.vlan','tenant_id')
	contract_ids=fields.Many2many('account.analytic.account', String="Contracts")
	adaccounts_ids=fields.One2many('lubon_qlan.adaccounts', 'tenant_id')
        credential_ids=fields.One2many('lubon_credentials.credentials','tenant_id')
	filemaker_site_id=fields.Char(string='Filemaker site')
	validcustomers_ids=fields.Many2many('res.partner', string="Customers", compute="_getvalidcustomer_ids")
        main_contact=fields.Many2one('res.partner', string="Main contact", domain="[['type','=','contact'],['is_company','=',False]]")
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
        vlan_id=fields.Many2one('lubon_qlan.vlan') #, domain="[['site_id','=',site_id]]")
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
	quant_ids=fields.One2many('stock.quant','site_id')


class stock_location(models.Model):
        _inherit="stock.location"
        site_id=fields.Many2one('lubon_qlan.sites')

class stock_quant(models.Model):
	_inherit="stock.quant"
        site_id=fields.Many2one('lubon_qlan.sites')

        @api.onchange('location_id')
#	@api.one
        def _get_site_id(self):
		self.site_id=self.location_id.site_id
