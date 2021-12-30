# -*- coding: utf-8 -*-

from openerp import models, fields, api
import pdb

class lubon_qlan_billing_history(models.Model):
	_name = 'lubon_qlan.billing_history'
	_description = 'Billing detail lines'

	related_model=fields.Char(help="Model that originated this line")
	related_id=fields.Integer()
	contract_line_id=fields.Many2one('account.analytic.invoice.line')
	date_start=fields.Datetime()
	date_end=fields.Datetime()
	description=fields.Char()

	@api.multi
	def verify_billing_history_line(self,related,number,contract_line_id,description):
		#pdb.set_trace()
		
		current_line=self.search([('related_model','ilike', str(related._model) ),('related_id','=',related.id)])
		if not current_line:
			self.create({
				'related_model': str(related._model),
				'related_id': related.id,
				'description': description,
				'contract_line_id': contract_line_id.id,
			})



class account_analytic_invoice_line(models.Model):
	_inherit = 'account.analytic.invoice.line'

	invoice_analytic_account_id = fields.Many2one('account.analytic.account', string="Invoice account", help="Specify the account to use when invoicing this line")
	add_to_prepaid= fields.Boolean(default=False, help="Tick if number has to be added to prepaid service units")
	product_type=fields.Selection([('work',"Worktime"),('licensed','Licensed product'),('storage','Storage product'),('rent','Rental product')])
	line_discount_rate=fields.Float(string="Discount %")
	line_reduced_price=fields.Float(string="Sales price",compute="_get_reduced_price")
	price_subtotal=fields.Float(compute="_get_reduced_price")
	sequence=fields.Integer()
	line_ok=fields.Boolean(compute="_set_line_state")
	adaccount_ids=fields.One2many('lubon_qlan.adaccounts','contract_line_id')
	billing_history_ids=fields.One2many('lubon_qlan.billing_history','contract_line_id')
	counted_items=fields.Integer(compute="_count_items", string="Counted (old)", help="This number is the total of items counted in the tenant")
	used_items=fields.Integer(compute="_count_used", string="Used (old)", help="The number of items used/assigned")
	billing_history_counted_items=fields.Integer(compute="_billing_history_count_items", string="Counted", help="This number is the total of items counted in the tenant")





	@api.multi
	@api.depends('adaccount_ids')
	def _count_items(self):
		for line in self:
			#pdb.set_trace()
			line.counted_items=len(line.adaccount_ids)
	@api.multi
	@api.depends('counted_items')
	def _set_line_state(self):
		for line in self:
			line.line_ok=True
			if line.adaccount_ids:
				if line.counted_items != line.quantity:
					line.line_ok=False
	@api.multi
	def _count_used(self):
		
		for line in self:
			n=0
			if line.product_id.reference_model:
				lines=self.env[line.product_id.reference_model.model].search([('contract_line_id','=',line.id)])
				if lines:
					for item in lines:
						n+=1
			line.used_items=n


	@api.multi
	@api.depends('billing_history_ids')
	def _billing_history_count_items(self):
		for line in self:
			#pdb.set_trace()
			line.billing_history_counted_items=len(line.billing_history_ids)



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
				text=line.name
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
		invoice_line=self.search(['&', '&',('analytic_account_id',"=",line.order_id.project_id.id ),('product_id',"=",line.product_id.id),('name',"ilike",line.name)])
		if not invoice_line:
			self.create({'analytic_account_id': line.order_id.project_id.id,
				'product_id': line.product_id.id,
				'price_unit': line.price_unit,	
				'name': line.name,	
				'quantity': line.product_uom_qty,	
				'line_discount_rate': line.discount,	
				'uom_id': line.product_uom.id,
				})
		else:
			invoice_line.update(
				{'quantity': invoice_line.quantity + line.product_uom_qty,	
				})





class account_analytic_account(models.Model):
	_name = "account.analytic.account"
	_inherit = "account.analytic.account"
	name=fields.Char(translate=False)
	check_before_invoice=fields.Boolean(help="If this field is set, invoice can only be made if ready for invoice is checked")
	ready_for_invoice=fields.Boolean(Store=True, compute="_set_ready_for_invoice",help="This needs to be set to signal that the invoice can be made.")
	invoiced_lines=fields.One2many("account.invoice.line",'account_analytic_id', readonly=True)
	quantity_hist=fields.Float(string="Historic balance", help="Credit before using odoo contracts")
	partner_related_ids=fields.Many2many('res.partner')
	date_cutoff=fields.Date(string="Last renewal date", help="Date to use as a start date for reporting and counting hours.")
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
		if line.add_to_prepaid:
			line.analytic_account_id.quantity_max += line.quantity
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
			for line in quote.order_line.sorted(key=lambda r: r.sequence):
				quote.project_id.add_line_from_quote(line)
			quote.state='done'



