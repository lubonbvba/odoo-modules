# -*- coding: utf-8 -*-

from openerp import models, fields, api
import yaml
import os,requests
import pdb,logging
logger = logging.getLogger(__name__)

class account_analytic_invoice_line(models.Model):
	_name = 'account.analytic.invoice.line'
	_inherit = 'account.analytic.invoice.line'
	_sql_constraints = [('counterdef_id_unique','UNIQUE(counterdef_id)','Counterdef id can only be used one 1 contractline')]
	invoice_analytic_account_id = fields.Many2one('account.analytic.account', string="Invoice account", help="Specify the account to use when invoicing this line")
	add_to_prepaid= fields.Boolean(default=False, help="Tick if number has to be added to prepaid service units")
	product_type=fields.Selection([('work',"Worktime"),('licensed','Licensed product'),('storage','Storage product'),('rent','Rental product')])
	line_discount_rate=fields.Float(string="Discount %")
	line_reduced_price=fields.Float(string="Sales price",compute="_get_reduced_price")
	price_subtotal=fields.Float(compute="_get_reduced_price")
	sequence=fields.Integer()
	line_ok=fields.Boolean(zcompute="_set_line_state")
	usage_mandatory=fields.Boolean(default=True, help="Is usage required, -1 in current usage means not updated ?")
	last_billed_usage=fields.Float(help="Last billed number")
	current_usage=fields.Float(help="Current value of the counter, after billing it is set to -1", default=-1)
	billing_check=fields.Boolean(compute="_calculate_billing_check", string="Billing check", store=True, index=True)
	next_report_date=fields.Datetime(compute="_calculate_next_report_date", help="Due date for the next reporting/invoicing", store=True)
	source=fields.Char(help="Asset/product/user waar dit betrekking op heeft")
	counterdef_id=fields.Many2one('lubon_qlan.counterdefs', string="Counter",domain="[('contract_line_id','=',False)]" )
	line_partner_id=fields.Many2one(related="analytic_account_id.partner_id", zreadonly=True, required=True)


	@api.one
	def write(self,vals):
		#pdb.set_trace()
		if 'counterdef_id' in vals.keys():
			if vals['counterdef_id']:
				browseid=vals['counterdef_id']
			else:
				browseid=self.counterdef_id.id
		res=super(account_analytic_invoice_line, self.with_context(from_parent_object=True)).write(vals)
		if 'counterdef_id' in vals.keys():
			#pdb.set_trace()
			if vals['counterdef_id']:
				self.env['lubon_qlan.counterdefs'].browse(browseid).write(
					{'contract_line_id':self.id,
	  				 'partner_id':self.analytic_account_id.partner_id.id	
	  				}
					)
			else:
				self.env['lubon_qlan.counterdefs'].browse(browseid).write({'contract_line_id':False})
		return res 
	
	@api.model
	def zzcreate(self,vals):
		pdb.set_trace()
		if vals:
			if 'counterdef_id' in vals.keys():
				if vals['counterdef_id']:
					browseid=vals['counterdef_id']
				else:
					browseid=self.counterdef_id.id
			res=super(account_analytic_invoice_line, self).create(vals)
			if 'counterdef_id' in vals.keys():
				pdb.set_trace()
				if vals['counterdef_id']:
					self.env['lubon_qlan.counterdefs'].browse(browseid).write(
						{'contract_line_id':self.id,
						'partner_id':self.analytic_account_id.partner_id.id	
						}
						)
				else:
					self.env['lubon_qlan.counterdefs'].browse(browseid).write({'contract_line_id':False})
		else:
			res=super(account_analytic_invoice_line, self).create()

		return res 







	@api.depends('counterdef_id')
	@api.onchange('counterdef_id')
	@api.one
	def _onchange_counterdef_id(self):
		self.source=self.counterdef_id.friendly_name

	@api.onchange('product_id')
	@api.one
	def _onchange_product_id(self):
		self.lookup_prices()


	@api.multi
	@api.depends('quantity','last_billed_usage', 'current_usage','usage_mandatory')
	def _calculate_billing_check(self):
			for line in self:
				if (line.usage_mandatory and line.current_usage != line.quantity):
					line.billing_check=True
				else:
					line.billing_check=False
				

	@api.one
	@api.depends('analytic_account_id.recurring_next_date')
	def _calculate_next_report_date(self):
		for line in self:
			line.next_report_date=line.analytic_account_id.recurring_next_date	

	@api.one
	@api.depends('name')
	def _compute_display_name(self):
		#pdb.set_trace()
		self.display_name=""
		if self.name:
			self.display_name=self.name
		self.display_name+=' -' + str(self.analytic_account_id.name) + '-'
	@api.multi
	def name_get(self):
		res=[]
		for line in self:
			text=''
			if line.name:
				text=line.name.partition('\n')[0]
			text+=' (' + str(line.analytic_account_id.name) + ')'
			res.append((line.id,text ))
		return res 	

	@api.depends('line_discount_rate','price_unit', 'quantity')
	def _get_reduced_price(self):
		for record in self:
			record.line_reduced_price=record.price_unit * (1-(record.line_discount_rate/100))
			record.price_subtotal=record.quantity * record.line_reduced_price
	@api.multi
	def new_recurring_line(self,line):
#		invoice_line=self.search(['&', '&',('analytic_account_id',"=",line.order_id.project_id.id ),('product_id',"=",line.product_id.id),('name',"ilike",line.name)])
#		if not invoice_line:
		self.create({'analytic_account_id': line.order_id.project_id.id,
			'product_id': line.product_id.id,
			'price_unit': line.price_unit,	
			'name': line.name,	
			'quantity': line.product_uom_qty,	
			'line_discount_rate': line.discount,	
			'uom_id': line.product_uom.id,
			})
		# else:
		# 	invoice_line.update(
		# 		{'quantity': invoice_line.quantity + line.product_uom_qty,	
		# 		})
	@api.multi
	def copy_desc(self):
		self.name = self.product_id.display_name
		if self.source:
			self.name+= ": " + self.source

	@api.multi
	def update_quantity(self):
		self.quantity=self.current_usage

	@api.multi
	def lookup_prices(self):
		for line in self:
			pricelist=line.analytic_account_id.partner_id.property_product_pricelist
			product_id=line.product_id
			price_unit=pricelist.price_get(product_id.id,line.quantity)
			line.price_unit=price_unit[pricelist.id]
			#pdb.set_trace()
	@api.one
	def update_counter_from_contract_line(self):
		self.counterdef_id.contract_line_id=self

class account_analytic_account(models.Model):
	_name = "account.analytic.account"
	_inherit = "account.analytic.account"
	name=fields.Char(translate=False)
	check_before_invoice=fields.Boolean(help="If this field is set, invoice can only be made if ready for invoice is checked")
	# ready_for_invoice=fields.Boolean(Store=True, compute="_set_ready_for_invoice",help="This needs to be set to signal that the invoice can be made.")
	invoiced_lines=fields.One2many("account.invoice.line",'account_analytic_id', readonly=True)
	quantity_hist=fields.Float(string="Historic balance", help="Credit before using odoo contracts")
	partner_related_ids=fields.Many2many('res.partner')
	date_cutoff=fields.Date(string="Last renewal date", help="Date to use as a start date for reporting and counting hours.")

	table_description=fields.Text(help = "Info die verschijnt op de contract table afdruk.")
#	counterdef_ids=fields.One2many('lubon_qlan.counterdefs','line_contract_id')
	counterdef_ids=fields.Integer()


	@api.multi
	def calculate_reporting_fields(self):
		self.recurring_invoice_line_ids._calculate_billing_check()

	@api.multi
	def delete_recurring_lines(self):
		for line in self.recurring_invoice_line_ids:
			line.unlink()

	@api.multi
	def calculate_current_prices(self):
		for line in self.recurring_invoice_line_ids:
			line.lookup_prices()
				
	@api.multi
	def sort_lines_by_code(self):
		lines=self.recurring_invoice_line_ids.sorted(key=lambda r: r.product_id.default_code)
		n=0
		for line in lines:
			line.sequence=n
			n=n+10




	@api.multi
	def add_line_from_quote(self,line):
		for l in line:
			self.env['account.analytic.invoice.line'].new_recurring_line(line)
	
	@api.multi
	@api.depends('recurring_invoice_line_ids')
	def _set_ready_for_invoice(self):
		for item in self:
			item.ready_for_invoice=True
			for line in item.recurring_invoice_line_ids:
				if not(line.line_ok):
					item.ready_for_invoice=False


	def _prepare_invoice_line(self, cr, uid, line, fiscal_position, context=None):
		
		res=super(account_analytic_account, self)._prepare_invoice_line(cr, uid,line,fiscal_position)

		res.update({'account_analytic_id': line.invoice_analytic_account_id.id})
		res.update({'discount': line.line_discount_rate})
		res.update({'sequence': line.sequence})

		#pdb.set_trace()
		line.last_billed_usage=line.current_usage
		if line.usage_mandatory:
			#set current usage to -1 if usage reporting is mandatory
			line.current_usage=-1

		if line.add_to_prepaid:
			line.analytic_account_id.quantity_max += line.quantity
		#line.next_report_date=self.recurring_next_date
		

		return res
	def _prepare_invoice_data(self, cr, uid, contract, context=None):
		res=super(account_analytic_account, self)._prepare_invoice_data( cr, uid, contract)
		res.update({'comment': contract.description})
		res.update({'origin': contract.name})
		
		return res
    



    



	@api.multi
	def make_quote_from_contract(self):
		self.env['sale.order'].new_quote_from_contract(self)


class sale_order(models.Model):
	_inherit = 'sale.order'
	@api.multi
	def add_to_contract(self):
		for quote in self:
			quote.project_id.update(
				{'recurring_invoices': True,
				'pricelist_id': quote.pricelist_id.id,
				'description': quote.note
				})
			#for oldline in quote.project_id.recurring_invoice_line_ids:
			#	oldline.unlink()		
			for line in quote.order_line.sorted(key=lambda r: r.sequence):
				quote.project_id.add_line_from_quote(line)
			quote.state='done'


class lubon_qlan_counterdefs(models.Model):
	_name = 'lubon_qlan.counterdefs'
	_description = 'Qlan Counter definitions'
	_rec_name = 'friendly_name'
	name=fields.Char()
	
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
	
	line_contract_id=fields.Many2one(related="contract_line_id.analytic_account_id", zreadonly=True)

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
			if vals['contract_line_id'] == self.contract_line_id.id:
				self.update_counterdef()	
		return res




	@api.onchange('entra_tenant_id')
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
	def lookupinvoiceline(self):
		for line in self:
			line.contract_line_id= self.env['account.analytic.invoice.line'].search([('counterdef_id',"=",line.id)])


	@api.multi
	def lookuptenant(self):
		for line in self:
			line.o365_tenant_id= self.env['lubon_qlan.tenants_o365'].search([('entra_tenant_id',"=",line.erp_collection)])


	@api.multi
	def update_counterdef(self):
		with open(os.path.expanduser('~/.odoosettings/qlanbilling.yaml')) as file:
			settings = yaml.load(file)
 		for line in self:		
			url=settings['baseurl'] + '/counterdef-update/' + line.counterdef_id + '/' + str(line.contract_line_id.id or 0)
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
	def refresh_counterdefs(self):
		with open(os.path.expanduser('~/.odoosettings/qlanbilling.yaml')) as file:
			settings = yaml.load(file)
		for line in self:
			if line.counterdef_id:
				values={}
				url=settings['baseurl'] + '/counterdefs/*/*/' + line.counterdef_id
				counterdefs = requests.get(  
            	url,
            	headers={'x-functions-key': settings['key']} )
				if counterdefs.json() != None:
					if 	type(counterdefs.json())==dict:
						counterdefs=counterdefs.json()
						if 'CurrentCounterValue' in counterdefs.keys():
							values['current_counter_value'] = counterdefs['CurrentCounterValue']	
						for x in ['counter_date','start_date','renewal_date','autorenew']:
							if x in counterdefs.keys():
								values[x]=counterdefs[x]
						#pdb.set_trace()
						line.update(values)						

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
				values={}
				if tenant_id:
					values['o365_tenant_id']=tenant_id
				if counter.contract_line_id.id != int(counterdef['OdooContractLineId']):
					values['contract_line_id']=int(counterdef['OdooContractLineId'])
				values['productcode']=counterdef['LubonProductCode']
				values['erp_collection']=counterdef['RowKey']

				# counter.update(
				# 	{
				# 		'productcode': counterdef['LubonProductCode'],
				# 		'contract_line_id':int(counterdef['OdooContractLineId']),
				# 		'erp_collection':counterdef['RowKey']
				# 	})
				# if 'ExternalRef1' in counterdef.keys():
				# 	counter.update(
				# 	{
				# 		'ExternalRef1': counterdef['ExternalRef1']
				# 	})
				# if 'ExternalRef2' in counterdef.keys():
				# 	counter.update(
				# 	{
				# 		'ExternalRef2': counterdef['ExternalRef2']
				# 	})
				if 'CurrentCounterValue' in counterdef.keys():
					values['current_counter_value']=counterdef['CurrentCounterValue']
					# counter.update(
					# {
					# 	'current_counter_value': counterdef['CurrentCounterValue']
					# })
				if 'FriendlyName' in counterdef.keys():
					values['friendly_name']=counterdef['FriendlyName']
					# counter.update(
					# {
					# 	'friendly_name': counterdef['FriendlyName']
					# })	
				for additional in ['counter_date','start_date','renewal_date','autorenew','ExternalRef1','ExternalRef2']:		
					if additional in counterdef.keys():
						values[additional]=counterdef[additional]
						# counter.update(
						# {
						# 	additional: counterdef[additional]
					# })		
				#pdb.set_trace()
				counter.update(values)
				if counter.contract_line_id:
					counter.partner_id=counter.contract_line_id.analytic_account_id.partner_id


class lubon_qlan_counterdef_partner(models.Model):
	_name='res.partner'
	_inherit='res.partner'
	counterdefs_ids=fields.One2many('lubon_qlan.counterdefs','partner_id')
	
