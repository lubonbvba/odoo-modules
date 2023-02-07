# -*- coding: utf-8 -*-
from openerp import models, fields, api
import pdb

# class lubon_sale(models.Model):
#     _name = 'lubon_sale.lubon_sale'

#     name = fields.Char()


#class sale_order(osv.osv):
#    _inherit = 'sale.order'
#    _columns = {
#        'quote_text': fields.html('Quote text'),
#        'has_discount': fields.boolean('Bottom Comment'),
#    }

class sale_order(models.Model):
	_inherit = 'sale.order'
	has_discount = fields.Boolean("Discount",default=False,help="Tick to enable discount on this quote")
	has_text = fields.Boolean("Enable text",default=False,help="Tick to enable html comments on this quote")
	frontcover = fields.Html("Qoute frontcover text", placeholder="Enter text for frontcover")
	backcover = fields.Html("Quote backcover text", placeholder="Enter text for backcover")
	contract_text = fields.Html("Contract text", placeholder="Contract text")
	quote_title = fields.Char("Quote title", help="Title that appears on the quote and in the subjext of the e-mail", required=True)
	global_discount=fields.Float("Discount")	
	contract_appendix=fields.Char(string="Title appendix page", default="Appendix 4: Product & prijsoverzicht")
	contract_term=fields.Char(default="3 jaar", string="Initial term")
	contract_start_date=fields.Date(string="Start date")
	@api.onchange('has_discount')
	def onchange_has_discount(self):
		if not self.has_discount:
			self.global_discount =0
			self.onchange_global_discount()

	@api.returns('self')	
	@api.onchange('global_discount')
	def onchange_global_discount(self):
		for line in self.order_line:
			line.discount=self.global_discount
		if not self.global_discount == 0:
			self.has_discount=True
		else:
			self.has_discount=False
		return
		self._amount_all()

	def check_discount(self):
		self.has_discount=False
		for line in self.order_line:
			if not line.discount==0:
				self.has_discount=True 	
	
	@api.multi		
	def new_quote_from_contract(self, analytic_account_id):
		order_id=self.create({
			'partner_id': analytic_account_id.partner_id.id,
			'quote_title': 'Renewal',
			'project_id': analytic_account_id.id,
		})
		lines=analytic_account_id.recurring_invoice_line_ids.sorted(key=lambda r: r.sequence)
		for line in lines:
			n=self.env['sale.order.line'].create({
				'order_id': order_id.id,
				'product_id': line.product_id.id,
				'product_uom_qty': line.quantity,
				'name': line.name,
				'discount': line.line_discount_rate,
			})



class sale_order_line(models.Model):
	_inherit = 'sale.order.line'
	tax_id = fields.Many2many(required=True)
	purchase_price_current=fields.Float(compute="_get_purchase_price_current",help="Current product purchase price.")
	price_reduce = fields.Float(string="Current", hint="Current purchase price", compute="_get_price_reduce")
	
	@api.multi
	def _get_price_reduce(self):
		#Correct error in normal odoo behaviour
		#pdb.set_trace()
		for line in self:
			line.price_reduce = line.price_unit * (1-line.discount/100)

	@api.multi	
	def _get_purchase_price_current(self):
		for line in self:
			line.purchase_price_current=line.product_id.standard_price



	# @api.onchange('discount')
	# def onchange_discount(self):
	# 	pdb.set_trace()
	# 	self.order_id.check_discount()
