# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api,exceptions, _
from datetime import datetime,timedelta
from passgen import passgen
import re
import pdb,logging
#from path import path
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
	user_o365_id = fields.Many2one('lubon_qlan.users_o365', ondelete='cascade')
	subscribedskus_o365 = fields.Many2one('lubon_qlan.subscribedskus_o365',ondelete='cascade')
	billingconfig_tenant_o365=fields.Many2one('lubon_qlan.billingconfig_tenant_o365')
#	billing_history_ids= fields.One2many('lubon_qlan.billing_history','related_user_id')
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
			if len(newsku)!=1:
				logger.error("Newsku !=1 in refresh")
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
	subscribedskus_o365_id=fields.Many2one('lubon_qlan.subscribedskus_o365',domain="[('invoicable','=',True),('id','in',valid_subscribedskus_o365_ids[0][2])]", required=True)
	o365_tenant_id=fields.Many2one('lubon_qlan.tenants_o365', ondelete='cascade', required=True)
	domains_o365_id=fields.Many2one('lubon_qlan.domains_o365', domain="[('id','in',valid_domains_o365_ids[0][2]),('used_for_billing','=',True)]", zrequired=True)
	qlan_tenant_id=fields.Many2one('lubon_qlan.tenants', ondelete='cascade', required=True)
	contract_line_id=fields.Many2one('account.analytic.invoice.line', domain="[('analytic_account_id','in', valid_contract_ids[0][2])]", zrequired=True)
	manual_exception=fields.Boolean(help="Manual created entry to set on exceptions")
	remark=fields.Char()
	valid_domains_o365_ids=fields.Many2many('lubon_qlan.domains_o365', compute='_get_valid_domains_o365_ids')
	valid_contract_ids=fields.Many2many('account.analytic.account', compute='_get_valid_contract_ids')
	valid_subscribedskus_o365_ids=fields.Many2many('lubon_qlan.subscribedskus_o365', compute='_get_valid_subscribedskus_o365_ids')

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

