# -*- coding: utf-8 -*-
from sys import settrace
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
#			if activelicense.billingconfig_tenant_o365:
#				self.env['lubon_qlan.billing_history'].verify_billing_history_line(activelicense,1,activelicense.billingconfig_tenant_o365.contract_line_id,"O365 license: %s" % activelicense.user_o365_id.name,related_user=user_id,owner=user_id.principalname.lower())

		#pdb.set_trace()

class lubon_qlan_billingconfig_tenant_o365(models.Model):
	_name = 'lubon_qlan.billingconfig_tenant_o365'
	_description = 'Office 365 tenant billing config'
#	_sql_constraints=[('contract_line_and_ad_group','UNIQUE(contract_line_id,subscribedskus_o365_id)','Contract and subscribed sku unique')]

	subscribedskus_o365_id=fields.Many2one('lubon_qlan.subscribedskus_o365',domain="[('invoicable','=',True),('id','in',valid_subscribedskus_o365_ids[0][2])]", zrequired=True)
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
	purchased_count=fields.Integer(zcompute='_recalculate_computed', zstore=True, Index=True)
	billed_count=fields.Integer(zcompute='_recalculate_computed', zstore=True,Index=True)
	billed_count_difference=fields.Integer(zcompute='_recalculate_computed', string='Billed vs enabled', zstore=True, index=True)
	billed_count_ok=fields.Boolean(zcompute='_recalculate_computed', zstore=True)#, index=True)


	# @api.one
	# @api.depends('enabled','subscribed_users_o365','consumedUnits','invoicable','arrow_services_ids','purchased_count')
	# def _recalculate_computed(self):
	# 	nPurchased=0
	# 	nBilled=0
	# 	contract_lines_ids=[]
	# 	for line in self.arrow_services_ids:
	# 		nPurchased+=line.arrow_number
	# 		if not line.contract_line_id.id in contract_lines_ids:
	# 			nBilled+=line.billed
	# 		contract_lines_ids.append(line.contract_line_id.id)	
	# 	self.purchased_count=nPurchased
	# 	self.billed_count=nBilled

	# 	self.billed_count_difference=self.enabled-self.billed_count
	# 	if self.invoicable and self.billed_count_difference !=0:
	# 		self.billed_count_ok=False
	# 	else:
	# 		self.billed_count_ok=True

     
	@api.multi
	def refresh(self,o365_tenant_id):
		logger.info("Getting subscribed skus for %s" % o365_tenant_id.defaultdomainname)
		result=o365_tenant_id.account_source_id.endpoints_id.execute('https://graph.microsoft.com/beta/subscribedskus',url='https://login.microsoftonline.com/' + o365_tenant_id.defaultdomainname)
		asku=[]
			#pdb.set_trace
		for sku in result['value']:
			nPurchased=0
			nBilled=0
			contract_lines_ids=[]

			#pdb.set_trace()
			asku.append(sku['skuId'])
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

			for line in subscribedsku.arrow_services_ids:
				nPurchased+=line.arrow_number
				if not line.contract_line_id.id in contract_lines_ids:
					nBilled+=line.billed
				contract_lines_ids.append(line.contract_line_id.id)	
				subscribedsku.purchased_count=nPurchased
				subscribedsku.billed_count=nBilled

			subscribedsku.billed_count_difference=subscribedsku.enabled-subscribedsku.billed_count
			if subscribedsku.invoicable and subscribedsku.billed_count_difference !=0:
				subscribedsku.billed_count_ok=False
			else:
				subscribedsku.billed_count_ok=True

		if len(asku)>0:
			#remove sku from odoo if the don't exist on azure
			for existingsku in self.search([('o365_tenant_id','=',o365_tenant_id.id)]):
				if existingsku.skuId not in asku:
					#pdb.set_trace()
					# for s in existingsku.subscribed_users_o365:
					# 	s.
					existingsku.unlink()




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
			if not 'value' in result.keys():
				existingdomain.unlink()
			else:	
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
#	_order='id'

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
	createdDateTime=fields.Datetime(index = True)
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
#					else:
#						logger.warning('Field %s does not exist in lubon_qlan.signin_azure ', field  )	
			newrec.write(value)
			newrec.user_id=self.env['lubon_qlan.users_o365'].search([('o365_id','=', record['userId'])])
			

	@api.multi
	def get_signins_cron(self, xyz=None):
		logger.info("Start get_signins_cron")
		#delete all older then 30 days
		logger.info("Delete all older then 30 days")
		cleandate=fields.Date.to_string(fields.Date.from_string(fields.Date.context_today(self)) - timedelta(days=30))
		obsolete=self.search([('createdDateTime','<',cleandate)])
		obsolete.unlink()
		self.env.cr.commit()
	    #delete appDisplayName Microsoft Azure Active Directory Connect
		logger.info("appDisplayName Microsoft Azure Active Directory Connect and older then 5 days")
		cleandate=fields.Date.to_string(fields.Date.from_string(fields.Date.context_today(self)) - timedelta(days=5))
		obsolete=self.search([('createdDateTime','<',cleandate),('appDisplayName','=','Microsoft Azure Active Directory Connect')])
		obsolete.unlink()
		self.env.cr.commit()
		logger.info("Start processing tenants")
		tenants=self.env['lubon_qlan.tenants_o365'].search([('get_signins','=',True)])
		#pdb.set_trace()
		for tenant in tenants:
			# if tenant.get_details:
			# 	logger.info("Processing users for: %s, %s", tenant.name, tenant.defaultdomainname)
			# 	tenant.refresh_users_o365(None)
			logger.info("Processing signins for: %s, %s", tenant.name, tenant.defaultdomainname)
			tenant.get_signin_logs_o365()
			self.env.cr.commit()
		logger.info("End get_signins_cron")
			

class lubon_qlan_tenants_o365(models.Model):
	_name = 'lubon_qlan.tenants_o365'
	_description = 'Office 365 tenants'
	_rec_name = 'defaultdomainname'
	name=fields.Char()
	tenant_id=fields.Char(string = 'Contract ID')
	entra_tenant_id=fields.Char(string="Entra Tenant ID" )
	consent_ok= fields.Boolean(help='Consent given to App in tenant?')
	arrow_ref=fields.Char(help='Arrow reference, XSP + Value found in Acronym')
	defaultdomainname=fields.Char()
	qlan_tenant_id=fields.Many2one('lubon_qlan.tenants')
	account_source_id=fields.Many2one('lubon_qlan.account_source')
	get_details=fields.Boolean(default = False, help='Get full user details of this tenant')
	get_signins=fields.Boolean(default = False, help='Get Sign in\'s for this tenant')
	invoicable=fields.Boolean(default = True, help='Tenant invoiced by us')
	arrow_services_o365_ids=fields.One2many('lubon_qlan.arrowservices_o365','o365_tenant_id')
	qlan_counterdefs_ids=fields.One2many('lubon_qlan.counterdefs','o365_tenant_id')
	
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
	def check_consent(self):
		logger.info("Calling https://graph.microsoft.com/beta/organization")
		endpoint='https://graph.microsoft.com/beta/organization'
		result=self.account_source_id.endpoints_id.execute(endpoint,url='https://login.microsoftonline.com/' + self.defaultdomainname)
		if 'error' in result.keys():
			self.consent_ok=False
		else:
			self.consent_ok=True


	@api.multi
	def refresh_tenants_o365(self,account_source_id):
		logger.info("Calling https://graph.microsoft.com/beta/contracts")
		result=account_source_id.endpoints_id.execute('https://graph.microsoft.com/beta/contracts','')
		logging.info("Tenants found: %d", len(result['value']))
		for tenant in result['value']:
			logging.info("Processing: %s", tenant['displayName'])
			tenant_id=self.search([('tenant_id','=',tenant['id'])])
			if not tenant_id:
				tenant_id=self.create({
					'tenant_id': tenant['id']
					})
			if tenant_id:
				tenant_id.name=tenant['displayName']
				tenant_id.defaultdomainname=tenant['defaultDomainName']
				tenant_id.entra_tenant_id=tenant['customerId']
				tenant_id.account_source_id=account_source_id.id
				pdb.set_trace()
				#tenant_id.refresh_thistenant_o365(None)
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
		self.check_consent()
		if self.consent_ok:
			self.refresh_domains_o365(None)
			if self.qlan_tenant_id:  
				self.refresh_subscribed_skus_o365(None)
				if self.get_details:
					self.refresh_users_o365(None)

	@api.multi
	def refresh_arrow_services(self):
		tenants=self.env['lubon_qlan.tenants_o365'].search([('arrow_ref','ilike','XSP')])
		logger.info("Getting arrow services for %d tenants." % len(tenants))
		for tenant in tenants:
			logger.info("Getting arrow services %s" % tenant.defaultdomainname)
			self.env['lubon_qlan.arrowservices_o365'].get_services(tenant)

	@api.multi
	def refresh_all_counterdefs(self):
		self.env['lubon_qlan.counterdefs'].get_counterdefs()
		
		# tenants=self.env['lubon_qlan.tenants_o365'].search([('entra_tenant_id','!=',False)])
		# logger.info("Getting counterdefs for %d tenants." % len(tenants))
		# for tenant in tenants:
		# 	logger.info("Getting counterdefs %s" % tenant.defaultdomainname)
		# 	self.env['lubon_qlan.counterdefs'].get_counterdefs(tenant)
	@api.multi
	def reset_all_counterdefs(self):
		tenants=self.env['lubon_qlan.tenants_o365'].search([('entra_tenant_id','!=',False)])
		logger.info("Resetting counterdefs for %d tenants." % len(tenants))
		for tenant in tenants:
			logger.info("Resetting counterdefs %s" % tenant.defaultdomainname)
			tenant.reset_counterdefs()
	
	@api.multi
	def update_all_contract_lines(self):
		tenants=self.env['lubon_qlan.tenants_o365'].search([('entra_tenant_id','!=',False)])
		logger.info("Resetting counterdefs for %d tenants." % len(tenants))
		for tenant in tenants:
			logger.info("Updating contractlines %s" % tenant.defaultdomainname)
			tenant.update_contract_lines()

	@api.multi	
	def update_contract_lines(self):
		for counterdef in self.qlan_counterdefs_ids:
			counterdef.update_contract_line()


	@api.multi
	def get_counterdefs(self):
		self.env['lubon_qlan.counterdefs'].get_counterdefs(self)

	@api.multi
	def reset_counterdefs(self):
		for counterdef in self.qlan_counterdefs_ids:
			counterdef.current_counter_value =-1

	@api.multi
	def update_contract_lines(self):
		for counterdef in self.qlan_counterdefs_ids:
			counterdef.update_contract_line()


	@api.multi
	def get_arrow_services(self):
		self.env['lubon_qlan.arrowservices_o365'].get_services(self)

	@api.multi
	def refresh_subscribed_skus_o365(self,o365_tenant_id):
		if self.consent_ok:
			self.env['lubon_qlan.subscribedskus_o365'].refresh(self)
	@api.multi
	def refresh_users_o365(self,o365_tenant_id):
		if self.consent_ok:
			self.env['lubon_qlan.users_o365'].refresh(self)
	@api.multi
	def refresh_domains_o365(self,o365_tenant_id):
		if self.consent_ok:
			self.env['lubon_qlan.domains_o365'].refresh_domains_o365(self)

class lubon_qlan_counterdefs(models.Model):
	_name = 'lubon_qlan.counterdefs'
	_description = 'Qlan Counter definitions'
	_rec_name = 'friendly_name'
	name=fields.Char()
	o365_tenant_id=fields.Many2one('lubon_qlan.tenants_o365')
#	contract_line_id=fields.Many2one('account.analytic.invoice.line', domain="[('analytic_account_id','in', valid_contract_ids[0][2])]", zrequired=True)
	contract_line_id=fields.Many2one('account.analytic.invoice.line', domain="[('id','in',valid_contract_line_ids[0][2])]", zrequired=True)
	partner_id=fields.Many2one('res.partner', domain="[('is_company','=',True)]")
	valid_contract_ids=fields.Many2many('account.analytic.account', compute='_get_valid_contract_ids')
	valid_contract_line_ids=fields.Many2many('account.analytic.invoice.line', compute='_get_valid_contract_line_ids')
	new_checked=fields.Boolean(help='New services are not ticked to verify them. If there is a contract line, this is ticked.')
	active=fields.Boolean(default=True)
	productcode=fields.Char(Index=True)
	ExternalRef1=fields.Char()
	ExternalRef2=fields.Char()
	friendly_name=fields.Char(Index=True)
	erp_collection=fields.Char(help="External collection / customer. Eg. Entra Tenant, DNS Owner Handle. this can be linked to a customer, contract etc. Is the rowkey in the azure storage table", readonly=True,Index=True)
	
	current_counter_value=fields.Float(string="Counted Value", help="Current reported value of the counter")
	counter_offset=fields.Float(string="Offset", help="Offset to apply")
	counter_to_bill=fields.Float(string="Bill value", compute="_calc_bill_value")
	counter_last_billed=fields.Float(string="Last billed", compute="_calc_counter_last_billed")
	current_quantity=fields.Float(help="Current quantitiy on the billing line",compute="_calc_current_quantity")
	start_date=fields.Date(readonly=True)
	renewal_date=fields.Date(readonly=True)
	autorenew=fields.Boolean(readonly=True)
	counter_date=fields.Datetime(Readonly=True)
	price=fields.Float(string="Price", help="Reported price")
	counterdef_id=fields.Char(help="PartitionKey")
	entra_tenant_id=fields.Char(help="Rowkey")
	

	@api.one
	def unlink(self):
		self.del_counterdef()
		return super(lubon_qlan_counterdefs, self).unlink()

	@api.one
	def write(self,vals):
		#self.del_counterdef()
		#pdb.set_trace()
		res= super(lubon_qlan_counterdefs, self.with_context(from_parent_object=True)).write(vals)
		if 'contract_line_id' in vals.keys():
			#pdb.set_trace()
			if vals['contract_line_id'] == self.contract_line_id.id:
				self.update_counterdef()	
		return res




	@api.onchange('o365_tenant_id')
	@api.one
	def _get_valid_contract_ids(self):
		self.valid_contract_ids=self.o365_tenant_id.qlan_tenant_id.contract_ids	

	@api.one
	def _get_valid_contract_line_ids(self):
		ids=[]
		for n in self.valid_contract_ids:
			ids.append(n.id)
		self.valid_contract_line_ids=self.env['account.analytic.invoice.line'].search(['&',('analytic_account_id','in', ids),('product_id','ilike',self.productcode)])

	@api.depends('current_counter_value')
	@api.onchange('counter_offset')
	@api.one
	def _calc_bill_value(self):
		self.counter_to_bill=self.current_counter_value+ self.counter_offset

	@api.one
	def _calc_counter_last_billed(self):
		self.counter_last_billed=self.contract_line_id.last_billed_usage

	@api.one
	def _calc_current_quantity(self):
		self.current_quantity=self.contract_line_id.quantity

	# @api.onchange('contract_line_id')
	# @api.one
	# def _change_counterdef(self):	
	# 	self.update_counterdef()




	@api.multi
	def update_counterdef(self):
		with open(os.path.expanduser('~/.odoosettings/qlanbilling.yaml')) as file:
			settings = yaml.load(file)
		url=settings['baseurl'] + '/counterdef-update/' + self.counterdef_id + '/' + str(self.contract_line_id.id or 0)
#		pdb.set_trace()
		counterdef = requests.get(  
            url,
            headers={'x-functions-key': settings['key']} )
		logging.info("url: %s, status: %d", url,counterdef.status_code)

	@api.multi
	def del_counterdef(self):
		with open(os.path.expanduser('~/.odoosettings/qlanbilling.yaml')) as file:
			settings = yaml.load(file)

		
		
		url=settings['baseurl'] + '/counterdef-delete/' + self.counterdef_id 
#		pdb.set_trace()
		counterdef = requests.get(  
            url,
            headers={'x-functions-key': settings['key']} )
		logging.info("url: %s, status: %d", url,counterdef.status_code)
#		if counterdef.status_code == 200:
#			self.unlink()

		
	@api.multi
	def assign_contract_line_id(self):
		if not self.contract_line_id:
			self.valid_contract_line_ids.search(['&',('product_id','ilike',self.productcode),])
			
	@api.multi
	def update_contract_line(self):
		if self.contract_line_id and self.current_counter_value != -1:
			self.contract_line_id.current_usage=self.counter_to_bill

	def get_counterdefs(self,o365_tenant_id=None):
		with open(os.path.expanduser('~/.odoosettings/qlanbilling.yaml')) as file:
			settings = yaml.load(file)
		if o365_tenant_id:	
			url=settings['baseurl'] + '/counterdefs/' + o365_tenant_id.entra_tenant_id 
			tenant_id=o365_tenant_id.id
		else:
			url=settings['baseurl'] + '/counterdefs/*' 
			tenant_id=False

		counterdefs = requests.get(  
            url,
            headers={'x-functions-key': settings['key']} )
		if counterdefs.json() != None:
			if 	type(counterdefs.json())==dict:
				counterdefs=[counterdefs.json()]
			else:
				counterdefs=counterdefs.json()

			for counterdef in counterdefs:
				if 'FriendlyName' in counterdef.keys():
					logging.info ("Processing friendly name: %s", counterdef['FriendlyName'])

				counter=self.search([('counterdef_id',"ilike",counterdef['PartitionKey'])])
				if not counter:
					counter=self.create(
						{
						'o365_tenant_id': tenant_id,
						'counterdef_id': counterdef['PartitionKey'],	
						'contract_line_id':int(counterdef['OdooContractLineId'])					
						}
					)
				counter.update(
					{
						'productcode': counterdef['LubonProductCode'],
#nog nodig?						'contract_line_id':int(counterdef['OdooContractLineId']),
						'erp_collection':counterdef['RowKey']
					})
				if 'ExternalRef1' in counterdef.keys():
					counter.update(
					{
						'ExternalRef1': counterdef['ExternalRef1']
					})
				if 'ExternalRef2' in counterdef.keys():
					counter.update(
					{
						'ExternalRef2': counterdef['ExternalRef2']
					})
				if 'CurrentCounterValue' in counterdef.keys():
					counter.update(
					{
						'current_counter_value': counterdef['CurrentCounterValue']
					})
				if 'FriendlyName' in counterdef.keys():
					counter.update(
					{
						'friendly_name': counterdef['FriendlyName']
					})	
				for additional in ['counter_date','start_date','renewal_date','autorenew']:		
					if additional in counterdef.keys():
						counter.update(
						{
							additional: counterdef[additional]
						})		


				if counter.contract_line_id:
					counter.partner_id=counter.contract_line_id.analytic_account_id.partner_id


class lubon_qlan_arrowservices_o365(models.Model):
	_name = 'lubon_qlan.arrowservices_o365'
	_description = 'Arrow services'
	_order='arrow_name'
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
	arrow_vendor_license_id=fields.Char()
	arrow_last_update=fields.Datetime()
	arrow_autorenew=fields.Boolean()
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
#		pdb.set_trace()

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
			self.contract_line_id.quantity=self.contract_line_id.current_usage
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
				'arrow_vendor_license_id': license['vendor_license_id'],
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
				service_id.new_checked
			else:
				service_id.active=True

			#pdb.set_trace()



class lubon_qlan_counterdef_partner(models.Model):
	_name='res.partner'
	_inherit='res.partner'
	counterdefs_ids=fields.One2many('lubon_qlan.counterdefs','partner_id')
	

class account_analytic_account(models.Model):
	_name = "account.analytic.account"
	_inherit = "account.analytic.account"
	counterdefs_ids=fields.One2many('lubon_qlan.counterdefs','partner_id')


class lubon_counterdefs_account_analytic_invoice_line(models.Model):
	_inherit = 'account.analytic.invoice.line'
	arrow_services_ids=fields.One2many('lubon_qlan.arrowservices_o365','contract_line_id')
	#counterdefs_ids=fields.One2many('lubon_qlan.counterdefs','contract_line_id')
#	counterdef_id=fields.Many2one('lubon_qlan.counterdefs', string="Counter",domain="[('partner_id','=',partner_id)]" ) #   ,('productcode','ilike',product_id)]" )
	counterdef_id=fields.Many2one('lubon_qlan.counterdefs', string="Counter",domain="[('contract_line_id','=',False)]" )
	zpartner_id=fields.Many2one(related="analytic_account_id.partner_id", zreadonly=True)
	partner_id=fields.Integer()
	

	@api.depends('counterdef_id')
	@api.onchange('counterdef_id')
	@api.one
	def _onchange_counterdef_id(self):
		self.source=self.counterdef_id.friendly_name

	@api.onchange('product_id')
	@api.one
	def _onchange_product_id(self):
		self.lookup_prices()


	@api.one
	def write(self,vals):
		#self.del_counterdef()
		if 'counterdef_id' in vals.keys():
			if vals['counterdef_id']:
#				self.env['lubon_qlan.counterdefs'].browse(vals['counterdef_id']).contract_line_id=self
				browseid=vals['counterdef_id']
			else:
				browseid=self.counterdef_id.id
		res=super(lubon_counterdefs_account_analytic_invoice_line, self.with_context(from_parent_object=True)).write(vals)
		# if vals['counterdef_id']:
		# 	self.env['lubon_qlan.counterdefs'].browse(browseid).contract_line_id=self
		# else:
		# 	self.env['lubon_qlan.counterdefs'].browse(browseid).contract_line_id=False
		if 'counterdef_id' in vals.keys():
			if vals['counterdef_id']:
				self.env['lubon_qlan.counterdefs'].browse(browseid).write(
					{'contract_line_id':self.id,
	  				 'partner_id':self.analytic_account_id.partner_id.id	
	  				}
					)
			else:
				self.env['lubon_qlan.counterdefs'].browse(browseid).write({'contract_line_id':False})
			return res 
