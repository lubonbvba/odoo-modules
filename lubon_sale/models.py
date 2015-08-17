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


class sale_order_line(models.Model):
	_inherit = 'sale.order.line'
	tax_id = fields.Many2many(required=True)

	def _get_price_reduce(self, cr, uid, ids, field_name, arg, context=None):
		#Correct error in normal odoo behaviour
		pdb.set_trace()
		res = dict.fromkeys(ids, 0.0)
		for line in self.browse(cr, uid, ids, context=context):
			res[line.id] = line.price_unit * (1-line.discount)
		return res

	# @api.onchange('discount')
	# def onchange_discount(self):
	# 	pdb.set_trace()
	# 	self.order_id.check_discount()
