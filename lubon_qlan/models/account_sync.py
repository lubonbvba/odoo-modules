# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api, _
from datetime import datetime,timedelta
import re
import pdb,logging
#from path import path
logger = logging.getLogger(__name__)

ad_allusers_command="get-aduser -filter * -properties * "
ad_singleuser_command="get-aduser -properties * -identity "
ad_allgroups_command="get-adgroup -filter * -properties * "
ad_output_modifier=" | select-object * | convertto-json"


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
#	user_command=fields.Char(help="Command used to get users", default="get-aduser -filter * -properties * | select-object * | convertto-json")
#	group_command=fields.Char(help="Command used to get groups", default="get-adgroup -filter * -properties * | select-object * | convertto-json")

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
  		self.last_full_run_stop=fields.Datetime.now()
 		logger.info("Run_sync: End Full sync %s" % self.name) 		

 	@api.multi
 	def run_single_sync(self,identity):
 		command=ad_singleuser_command + identity + ad_output_modifier
 		result=self.endpoints_id.execute(command)
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
				adaccount.memberofstring=item['memberof']
				groups=[]
				for group in item['memberof']:
					g=self.env['lubon_qlan.adaccounts'].search([('distinguishedname',"=",group)])
					if g:
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
	alias=fields.Char() 
	mobile=fields.Char(placeholder="+32475963182") 
	samaccountname=fields.Char()
	tenant_id=fields.Many2one('lubon_qlan.tenants')
	contract_line_id=fields.Many2one('account.analytic.invoice.line')
	validcustomers_ids=fields.Many2many('res.partner')
	validcontract_ids=fields.Many2many('account.analytic.account')



	@api.multi
	@api.onchange('tenant_id')
	def set_defs(self):
		if len(self.validcustomers_ids)==1:
			self.customer_id=self.validcustomers_ids[0]
		if len(self.validcontract_ids)==1:
			self.contract_id=self.validcontract_ids[0]

	@api.multi
	@api.onchange('first_name','last_name')
	def set_alias(self):
		self.alias=self.tenant_id.code + "-"
		if self.first_name:
			self.alias += self.first_name[:2].lower()
		if self.last_name:
			self.alias += self.last_name[:2].lower()
