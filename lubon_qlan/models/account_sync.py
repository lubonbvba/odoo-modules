# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api,exceptions, _
from datetime import datetime,timedelta
from passgen import passgen
import re
import pdb,logging
#from path import path
logger = logging.getLogger(__name__)

ad_allusers_command="get-aduser -filter * -properties * "
ad_singleuser_command="get-aduser -server q01dc003.q.lan -properties * -identity "
ad_allgroups_command="get-adgroup -filter * -properties * "
ad_output_modifier=" | select-object * | convertto-json"

o365_allusers_command=""

class lubon_qlan_account_source_type(models.Model):
	_name = 'lubon_qlan.account_source_type'
	_description = "Account source type"
	name=fields.Char()
	single_tenant=fields.Boolean()


class lubon_qlan_account_source(models.Model):
	_name = 'lubon_qlan.account_source'
	_description = "Account source"
	name=fields.Char(required=True)
	account_source_type_id=fields.Many2one('lubon_qlan.account_source_type', string='Account Type')
	tenant_id=fields.Many2one('lubon_qlan.tenants', string="Tenant")
	command_id=fields.Many2one('cmd_execute.command', string="Command")
	endpoints_id=fields.Many2one('cmd_execute.endpoints', string="Endpoint")
#	command_options=fields.Char()
	include_in_schedule=fields.Boolean()
	adaccount_ids=fields.One2many('lubon_qlan.adaccounts','account_source_id')
	adusers_ids=fields.One2many('lubon_qlan.adusers','account_source_id')
	adgroups_ids=fields.One2many('lubon_qlan.adgroups','account_source_id')
	last_full_run_start=fields.Datetime()
	last_full_run_stop=fields.Datetime()
	credential_id=fields.Many2one('lubon_credentials.credentials',  string='credential' , help="Credential to be used on the service, eg office 365")
	tenant_command=fields.Text(help="Command used to get all tenants", default="get-aduser -filter * -properties * | select-object * | convertto-json")
	user_command=fields.Text(help="Command used to get all users", default="get-aduser -filter * -properties * | select-object * | convertto-json")
	group_command=fields.Text(help="Command used to get all groups", default="get-adgroup -filter * -properties * | select-object * | convertto-json")

	@api.onchange('tenant_id','account_source_type_id')
	def _set_name(self):
		for source in self:
			self.name=self.tenant_id.code or " " 
			self.name += " - "
			self.name += self.account_source_type_id.name or " "

	@api.multi
 	def cron_scheduler(self,dummy=None):
 		sources=self.search([('include_in_schedule',"=",True)])
 		for source in sources:
 			source.run_sync()
 			

 	@api.multi
 	def run_sync(self):
# 		cmd=self.command_id.ps_command_line
#		if self.command_options:
# 			cmd += " " + self.command_options
		logger.info("Run_sync: Start Full sync %s" % self.name)
 		self.last_full_run_start=fields.Datetime.now()
 		#Account source type = Windows
 		if (self.account_source_type_id.id == self.env.ref('lubon_qlan.ast_windows').id):
			logger.info("Run_sync: Retrieving groups")
 			result=self.endpoints_id.execute(ad_allgroups_command + ad_output_modifier)
 			logger.info("Run_sync: Processing groups")
 			ids=(self.sync_object_level(result,'group',self.env['lubon_qlan.adgroups']))
			logger.info("Run_sync: Retrieving users")
 			result=self.endpoints_id.execute(ad_allusers_command + ad_output_modifier)
 			logger.info("Run_sync: Processing users")
 			ids += self.sync_object_level(result,'user',self.env['lubon_qlan.adusers'])
 			logger.info("Run_sync: Processing obsoletes")
  			self.check_obsolete_accounts(ids)
  		#Account source type = O365	
 		if (self.account_source_type_id.id == self.env.ref('lubon_qlan.ast_o365').id):
 			pdb.set_trace()

  		self.last_full_run_stop=fields.Datetime.now()
 		logger.info("Run_sync: End Full sync %s" % self.name) 		

 	@api.multi
 	def run_single_sync(self,identity):
 		command=ad_singleuser_command + identity + ad_output_modifier
 		result=self.endpoints_id.execute(command)
 		#pdb.set_trace()
 		self.sync_object_level([result],'user',self.env['lubon_qlan.adusers'])



 	@api.multi
 	def sync_object_level(self,objects,objtype,obj):
 		ids=[]
 		groups2update=self.env['lubon_qlan.adaccounts']
  		for items in objects:
 			item={}
 			for keys in items:
 				item[keys.lower()]=items[keys]
 			ids.append(item['objectguid'])
 			adaccount=obj.search([('objectguid','=',item['objectguid'])])
 
 			if not adaccount:
	 			parent_account=self.env['lubon_qlan.adaccounts'].search([('objectguid','=',item['objectguid'])])
 				if parent_account:
	 				adaccount=obj.create({
	 					'objectguid': item['objectguid'],
	 					'date_first':fields.Datetime.now(),
	 					'account_id':parent_account.id,
 					})
 				else:
	 				adaccount=obj.create({
	 					'objectguid': item['objectguid'],
	 					'date_first':fields.Datetime.now(),
 					})
 			adaccount.distinguishedname=item['distinguishedname']
			adaccount.date_last=fields.Datetime.now()
			adaccount.account_source_id=self.id
 			adaccount.account_created=True
 			adaccount.displayname=item['displayname']
 			adaccount.name=item['name']
 			if 'extensionattribute1' in item.keys():
				adaccount.tenant_id=self.env['lubon_qlan.tenants'].search([('code','=', item['extensionattribute1'].upper())])
			adaccount.tenant_id = adaccount.tenant_id or self.tenant_id
 			adaccount.account_id.checkmailaddresses(self.returnkeyvalue(item,'proxyaddresses'))


 			if objtype=='user':
 				adaccount.mail=self.returnkeyvalue(item,'mail')
 	 			adaccount.product=self.returnkeyvalue(item,'extensionattribute9')	
	 			adaccount.legacyexchangedn=self.returnkeyvalue(item,'legacyexchangedn')	
	 			adaccount.mailnickname=self.returnkeyvalue(item,'mailnickname')	
	 			adaccount.targetaddress=self.returnkeyvalue(item,'targetaddress')	
	 			adaccount.mobile=self.returnkeyvalue(item,'mobile')	
	 			adaccount.last_name=self.returnkeyvalue(item,'sn')	
	 			adaccount.first_name=self.returnkeyvalue(item,'givenname')	
	 			adaccount.scriptpath=self.returnkeyvalue(item,'scriptpath')	
	 			adaccount.samaccountname=item['samaccountname']	
	 			adaccount.ad_enabled=item['enabled']
	 			adaccount.ad_lockedout=item['lockedout']
	 			adaccount.logonname=item['userprincipalname']
	 			adaccount.ad_date_created=self._calcwin32epoch(item['createtimestamp'])

				#if 'LastLogonDate' in item.keys():
					#adaccount.last_logon=self._calcwin32epoch(item['LastLogonDate'])
				#pdb.set_trace()
				if 'lastlogon' in item.keys():
					#adaccount.last_logon=fields.Datetime.to_string(datetime(1601,1,1) + timedelta(seconds=item['lastLogon']/1e7))
					last=datetime(1601,1,1) + timedelta(seconds=item['lastlogon']/1e7)
					if last.year > 1900:
						adaccount.last_logon=datetime(1601,1,1) + timedelta(seconds=item['lastlogon']/1e7)
				if not adaccount.person_id:
					partner=self.env['res.partner'].search([('email','ilike',adaccount.logonname)])
					#pdb.set_trace()
					if len(partner)==1:
						adaccount.person_id=partner
			if str(item['memberof']) != adaccount.memberofstring:
				logger.info("sync_object_level: Processing group membership: %s" % item['samaccountname'])
				adaccount.memberofstring=item['memberof']
				groups=[]
				for group in item['memberof']:
					g=self.env['lubon_qlan.adaccounts'].search([('distinguishedname',"=",group),('account_created','=',True)])
					if g:
						if len(g)>1:
							logger.error('Multiple groups found %s') % item['samaccountname']
						groups.append(g.id)

				if len(groups)>0:
					adaccount.account_id.write({'memberof':[(6, 0, groups)]})
					groups2update = groups2update + adaccount.account_id.memberof
					#pdb.set_trace()
				else:
					adaccount.account_id.write({'memberof':[(5, 0, 0)]})
	 		if objtype=='group':
	 			adaccount.membercount=len(adaccount.members)
			
		for g in groups2update:
			g.membercount=len(g.members)

		return ids

	def returnkeyvalue(self,dict,key):
		if key in dict.keys():
			return dict[key]
		else:
			return False

	def check_obsolete_accounts(self,ids):				
		#pdb.set_trace()
		for account in self.adaccount_ids:
			#a=None
			#a=next((item for item in result if item["ObjectGUID"] == account.objectguid),False)
			if not account.objectguid in ids:
				account.account_created=False
				account.ad_enabled=False

	def _calcwin32epoch(self,timestamp):
		if timestamp:
			timestamp=int(re.findall('\d+', timestamp)[0])
		else:
			return None
		t=datetime(1970,1,1) + timedelta(seconds=timestamp/1e3)
		if t.year > 1900:
			result=t
		else: 
			result=datetime(1999,12,31)
		#pdb.set_trace()
		return result

	@api.multi	
	def get_tenants(self):
		#Office 365
		if (self.account_source_type_id.id == self.env.ref('lubon_qlan.ast_o365').id):
			self.env['lubon_qlan.tenants_o365'].refresh_tenants_o365(self)



class lubon_qlan_skus_o365(models.Model):
	_name = 'lubon_qlan.skus_o365'
	_description = 'Office 365 sku names'
	_rec_name='Service_plan_name'

	product_display_name=fields.Char()
	string_id=fields.Char()
	GUID=fields.Char()
	Service_plan_name=fields.Char()
	service_plan_id=fields.Char()
	Service_plan_included_friendly_names=fields.Char()

class lubon_qlan_users_licenses_o365(models.Model):
	_name = 'lubon_qlan.users_licenses_o365'
	_description = 'MS 365 user assigned skus'	
	user_o365_id = fields.Many2one('lubon_qlan.users_o365', ondelete='cascade')
	subscribedskus_o365 = fields.Many2one('lubon_qlan.subscribedskus_o365',ondelete='cascade')
	

	@api.multi
	def refresh(self,user_id,graphresult):
		if not graphresult:
			result=user_id.o365_tenant_id.account_source_id.endpoints_id.execute('https://graph.microsoft.com/beta/users/'+ user_id.o365_id,url='https://login.microsoftonline.com/' + user_id.o365_tenant_id.defaultdomainname)
			assignedLicenses=result['assignedLicenses']
		else:
			assignedLicenses=graphresult['assignedLicenses']

		for license in user_id.user_licenses_ids:
			licensefound=False
			for current in assignedLicenses:
				if current['skuId']==license.subscribedskus_o365.skuId:
					licensefound=True
			if not licensefound:
				license.unlink()
		#pdb.set_trace()
		#pdb.set_trace()
		for license in assignedLicenses:
			newsku=self.env['lubon_qlan.subscribedskus_o365'].search([('skuId','=',license['skuId']),('o365_tenant_id','=',user_id.o365_tenant_id.id)])
			if len(newsku)!=1:
				logger.error("Newsku !=1 in refresh")
			activelicense=self.search([('user_o365_id','=',user_id.id),('subscribedskus_o365','=',newsku.id)])
			if not activelicense:
				activelicense=self.create({
					'user_o365_id':user_id.id,
					'subscribedskus_o365': newsku.id
				})
		#pdb.set_trace()

class lubon_qlan_billingconfig_tenant_o365(models.Model):
	_name = 'lubon_qlan.billingconfig_tenant_o365'
	_description = 'Office 365 tenant billing config'
	subscribedskus_o365_id=fields.Many2one('lubon_qlan.subscribedskus_o365',domain="[('invoicable','=',True),('id','in',valid_subscribedskus_o365_ids[0][2])]", required=True)
	o365_tenant_id=fields.Many2one('lubon_qlan.tenants_o365', ondelete='cascade', required=True)
	domains_o365_id=fields.Many2one('lubon_qlan.domains_o365', domain="[('id','in',valid_domains_o365_ids[0][2]),('used_for_billing','=',True)]", required=True)
	qlan_tenant_id=fields.Many2one('lubon_qlan.tenants', ondelete='cascade', required=True)
	contract_line_id=fields.Many2one('account.analytic.invoice.line', domain="[('analytic_account_id','in', valid_contract_ids[0][2])]", zrequired=True)
	
	valid_domains_o365_ids=fields.Many2many('lubon_qlan.domains_o365', compute='_get_valid_domains_o365_ids')
	valid_contract_ids=fields.Many2many('account.analytic.account', compute='_get_valid_contract_ids')
	valid_subscribedskus_o365_ids=fields.Many2many('lubon_qlan.subscribedskus_o365', compute='_get_valid_subscribedskus_o365_ids')

	@api.onchange('o365_tenant_id')
	@api.one
	def _get_valid_subscribedskus_o365_ids(self):
		self.valid_subscribedskus_o365_ids=self.o365_tenant_id.sku_ids
		#pdb.set_trace()
		# 	
	@api.onchange('o365_tenant_id')
	@api.one
	def _get_valid_domains_o365_ids(self):
		self.valid_domains_o365_ids=self.o365_tenant_id.domains_o365_ids
		#pdb.set_trace()
	@api.onchange('qlan_tenant_id')
	@api.one
	def _get_valid_contract_ids(self):
		self.valid_contract_ids=self.qlan_tenant_id.contract_ids
		#pdb.set_trace()



class lubon_qlan_subscribedskus_o365(models.Model):
	_name = 'lubon_qlan.subscribedskus_o365'
	_description = 'Office 365 subscribed skus'
	_rec_name= 'friendly_name'
	o365_tenant_id=fields.Many2one('lubon_qlan.tenants_o365', ondelete='cascade')
	capabilityStatus=fields.Char()
	consumedUnits=fields.Integer()
	o365_id=fields.Char()
	skuId=fields.Char()
	skuPartNumber=fields.Char()
	appliesTo=fields.Char()
	enabled=fields.Integer()
	suspended=fields.Integer()
	warning=fields.Integer()
	friendly_name=fields.Char()
	invoicable=fields.Boolean()
     
	@api.multi
	def refresh(self,o365_tenant_id):
		logger.info("Getting subscribed skus for %s" % o365_tenant_id.defaultdomainname)
		result=o365_tenant_id.account_source_id.endpoints_id.execute('https://graph.microsoft.com/beta/subscribedskus',url='https://login.microsoftonline.com/' + o365_tenant_id.defaultdomainname)
		for sku in result['value']:
			#pdb.set_trace()
			subscribedsku=self.search([('o365_tenant_id','=',o365_tenant_id.id),('skuId','=',sku['skuId'])])
			if not subscribedsku:
				subscribedsku=self.create ({
					'o365_tenant_id':o365_tenant_id.id,
					'skuId':sku['skuId'],
					'skuPartNumber':sku['skuPartNumber'],
					'o365_id':sku['id'],
				})
			skus=self.env['lubon_qlan.skus_o365'].search([('GUID','=',sku['skuId'])])
			#pdb.set_trace()
			if len(skus)>=1:
				subscribedsku.friendly_name=skus[0].product_display_name
			subscribedsku.consumedUnits=sku['consumedUnits']
			subscribedsku.capabilityStatus=sku['capabilityStatus']
			subscribedsku.enabled=sku['prepaidUnits']['enabled']
			subscribedsku.warning=sku['prepaidUnits']['warning']
			subscribedsku.suspended=sku['prepaidUnits']['suspended']



class lubon_qlan_users_o365(models.Model):
	_name = 'lubon_qlan.users_o365'
	_description = 'Office 365 users'
	name=fields.Char()
	o365_id=fields.Char()
	lastname=fields.Char()
	firstname=fields.Char()
	principalname=fields.Char()
	domainname=fields.Char()
	o365_tenant_id=fields.Many2one('lubon_qlan.tenants_o365', ondelete='cascade')
	mail=fields.Char()
	qlan_tenant_id=fields.Many2one('lubon_qlan.tenants')
	person_id=fields.Many2one('res.partner', string="Related person", domain="[('type','=','contact')]")
	user_licenses_ids=fields.One2many('lubon_qlan.users_licenses_o365','user_o365_id')
	o365_domains_id=fields.Many2one('lubon_qlan.domains_o365')

	@api.multi
	def refresh(self,o365_tenant_id):
		logger.info("Getting users for %s" % o365_tenant_id.defaultdomainname)
		endpoint='https://graph.microsoft.com/beta/users'
		resultingUsers=[]
		while endpoint:
			result=o365_tenant_id.account_source_id.endpoints_id.execute(endpoint,url='https://login.microsoftonline.com/' + o365_tenant_id.defaultdomainname)
			resultingUsers+=result['value']
			if '@odata.nextLink' in result.keys():
				endpoint=result['@odata.nextLink']
			else:
				endpoint=None
			#pdb.set_trace()	
		#remove obsolete users
		for existinguser in o365_tenant_id.users_o365_ids:
			userfound=False
			for user in resultingUsers:
				if existinguser.o365_id==user['id']:
					userfound=True
			if not userfound:
				existinguser.unlink()
	#	pdb.set_trace()
		for user in resultingUsers:
			user_o365=self.search([('o365_tenant_id','=',o365_tenant_id.id),('o365_id','=',user['id'])])
			if not user_o365:
				user_o365=self.create ({
					'o365_tenant_id':o365_tenant_id.id,
					'o365_id':user['id'],
				})
			#pdb.set_trace()
			user_o365.lastname=user['surname']
			user_o365.firstname=user['givenName']
			user_o365.name=user['displayName']
			user_o365.principalname=user['userPrincipalName']
			user_o365.mail=user['mail']
			#user_o365.domainname=user['userPrincipalName'][user['userPrincipalName'].index('@') + 1 : ]
			user_o365.o365_domains_id=self.env['lubon_qlan.domains_o365'].search([('o365_tenant_id','=',o365_tenant_id.id),('name','=',(user['userPrincipalName'][user['userPrincipalName'].index('@') + 1 : ]).lower())])
			user_o365.qlan_tenant_id=o365_tenant_id.qlan_tenant_id
			user_o365.refresh_licenses(None,user)


	@api.multi
	def refresh_licenses(self,o365_id,graphresult=None):
		self.env['lubon_qlan.users_licenses_o365'].refresh(self,graphresult)		

class lubon_qlan_domains_o365(models.Model):
	_name = 'lubon_qlan.domains_o365'
	_description = 'Office 365 domains'
	name=fields.Char()
	used_for_billing=fields.Boolean()
	o365_tenant_id=fields.Many2one('lubon_qlan.tenants_o365',ondelete='cascade')

	@api.multi
	def refresh_domains_o365(self,o365_tenant_id):
		logger.info("Calling https://graph.microsoft.com/beta/domains for %s" % o365_tenant_id.defaultdomainname)
		result=o365_tenant_id.account_source_id.endpoints_id.execute('https://graph.microsoft.com/beta/domains',url='https://login.microsoftonline.com/' + o365_tenant_id.defaultdomainname)		
		for existingdomain in o365_tenant_id.domains_o365_ids:
			domainfound = False
			for domain in result['value']:
				if existingdomain.name==domain['id']:
					domainfound=True
			if not domainfound:
				existingdomain.unlink()		

		for domain in result['value']:
			currentdomain=self.search([('o365_tenant_id','=',o365_tenant_id.id),('name','=',domain['id'])])
			if not currentdomain:
				self.create({
					'name':domain['id'],
					'o365_tenant_id': o365_tenant_id.id
				})


class lubon_qlan_tenants_o365(models.Model):
	_name = 'lubon_qlan.tenants_o365'
	_description = 'Office 365 tenants'
	_rec_name = 'defaultdomainname'
	name=fields.Char()
	tenant_id=fields.Char()
	defaultdomainname=fields.Char()
	qlan_tenant_id=fields.Many2one('lubon_qlan.tenants')
	account_source_id=fields.Many2one('lubon_qlan.account_source')
	get_details=fields.Boolean(default = False)
	sku_ids=fields.One2many('lubon_qlan.subscribedskus_o365','o365_tenant_id')
	users_o365_ids=fields.One2many('lubon_qlan.users_o365','o365_tenant_id')
	domains_o365_ids=fields.One2many('lubon_qlan.domains_o365','o365_tenant_id')
	billingconfig_tenants_o365_ids=fields.One2many('lubon_qlan.billingconfig_tenant_o365','o365_tenant_id')

	@api.multi
	def refresh_tenants_o365(self,account_source_id):
		logger.info("Calling https://graph.microsoft.com/beta/contracts")
		result=account_source_id.endpoints_id.execute('https://graph.microsoft.com/beta/contracts','')
		for tenant in result['value']:
			tenant_id=self.search([('tenant_id','=',tenant['id'])])
			if not tenant_id:
				tenant_id=self.create({
					'tenant_id': tenant['id']
					})
			if tenant_id:
				tenant_id.name=tenant['displayName']
				tenant_id.defaultdomainname=tenant['defaultDomainName']
				tenant_id.account_source_id=account_source_id.id
				tenant_id.refresh_thistenant_o365(None)
			else:
				pdb.set_trace()
	@api.multi
	def load_billing_combinations_o365(self, o365_tenant_id):
		for sku in self.sku_ids:
			if sku.invoicable:
				for domain in self.domains_o365_ids:
					if domain.used_for_billing:
						if not self.env['lubon_qlan.billingconfig_tenant_o365'].search(['&',('subscribedskus_o365_id','=',sku.id),('domains_o365_id','=',domain.id)]):
							#pdb.set_trace()
							#combination domain/sku not found
							self.env['lubon_qlan.billingconfig_tenant_o365'].create({
								'o365_tenant_id':self.id,
								'qlan_tenant_id':self.qlan_tenant_id.id,
								'subscribedskus_o365_id': sku.id,
								'domains_o365_id': domain.id
							})		
						
	
	@api.multi
	def refresh_thistenant_o365(self,o365_tenant_id):
		self.refresh_domains_o365(None)
		if self.qlan_tenant_id:  
			self.refresh_subscribed_skus_o365(None)
			if self.get_details:
				self.refresh_users_o365(None)		




	@api.multi
	def refresh_subscribed_skus_o365(self,o365_tenant_id):
		self.env['lubon_qlan.subscribedskus_o365'].refresh(self)
	@api.multi
	def refresh_users_o365(self,o365_tenant_id):
		self.env['lubon_qlan.users_o365'].refresh(self)
	@api.multi
	def refresh_domains_o365(self,o365_tenant_id):
		self.env['lubon_qlan.domains_o365'].refresh_domains_o365(self)




class lubon_qlan_new_aduser(models.TransientModel):
	_name = 'lubon_qlan.new_aduser'
	_description = "New AD User"

	name=fields.Char()
	person_id=fields.Many2one('res.partner')
	customer_id=fields.Many2one('res.partner')
	contract_id=fields.Many2one('account.analytic.account')
	displayname=fields.Char() 
	first_name=fields.Char() 
	last_name=fields.Char() 
	email=fields.Char() 
	upn=fields.Char() 
	logon_script=fields.Char() 
	mail_db=fields.Char() 
	alias=fields.Char() 
	mobile=fields.Char(placeholder="+32475963182") 
	samaccountname=fields.Char()
	tenant_id=fields.Many2one('lubon_qlan.tenants')
	contract_line_id=fields.Many2one('account.analytic.invoice.line')
	validcustomers_ids=fields.Many2many('res.partner')
	validcontract_ids=fields.Many2many('account.analytic.account')
	password_never_expires=fields.Boolean()
	debug=fields.Boolean()


	def _generate_password(self):
		return passgen(length=12, punctuation=False, digits=True, letters=True, case='both')

	password=fields.Char(default=_generate_password)

	@api.multi
	@api.onchange('tenant_id')
	def set_defs(self):
		if len(self.validcustomers_ids)==1:
			self.customer_id=self.validcustomers_ids[0]
		if len(self.validcontract_ids)==1:
			self.contract_id=self.validcontract_ids[0]
		self.mail_db=self.tenant_id.default_mail_db	
		self.logon_script=self.tenant_id.default_logon_script
		self.password_never_expires=self.tenant_id.default_password_never_expires	

	@api.multi
	@api.onchange('first_name','last_name')
	def set_name_related(self):
		self.displayname=""
		self.email=""
		self.alias=self.tenant_id.code + "-"
		if self.first_name:
			self.alias += self.first_name[:2].lower()
			self.displayname += self.first_name
			self.email+=self.first_name.lower()
		if self.last_name:
			self.alias += self.last_name[:2].lower()
			if self.first_name:
				self.displayname += " "
				self.email += "."
			self.displayname += self.last_name
			self.email += self.last_name.lower()
	@api.multi
	def create_user(self):
		cmd={'parameters':
				{
				'strTenant':self.tenant_id.code,
				'strReseller':self.tenant_id.reseller_partner_id.reseller_code,
				'strPassword': self.password,
				}
			}

		pdb.set_trace()

