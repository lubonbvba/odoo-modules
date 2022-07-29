# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api,exceptions, _
from datetime import datetime,timedelta
from passgen import passgen
import re
import pdb,logging
import yaml
import os,requests
logger = logging.getLogger(__name__)


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
	_sql_constraints=[('user_and_ad_group','UNIQUE(user_o365_id,subscribedskus_o365)','Model lubon_qlan_users_license_o365: Combination user/sunscribed sku unique')]
	user_o365_id = fields.Many2one('lubon_qlan.users_o365', ondelete='cascade')
	subscribedskus_o365 = fields.Many2one('lubon_qlan.subscribedskus_o365',ondelete='cascade')
	billingconfig_tenant_o365=fields.Many2one('lubon_qlan.billingconfig_tenant_o365',ondelete='cascade')


#	billing_history_id= fields.Many2one('lubon_qlan.billing_history' )
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

		for license in assignedLicenses:
			newsku=self.env['lubon_qlan.subscribedskus_o365'].search([('skuId','=',license['skuId']),('o365_tenant_id','=',user_id.o365_tenant_id.id)])
			if len(newsku)>1:
				logger.error("Newsku > in refresh")
			activelicense=self.search([('user_o365_id','=',user_id.id),('subscribedskus_o365','=',newsku.id)])
			if not activelicense:
				activelicense=self.create({
					'user_o365_id':user_id.id,
					'subscribedskus_o365': newsku.id
				})
			if not activelicense.billingconfig_tenant_o365.manual_exception:
				# do not change license assignment if a manual one was assigned 		
				activelicense.billingconfig_tenant_o365=self.env['lubon_qlan.billingconfig_tenant_o365'].search([('domains_o365_id','=',user_id.o365_domains_id.id),('subscribedskus_o365_id','=',newsku.id)])
			if activelicense.billingconfig_tenant_o365:
				self.env['lubon_qlan.billing_history'].verify_billing_history_line(activelicense,1,activelicense.billingconfig_tenant_o365.contract_line_id,"O365 license: %s" % activelicense.user_o365_id.name,related_user=user_id,owner=user_id.principalname.lower())

		#pdb.set_trace()

class lubon_qlan_billingconfig_tenant_o365(models.Model):
	_name = 'lubon_qlan.billingconfig_tenant_o365'
	_description = 'Office 365 tenant billing config'
#	_sql_constraints=[('contract_line_and_ad_group','UNIQUE(contract_line_id,subscribedskus_o365_id)','Contract and subscribed sku unique')]

	subscribedskus_o365_id=fields.Many2one('lubon_qlan.subscribedskus_o365',domain="[('invoicable','=',True),('id','in',valid_subscribedskus_o365_ids[0][2])]", required=True)
	o365_tenant_id=fields.Many2one('lubon_qlan.tenants_o365', ondelete='cascade', required=True)
	domains_o365_id=fields.Many2one('lubon_qlan.domains_o365', domain="[('id','in',valid_domains_o365_ids[0][2]),('used_for_billing','=',True)]", zrequired=True)
	qlan_tenant_id=fields.Many2one('lubon_qlan.tenants', ondelete='cascade', required=True)
	contract_line_id=fields.Many2one('account.analytic.invoice.line', domain="[('analytic_account_id','in', valid_contract_ids[0][2])]", zrequired=True)
	manual_exception=fields.Boolean(help="Manual created entry to set on exceptions")
	remark=fields.Char()
	users_licenses_o365_ids=fields.One2many('lubon_qlan.users_licenses_o365', 'billingconfig_tenant_o365')
	users_licenses_o365_count=fields.Integer(string='Count', compute ='_get_users_licenses_o365_count')
	valid_domains_o365_ids=fields.Many2many('lubon_qlan.domains_o365', compute='_get_valid_domains_o365_ids')
	valid_contract_ids=fields.Many2many('account.analytic.account', compute='_get_valid_contract_ids')
	valid_subscribedskus_o365_ids=fields.Many2many('lubon_qlan.subscribedskus_o365', compute='_get_valid_subscribedskus_o365_ids')

	@api.depends('users_licenses_o365_ids')
	@api.one
	def _get_users_licenses_o365_count(self):
		self.users_licenses_o365_count=len(self.users_licenses_o365_ids)

	@api.multi
	def name_get(self):
		res=[]
		for line in self:
			if line.domains_o365_id.name:
				res.append((line.id,line.domains_o365_id.name + " - " + line.subscribedskus_o365_id.friendly_name  ))
			if line.manual_exception:
				res.append((line.id, "Manual - " + line.subscribedskus_o365_id.friendly_name + " " + line.remark ))	
		return res



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
	subscribed_users_o365=fields.One2many( 'lubon_qlan.users_licenses_o365','subscribedskus_o365')
	arrow_services_ids=fields.One2many('lubon_qlan.arrowservices_o365','sku_id')
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
	purchased_count=fields.Integer(compute='_recalculate_computed', store=True, Index=True)
	billed_count=fields.Integer(compute='_recalculate_computed', store=True,Index=True)
	billed_count_difference=fields.Integer(compute='_recalculate_computed', string='Billed vs enabled', store=True, index=True)
	billed_count_ok=fields.Boolean(compute='_recalculate_computed', store=True)#, index=True)


	@api.one
	@api.depends('enabled','subscribed_users_o365','consumedUnits','invoicable','arrow_services_ids','purchased_count')
	def _recalculate_computed(self):
		nPurchased=0
		nBilled=0
		for line in self.arrow_services_ids:
			nPurchased+=line.arrow_number
			nBilled+=line.billed
		self.purchased_count=nPurchased
		self.billed_count=nBilled
		self.billed_count_difference=self.enabled-self.billed_count
		if self.invoicable and self.billed_count_difference !=0:
			self.billed_count_ok=False
		else:
			self.billed_count_ok=True


	# @api.one
	# @api.onchange('arrow_services_ids')
	# def _calculate_purchased_count(self):
	# 	n=0
	# 	for line in self.arrow_services_ids:
	# 		n+=line.arrow_number
	# 	self.purchased_count=n
	# 	self._calculate_billed_difference()
	# #	pdb.set_trace()	


	# @api.one
	# @api.depends('enabled','subscribed_users_o365','consumedUnits','invoicable')
	# def _calculate_billed(self):

	# 	self.billed_count=len(self.subscribed_users_o365)
	# 	self.billed_count_difference=self.enabled-self.billed_count

	# @api.one
	# @api.depends('billed_count','purchased_count')
	# def _calculate_billed_difference(self):
	# 	self.billed_count_difference=self.enabled-self.purchased_count

	# @api.one
	# @api.depends('billed_count_difference', 'enabled','purchased_count','invoicable', )
	# def _calculate_billed_ok(self):
	# 	if self.invoicable and self.billed_count_difference !=0:
	# 		self.billed_count_ok=False
	# 	else:
	# 		self.billed_count_ok=True



     
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
			if len(skus)>=1:
				subscribedsku.friendly_name=skus[0].product_display_name
			#pdb.set_trace()
			if o365_tenant_id.invoicable:	
				subscribedsku.consumedUnits=sku['consumedUnits']
				subscribedsku.capabilityStatus=sku['capabilityStatus']
				subscribedsku.enabled=sku['prepaidUnits']['enabled']
				subscribedsku.warning=sku['prepaidUnits']['warning']
				subscribedsku.suspended=sku['prepaidUnits']['suspended']
			else:
				subscribedsku.consumedUnits=0
				subscribedsku.capabilityStatus=0
				subscribedsku.enabled=0
				subscribedsku.warning=0
				subscribedsku.suspended=0




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
	mail_rules=fields.Char()
	mail_rules_nr=fields.Integer()

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
#			user_o365.refresh_mail_rules()


	@api.multi
	def refresh_licenses(self,o365_id,graphresult=None):
		self.env['lubon_qlan.users_licenses_o365'].refresh(self,graphresult)	

	@api.multi
	def refresh_mail_rules(self):
		endpoint='https://graph.microsoft.com/v1.0/users/'+ self.o365_id + '/mailFolders/inbox/messageRules'
#		while endpoint:
		result=self.o365_tenant_id.account_source_id.endpoints_id.execute(endpoint,url='https://login.microsoftonline.com/' + self.o365_tenant_id.defaultdomainname)
		if 'value' in result.keys():
			self.mail_rules_nr=len(result['value'])
			self.mail_rules=result['value']



class lubon_qlan_domains_o365(models.Model):
	_name = 'lubon_qlan.domains_o365'
	_description = 'Office 365 domains'
	name=fields.Char()
	used_for_billing=fields.Boolean()
	o365_tenant_id=fields.Many2one('lubon_qlan.tenants_o365',ondelete='cascade')
	qlan_tenant_id=fields.Many2one('lubon_qlan.tenants',ondelete='cascade')

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
				currentdomain=self.create({
					'name':domain['id'],
					'o365_tenant_id': o365_tenant_id.id
				})
			currentdomain.qlan_tenant_id=o365_tenant_id.qlan_tenant_id	

class lubon_qlan_signin_azure(models.Model):
	_name = 'lubon_qlan.signin_azure'
	_description = 'Azure AD signin log'
	_sql_constraints=[('azure_ad_unique','UNIQUE(azure_id)','Azure id unique')]
	_order='createdDateTime DESC'
	o365_tenant_id=fields.Many2one('lubon_qlan.tenants_o365',ondelete='cascade')
	user_id=fields.Many2one('lubon_qlan.users_o365')
	isbasicauth=fields.Boolean()
	appliedConditionalAccessPolicies=fields.Char()
	resourceId=fields.Char()
	riskEventTypes_v2=fields.Char()
	userPrincipalName=fields.Char()
	azure_id=fields.Char(index=True)
	correlationId=fields.Char()
	userDisplayName=fields.Char()
	deviceDetail=fields.Char()
	location=fields.Char()
	status=fields.Char()
	riskLevelDuringSignIn=fields.Char()
	conditionalAccessStatus=fields.Char()
	clientAppUsed=fields.Char()
	resourceDisplayName=fields.Char()
	userId=fields.Char()
	riskDetail=fields.Char()
	appId=fields.Char()
	riskLevelAggregated=fields.Char()
	createdDateTime=fields.Datetime()
	appDisplayName=fields.Char()
	isInteractive=fields.Char()
	riskEventTypes=fields.Char()
	riskState=fields.Char()
	ipAddress=fields.Char()
	authenticationContextClassReferences=fields.Char()
	authenticationDetails=fields.Char()
	authenticationMethodsUsed=fields.Char()
	authenticationProcessingDetails=fields.Char()
	authenticationProtocol=fields.Char()
	authenticationRequirement=fields.Char()
	authenticationRequirementPolicies=fields.Char()
	autonomousSystemNumber=fields.Char()
	clientCredentialType=fields.Char()
	crossTenantAccessType=fields.Char()
	federatedCredentialId=fields.Char()
	flaggedForReview=fields.Char()
	homeTenantId=fields.Char()
	homeTenantName=fields.Char()
	incomingTokenType=fields.Char()
	ipAddressFromResourceProvider=fields.Char()
	isTenantRestricted=fields.Char()
	mfaDetail=fields.Char()
	networkLocationDetails=fields.Char()
	originalRequestId=fields.Char()
	privateLinkDetails=fields.Char()
	processingTimeInMilliseconds=fields.Char()
	resourceServicePrincipalId=fields.Char()
	resourceTenantId=fields.Char()
	servicePrincipalCredentialKeyId=fields.Char()
	servicePrincipalCredentialThumbprint=fields.Char()
	servicePrincipalId=fields.Char()
	servicePrincipalName=fields.Char()
	sessionLifetimePolicies=fields.Char()
	signInEventTypes=fields.Char()
	signInIdentifier=fields.Char()
	signInIdentifierType=fields.Char()
	tokenIssuerName=fields.Char()
	tokenIssuerType=fields.Char()
	uniqueTokenIdentifier=fields.Char()
	userAgent=fields.Char()
	userType=fields.Char()	

	@api.multi
	def new_signin(self,o365_tenant_id,record):
		if not self.search([('azure_id','=',record['id'])]):
			newrec=self.create({
				'o365_tenant_id': o365_tenant_id.id,
				'azure_id': record['id'],
				'createdDateTime': record['createdDateTime'],
			})
			value={}
			for field in record.keys():
				if field not in ['id','createdDateTime']:
					if field in newrec._fields:
						value[field]=record[field]
					else:
						logger.warning('Field %s does not exist in lubon_qlan.signin_azure ', field  )	
			newrec.write(value)
			newrec.user_id=self.env['lubon_qlan.users_o365'].search([('o365_id','=', record['userId'])])
	@api.multi
	
	def get_signins_cron(self, xyz=None):
		logger.info("Start get_signins_cron")
		tenants=self.env['lubon_qlan.tenants_o365'].search([('get_signins','=',True)])
		#pdb.set_trace()
		for tenant in tenants:
			if tenant.get_details:
				logger.info("Processing users for: %s, %s", tenant.name, tenant.defaultdomainname)
				tenant.refresh_users_o365(None)
			logger.info("Processing signins for: %s, %s", tenant.name, tenant.defaultdomainname)
			tenant.get_signin_logs_o365()
		logger.info("End get_signins_cron")
			

class lubon_qlan_tenants_o365(models.Model):
	_name = 'lubon_qlan.tenants_o365'
	_description = 'Office 365 tenants'
	_rec_name = 'defaultdomainname'
	name=fields.Char()
	tenant_id=fields.Char()
	arrow_ref=fields.Char(help='Arrow reference, XSP + Value found in Acronym')
	defaultdomainname=fields.Char()
	qlan_tenant_id=fields.Many2one('lubon_qlan.tenants')
	account_source_id=fields.Many2one('lubon_qlan.account_source')
	get_details=fields.Boolean(default = False, help='Get full user details of this tenant')
	get_signins=fields.Boolean(default = False, help='Get Sign in\'s for this tenant')
	invoicable=fields.Boolean(default = True, help='Tenant invoiced by us')
	arrow_services_o365_ids=fields.One2many('lubon_qlan.arrowservices_o365','o365_tenant_id')
	show_hidden=fields.Boolean()
	sku_ids=fields.One2many('lubon_qlan.subscribedskus_o365','o365_tenant_id')
	users_o365_ids=fields.One2many('lubon_qlan.users_o365','o365_tenant_id')
	domains_o365_ids=fields.One2many('lubon_qlan.domains_o365','o365_tenant_id')
	billingconfig_tenants_o365_ids=fields.One2many('lubon_qlan.billingconfig_tenant_o365','o365_tenant_id')
	signin_azure_ids=fields.One2many('lubon_qlan.signin_azure','o365_tenant_id')
	last_error_signins=fields.Char()
	
	@api.multi
	def process_changes(self):
		#pdb.set_trace()
		for sku in self.sku_ids:
			sku.calculate_purchased_count()

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
	def get_signin_logs_o365(self): #, o365_tenant_id):		
		endpoint='https://graph.microsoft.com/beta/auditLogs/signIns'
		filter = ""
		if self.signin_azure_ids:
			last_rec=self.signin_azure_ids.sorted(key=lambda x: x.createdDateTime, reverse=True)[0]
			max_date=last_rec.createdDateTime.replace (' ', 'T')+'z'
			filter=("?$filter=createdDateTime gt %s and id ne '%s'" % (max_date, last_rec['azure_id']) )
		if filter:
			endpoint=endpoint + filter + "&order by createdDateTime asc"
		else:	
			endpoint=endpoint + "?order by createdDateTime asc"

		nIterations=0
		while endpoint and nIterations <= 25:
			logger.info(endpoint)
			nIterations+=1
			result=self.account_source_id.endpoints_id.execute(cmd_line=endpoint,url='https://login.microsoftonline.com/'+ self.defaultdomainname)	
			if 'error' in result.keys():
				logger.exception("Error message: %s", result['error']['message'])
				self.last_error_signins=result['error']['message']
				endpoint=None
			else:
				for record in result['value']:
					self.env['lubon_qlan.signin_azure'].new_signin(self,record)
				if '@odata.nextLink' in result.keys():
					endpoint=result['@odata.nextLink']
				else:
					endpoint=None
	@api.multi
	def purge_signin_logs_o365(self):	
		self.signin_azure_ids.unlink()
	
	@api.multi
	def refresh_thistenant_o365(self,o365_tenant_id):
		self.refresh_domains_o365(None)
		if self.qlan_tenant_id:  
			self.refresh_subscribed_skus_o365(None)
			if self.get_details:
				self.refresh_users_o365(None)
		self.sku_ids._recalculate_computed()				

	@api.multi
	def refresh_arrow_services(self):
		tenants=self.env['lubon_qlan.tenants_o365'].search([('arrow_ref','ilike','XSP')])
		logger.info("Getting arrow services for %d tenants." % len(tenants))
		for tenant in tenants:
			logger.info("Getting arrow services %s" % tenant.defaultdomainname)
			self.env['lubon_qlan.arrowservices_o365'].get_services(tenant)



	@api.multi
	def get_arrow_services(self):
		self.env['lubon_qlan.arrowservices_o365'].get_services(self)

	@api.multi
	def refresh_subscribed_skus_o365(self,o365_tenant_id):
		self.env['lubon_qlan.subscribedskus_o365'].refresh(self)
	@api.multi
	def refresh_users_o365(self,o365_tenant_id):
		self.env['lubon_qlan.users_o365'].refresh(self)
	@api.multi
	def refresh_domains_o365(self,o365_tenant_id):
		self.env['lubon_qlan.domains_o365'].refresh_domains_o365(self)

class lubon_qlan_arrowservices_o365(models.Model):
	_name = 'lubon_qlan.arrowservices_o365'
	_description = 'Arrow services'
	name=fields.Char()
	active=fields.Boolean(default=True)
	o365_tenant_id=fields.Many2one('lubon_qlan.tenants_o365')
	sku_id=fields.Many2one('lubon_qlan.subscribedskus_o365',domain="[('o365_tenant_id','=',o365_tenant_id)]", string='Linked sku in tenant' )
	arrow_license_id=fields.Char()
	arrow_name=fields.Char()
	arrow_number=fields.Integer()
	arrow_friendly_name=fields.Char()
	arrow_vendor_sku=fields.Char()
	arrow_state=fields.Char()
	arrow_expiry_datetime=fields.Char()
	arrow_last_update=fields.Datetime()
	contract_line_id=fields.Many2one('account.analytic.invoice.line', domain="[('analytic_account_id','in', valid_contract_ids[0][2])]", zrequired=True)
	valid_contract_ids=fields.Many2many('account.analytic.account', compute='_get_valid_contract_ids')
	billed=fields.Integer(compute='_compute_billed')
	new_checked=fields.Boolean(help='New services are not ticked to verify them. If there is a contract line, this is ticked.')
#	check_billing=fields.Boolean(compute='_compute_check', index=True, store=True )
	hidden=fields.Boolean()

	@api.depends('sku_id')
	@api.one
	def _process_sku_id_change(self):
		self.sku_id.o365_tenant_id.process_changes()

	@api.onchange('o365_tenant_id')
	@api.one
	def _get_valid_contract_ids(self):
		self.valid_contract_ids=self.o365_tenant_id.qlan_tenant_id.contract_ids
		#pdb.set_trace()

	# @api.one
	# @api.depends('arrow_number','contract_line_id.quantity')
	# def _compute_check(self):
	# 	if self.arrow_number == self.contract_line_id.quantity:
	# 		self.check_billing=False
	# 	else:
	# 		self.check_billing=True
	# 	pdb.set_trace()

	@api.onchange('contract_line_id')
	@api.one
	def _compute_billed(self):	
		if self.contract_line_id:
			self.billed=self.contract_line_id.quantity
		else:
			self.billed=0

	@api.multi
	def update_billing(self):
		if self.contract_line_id:
			self.contract_line_id.quantity=self.arrow_number
			self.env.cr.commit()

	@api.multi
	def get_services(self,o365_tenant_id):
		with open(os.path.expanduser('~/.odoosettings/arrow.yaml')) as file:
			settings = yaml.load(file)
		url=settings['baseurl'] + '/customers/' + o365_tenant_id.arrow_ref + '/licenses'
		arrow_data = requests.get(  
            url,
            headers={'apikey': settings['key']} )
		for license in arrow_data.json()['data']['licenses']:
			service_id=self.search([('arrow_license_id',"ilike",license['license_id'])])
			if not service_id:
				service_id= self.create({
					'o365_tenant_id': o365_tenant_id.id,
					'arrow_license_id': license['license_id']
				})
			service_id.update({
				'arrow_name': license['name'],
				'arrow_number': license['seats'],
				'arrow_friendly_name': license['friendlyName'],
				'arrow_vendor_sku': license['sku'],
				'arrow_state': license['state'],
				'arrow_expiry_datetime': license['expiry_datetime'],
				'arrow_last_update':fields.Datetime.now(),
			})	
			if service_id.contract_line_id:
				service_id.new_checked=True
				nLicenses=0
				for service in service_id.contract_line_id.arrow_services_ids:
					nLicenses += service.arrow_number
				#service_id.contract_line_id.current_usage=license['seats']
				service_id.contract_line_id.current_usage=nLicenses

			if service_id and license['state'] in ['suspended','expired trial','canceled']:
				service_id.active=False
				service_id.contract_line_id=False
			else:
				service_id.active=True

			#pdb.set_trace()

class account_analytic_invoice_line(models.Model):
	_inherit = 'account.analytic.invoice.line'
	arrow_services_ids=fields.One2many('lubon_qlan.arrowservices_o365','contract_line_id')
