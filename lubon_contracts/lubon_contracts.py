# -*- coding: utf-8 -*-

from openerp import models, fields, api
import pdb

class account_analytic_invoice_line(models.Model):
	_inherit = 'account.analytic.invoice.line'

	invoice_analytic_account_id = fields.Many2one('account.analytic.account', string="Invoice account", help="Specify the account to use when invoicing this line")
	add_to_prepaid= fields.Boolean(default=False, help="Tick if number has to be added to prepaid service units")
	product_type=fields.Selection([('work',"Worktime"),('licensed','Licensed product'),('storage','Storage product'),('rent','Rental product')])
	line_discount_rate=fields.Float(string="Discount %")
	line_reduced_price=fields.Float(string="Sales price",compute="_get_reduced_price")
	price_subtotal=fields.Float(compute="_get_reduced_price")
	sequence=fields.Integer()


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
	check_before_invoice=fields.Boolean(help="If this field is set, invoice can only be made if ready for invoice is checked")
	ready_for_invoice=fields.Boolean(help="This needs to be set to signal that the invoice can be made.")
	@api.multi
	def add_line_from_quote(self,line):
		for l in line:
			self.env['account.analytic.invoice.line'].new_recurring_line(line)

	
	def _prepare_invoice_line(self, cr, uid, line, fiscal_position, context=None):
		
		res=super(account_analytic_account, self)._prepare_invoice_line(cr, uid,line,fiscal_position)

		res.update({'account_analytic_id': line.invoice_analytic_account_id.id})
		res.update({'discount': line.line_discount_rate})
		#pdb.set_trace()
		if line.add_to_prepaid:
			line.analytic_account_id.quantity_max += line.quantity
		return res
	def _prepare_invoice_data(self, cr, uid, contract, context=None):
		res=super(account_analytic_account, self)._prepare_invoice_data( cr, uid, contract)
		res.update({'comment': contract.description})
		return res


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



