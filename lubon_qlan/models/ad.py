from openerp import models, fields, api,exceptions,_
import csv,os,string,datetime,logging
from path import Path
import pdb, base64
import dns.resolver
from os.path import expanduser
import openerp


logger = logging.getLogger(__name__)

class lubon_qlan_tenants(models.Model):
    _name = 'lubon_qlan.tenants'
    _inherit = 'mail.thread'
    _description = 'Tenant'
    _rec_name = 'code'
    _sql_constraints = [('code_unique','UNIQUE(code)','Code has to be unique')]
    _order = 'code' 
    active=fields.Boolean(default=True)
    code = fields.Char(oldname='name', required=True, help='Tenant code', index=True )
    tenant_name = fields.Char(string='Name', required=True, oldname='descript_name', help="Descriptive name of the tenant")
    qadm_password = fields.Char(help="Password for qadm@upn user")
    qtest_password = fields.Char()
    upn = fields.Char()
    ip = fields.Char(string='DC IP', help='Datacenter IP range')
    is_telephony=fields.Boolean()
    is_citrix=fields.Boolean()
    ip_ids=fields.One2many('lubon_qlan.ip','tenant_id')
    vlan_ids=fields.One2many('lubon_qlan.vlan','tenant_id')
	
    reseller_partner_id=fields.Many2one('res.partner')
    cmd_endpoint=fields.Many2one('cmd_execute.endpoints')
    contract_ids=fields.Many2many('account.analytic.account', String="Contracts")
    account_source_ids=fields.One2many('lubon_qlan.account_source','tenant_id')
    default_logon_script=fields.Char()
    default_password_never_expires=fields.Boolean()

    adaccounts_ids=fields.One2many('lubon_qlan.adaccounts', 'tenant_id', domain=lambda self: [('account_created', '=', True)],auto_join=True )
    adusers_ids=fields.One2many('lubon_qlan.adusers', 'tenant_id', domain=lambda self: [('account_created', '=', True)],auto_join=True )
    adgroups_ids=fields.One2many('lubon_qlan.adgroups', 'tenant_id', domain=lambda self: [('account_created', '=', True)],auto_join=True )
    assets_ids=fields.One2many('lubon_qlan.assets', 'tenant_id')
    users_o365_ids=fields.One2many('lubon_qlan.users_o365', 'qlan_tenant_id')
    billingconfig_tenants_ad_ids=fields.One2many('lubon_qlan.billingconfig_tenant_ad', 'qlan_tenant_id')
    credential_ids=fields.One2many('lubon_credentials.credentials','tenant_id')
    filemaker_site_id=fields.Char(string='Filemaker site')
    
    domains_o365_ids=fields.One2many('lubon_qlan.domains_o365','qlan_tenant_id')
    validcustomers_ids=fields.Many2many('res.partner', string="Customers", compute="_getvalidcustomer_ids")
    main_contact=fields.Many2one('res.partner', string="Main contact", domain="[['type','=','contact'],['is_company','=',False]]")
#	qlan_adaccounts_import_ids=fields.One2many('lubon_qlan_adaccounts_import','tenant')

    vm_glacier_cleanup=fields.Boolean(help='Cleanup glacier automatically')
    vm_glacier_month_retention_age=fields.Integer(default=180, string='Retention days month', help="Retention time in days for the monthly backups")
    vm_glacier_month_retention_num=fields.Integer(default=6,string='Monthly minimum #', help="Minimum number of monthly backups to keep")
    vm_glacier_week_retention_age=fields.Integer(default=90,string='Retention days week', help="Retention time in days for the weekly backups")
    vm_glacier_week_retention_num=fields.Integer(default=13,string='Weekly minimum #', help="Minimum number of weekly backups to keep")

    # @api.multi
    # def name_get(self):
    #     res=[]
    #     for line in self:
    #         res.append((line.id,line.code + " - " + line.tenant_name))
    #     return res
	
# 	@api.model
# 	def name_search(self, name, args=None, operator='ilike', limit=100):
# 		args = args or []
# #		recs = self.browse()
# #		logger.info("Name search: %s", name)

# 		recs = self.search(['|',('tenant_name', 'ilike', name),('code', 'ilike', name), ] + args, limit=limit)
# 		logger.info("Tenant name search: %s Found :%d", name, len(recs))
# 		if len(recs) == 0:
# 			pdb.set_trace()
# 		return recs.name_get()


    def _getvalidcustomer_ids(self):
        for rec in self.contract_ids:
            self.validcustomers_ids=self.validcustomers_ids + rec.partner_id
    @api.one
    def _adaccounts_count(self):
        self.adaccounts_count=len(self.adaccounts_ids)
    adaccounts_count=fields.Integer(compute=_adaccounts_count)

    @api.one
    def _adusers_count(self):
        self.adusers_count=len(self.adusers_ids)
    adusers_count=fields.Integer(compute=_adusers_count)

    @api.one
    def _adgroups_count(self):
        self.adgroups_count=len(self.adgroups_ids)
    adgroups_count=fields.Integer(compute=_adgroups_count)

    @api.one
    def _contracts_count(self):
        self.contracts_count=len(self.contract_ids)
    contracts_count=fields.Integer(compute=_contracts_count)
	
    @api.multi
    def refresh_licenses_ad(self,context):
        for user in self.adusers_ids:
            user.refresh_licenses_ad(user)
        # for o365tenant in self.users_o365_ids:
        #     o365tenant.refresh_thistenant_o365(self)



    @api.multi
    def set_glacier_for_all_vm(self):
        for vm in self.assets_ids:
            if vm.asset_type == 'vm' and not vm.vm_glacier_block:
                vm.vm_glacier_cleanup=self.vm_glacier_cleanup
                vm.vm_glacier_week_retention_num=self.vm_glacier_week_retention_num
                vm.vm_glacier_week_retention_age=self.vm_glacier_week_retention_age
                vm.vm_glacier_month_retention_num=self.vm_glacier_month_retention_num
                vm.vm_glacier_month_retention_age=self.vm_glacier_month_retention_age


class lubon_qlan_adaccounts(models.Model):
	_name = 'lubon_qlan.adaccounts'
	_description = "AD Account"
	_inherit = ['mail.thread','ir.needaction_mixin']
	_sql_constraints = [('guid_unique','UNIQUE(objectguid)','objectguid has to be unique'),('distinguishedname_unique','UNIQUE(distinguishedname, account_created)','distinguishedname has to be unique')]
	_rec_name = 'name'
	_mail_post_access = 'read'
	_track = {
        'product': {
            'lubon_qlan.mt_adaccount_changed': lambda self, cr, uid, obj, ctx=None: True,
        },
         'tenant_id': {
            'lubon_qlan.mt_adaccount_created': lambda self, cr, uid, obj, ctx=None: True,
        },
         'ad_enabled': {
            'lubon_qlan.mt_adaccount_deactivated': lambda self, cr, uid, obj, ctx=None: not obj.ad_enabled,
            'lubon_qlan.mt_adaccount_activated': lambda self, cr, uid, obj, ctx=None: obj.ad_enabled,
        },

    }


    #qlan fields
	tenant_id=fields.Many2one('lubon_qlan.tenants',track_visibility='onchange') #, required=True)
	active=fields.Boolean(default=True)
	account_created=fields.Boolean(default=True, track_visibility='onchange')
	account_source_id=fields.Many2one('lubon_qlan.account_source')
	name=fields.Char()
	displayname=fields.Char()
	product=fields.Char(track_visibility='onchange')
	date_first=fields.Datetime(help="Date of first import")
	date_last=fields.Datetime(help="Date last seen")
	person_id=fields.Many2one('res.partner', string="Related person", domain="['&',('type','=','contact'),('parent_id','in', validcustomers_ids[0][2])]")
	contract_id=fields.Many2one('account.analytic.account', string="Contract" )
	validcustomers_ids=fields.Many2many('res.partner', compute='_getvalidcustomer_ids',)
	validcontract_ids=fields.Many2many('account.analytic.account', compute='_getvalidcontract_ids',)
	contract_line_id=fields.Many2one('account.analytic.invoice.line', domain="['&',('name','ilike',product),('analytic_account_id','in', validcontract_ids[0][2])]")	
	ad_date_created=fields.Datetime(help="Date created in ad")

	#adobject fields
	distinguishedname=fields.Char(index=True)
	objectguid=fields.Char(required=True, index=True)
	memberofstring=fields.Char(help="String used to detect changes in group membership.")
	memberof=fields.Many2many('lubon_qlan.adaccounts',relation='lubon_qlan_adaccounts_groups',column1="member",column2="container")
	members=fields.Many2many('lubon_qlan.adaccounts',relation='lubon_qlan_adaccounts_groups', column1="container",column2="member" )
	membercount=fields.Integer(string="Nr Memb")
	email_address_ids=fields.One2many('lubon_qlan.email_address','adaccounts_id')

	@api.onchange('tenant_id')
	@api.one
	def _getvalidcontract_ids(self):
		self.validcontract_ids=self.tenant_id.contract_ids

	@api.onchange('tenant_id')
	@api.one
	def _getvalidcustomer_ids(self):
		self.validcustomers_ids=self.tenant_id.validcustomers_ids

	@api.onchange('person_id')
	@api.one
	def _getpersonname(self):
		self.name=self.person_id.name
	
	@api.onchange('account_created')
	@api.one
	def check_product(self):
		if not self.account_created:
			self.contract_line_id=False

	@api.multi
	def checkmailaddresses(self,addresslist):
		if addresslist:
			current_list=self.email_address_ids
			for address in addresslist:
				email=self.email_address_ids.search([('email_address','ilike',address)])
				if not email:
					email=self.email_address_ids.create({
						'email_address':address,
						'adaccounts_id':self.id,
						})
				email.email_address=address	
				email.is_default= 'SMTP' in email.email_address
				current_list=current_list - email
			for email in current_list:
				email.unlink()
		

class lubon_qlan_adusers(models.Model):
    _name = 'lubon_qlan.adusers'
    _inherit = ['mail.thread']
    _inherits = {'lubon_qlan.adaccounts':'account_id'}
    _description = "AD Users"	#ad user fields
    _rec_name='name'
    account_id=fields.Many2one('lubon_qlan.adaccounts', required=True, ondelete='cascade')
    samaccountname=fields.Char()
    logonname=fields.Char()
    last_passwd_change=fields.Datetime(help="Last password change")
    last_logon=fields.Datetime(help="Last logon date")
    ad_enabled=fields.Boolean(string="Enabled",default=True,track_visibility='onchange')
    ad_lockedout=fields.Boolean(string="AD Locked",track_visibility='onchange')
    exc_mb_size=fields.Float(string="Mailbox size")
    xasessions_ids=fields.One2many('lubon_qlan.xasessions','adaccount_id')
    legacyexchangedn=fields.Char()
    mailnickname=fields.Char()
    mail=fields.Char()
    scriptpath=fields.Char()
    targetaddress=fields.Char()
    objectclass=fields.Char()
    first_name=fields.Char()
    last_name=fields.Char()
    mobile=fields.Char()
    user_licenses_ids=fields.One2many('lubon_qlan.users_licenses_ad','user_ad_id')
    licensing_manual=fields.Boolean()

    @api.multi
    def refresh_licenses_ad(self,context=None):
        self.env['lubon_qlan.users_licenses_ad'].refresh(self)


    @api.multi
    def refresh(self):
        self.account_source_id.run_single_sync(self.objectguid)

    @api.multi
    def disable_user(self):
        parameters={
            'identity':self.objectguid,
        }
        cmd={'parameters':parameters,
            'cmd':'disable-adaccount',
            
            }	
        self.tenant_id.cmd_endpoint.execute_json(cmd,debug=False)
        self.refresh()

    @api.multi
    def enable_user(self):
        parameters={
            'identity':self.objectguid,
        }
        cmd={'parameters':parameters,
            'cmd':'enable-adaccount',
            
            }	
        self.tenant_id.cmd_endpoint.execute_json(cmd,debug=False)
        self.refresh()
    @api.multi
    def update_values(self):
        # context = self.env.context.copy()
        # context['cmd_execute_object'] = self.id
        # action = {
        # 'name': self.name,
        # 'view_type': 'form',
        # 'view_mode': 'form',
        # 'res_model': 'lubon_qlan.new_aduser',
        # 'context': context,
        # 'type': 'ir.actions.act_window',
        # 'target': 'new',
        # 'domain': [],
        # }      
        # return action
        cmd=self.env['cmd_execute.command'].browse(self.env.ref('lubon_qlan.cm_update_ad_user').id)
        action=cmd.run_command(self)
        return action


class lubon_qlan_email_address(models.Model):
	_name = 'lubon_qlan.email_address'
	_order = 'is_default DESC, email_address'
	email_address=fields.Char()
	is_default=fields.Boolean()
	adaccounts_id=fields.Many2one('lubon_qlan.adaccounts')


class lubon_qlan_groups(models.Model):
	_name = 'lubon_qlan.adgroups'
	_inherit = ['mail.thread']
	_inherits = {'lubon_qlan.adaccounts':'account_id'}
	_description = "AD Groups"	#ad user fields
	account_id=fields.Many2one('lubon_qlan.adaccounts', required=True,ondelete='cascade')

class lubon_qlan_users_license_ad(models.Model):
    _name = 'lubon_qlan.users_licenses_ad'
    _description = 'AD user assigned skus'
    _sql_constraints=[('user_and_ad_group','UNIQUE(user_ad_id,prd_group_id)','Model lubon_qlan_users_license_ad: Combination user/grp unique')]

    user_ad_id = fields.Many2one('lubon_qlan.adusers',ondelete='cascade')
    billingconfig_tenant_ad=fields.Many2one('lubon_qlan.billingconfig_tenant_ad', ondelete='cascade')
    prd_group_id=fields.Many2one("lubon_qlan.adaccounts")
    qlan_tenant_id=fields.Many2one('lubon_qlan.tenants', compute='_calculate_tenant_id',ondelete='cascade')


    @api.one
    @api.depends('user_ad_id')
    def _calculate_tenant_id(self):
        self.qlan_tenant_id=self.user_ad_id.tenant_id


    @api.multi
    def refresh(self,user_id):
        if not user_id.licensing_manual:
            for config in user_id.tenant_id.billingconfig_tenants_ad_ids:
                if not(config.manual_exception):
                    activelicense = self.search ([('billingconfig_tenant_ad','=',config.id),('user_ad_id','=',user_id.id),('prd_group_id','=',config.ad_groups_licenses_id.id)])
                    if config.ad_groups_licenses_id in user_id.memberof:
#                        activelicense = self.search ([('billingconfig_tenant_ad','=',config.id),('user_ad_id','=',user_id.id),('prd_group_id','=',config.ad_groups_licenses_id.id)])
                        if not activelicense:
                            activelicense=self.create({
                                'billingconfig_tenant_ad':config.id,
                                'user_ad_id':user_id.id,
                                'prd_group_id': config.ad_groups_licenses_id.id
                            })
                    else:
                        if activelicense:
                            activelicense.unlink()

        for activelicense in user_id.user_licenses_ids:
            self.env['lubon_qlan.billing_history'].verify_billing_history_line(activelicense,1,activelicense.billingconfig_tenant_ad.contract_line_id,"QLAN license: %s" % activelicense.user_ad_id.name,related_user=user_id,owner=user_id.logonname.lower())            

        
        #pdb.set_trace()







class lubon_qlan_billingconfig_tenant_ad(models.Model):
    _name = 'lubon_qlan.billingconfig_tenant_ad'
    _description = 'AD tenant billing config'
    _sql_constraints=[('contract_line_and_ad_group','UNIQUE(contract_line_id,ad_groups_licenses_id)','Contract and Group unique')]
    contract_line_id=fields.Many2one('account.analytic.invoice.line', domain="[('analytic_account_id','in', valid_contract_ids[0][2])]", zrequired=True)
    manual_exception=fields.Boolean(help="Manual created entry to set on exceptions")
    remark=fields.Char()
    ad_groups_licenses_id=fields.Many2one('lubon_qlan.adaccounts',string='AD Licensing group')
    qlan_tenant_id=fields.Many2one('lubon_qlan.tenants', ondelete='cascade', required=True)
    users_license_ad_ids=fields.One2many('lubon_qlan.users_licenses_ad','billingconfig_tenant_ad')
    users_license_ad_ids_count=fields.Integer(compute='_compute_users_license_ad_ids_count', index=True)
	# valid_domains_o365_ids=fields.Many2many('lubon_qlan.domains_o365', compute='_get_valid_domains_ad_ids')
    valid_contract_ids=fields.Many2many('account.analytic.account', compute='_get_valid_contract_ids')
#	valid_ad_groups_ids=fields.Many2many('lubon_qlan.subscribedskus_o365', compute='_get_valid_ad_groups_ids')

	# @api.multi
	# def name_get(self):
	# 	res=[]
	# 	for line in self:
	# 		if line.domains_o365_id.name:
	# 			res.append((line.id,line.domains_o365_id.name + " - " + line.subscribedskus_o365_id.friendly_name  ))
	# 		if line.manual_exception:
	# 			res.append((line.id, "Manual - " + line.subscribedskus_o365_id.friendly_name + " " + line.remark ))	
	# 	return res

    @api.one
    @api.depends('users_license_ad_ids')
    def _compute_users_license_ad_ids_count(self):
        self.users_license_ad_ids_count=len(self.users_license_ad_ids)

    @api.multi
    def name_get(self):
        res=[]
        for line in self:
            if line.manual_exception:
                res.append((line.id, "Manual - " + line.ad_groups_licenses_id.name + " " + line.remark ))	
            else:
                res.append((line.id, line.ad_groups_licenses_id.name))	
        return res


    @api.onchange('qlan_tenant_id')
    @api.one
    def _get_valid_contract_ids(self):
        self.valid_contract_ids=self.qlan_tenant_id.contract_ids
		#pdb.set_trace()

#	@api.onchange('qlan_tenant_id')
#	@api.one
#	def _get_valid_adgroups_ids(self):
#		self.valid_ad_groups_ids=self.qlan_tenant_id.ad_groups_licenses_ids