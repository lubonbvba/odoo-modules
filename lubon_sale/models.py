# -*- coding: utf-8 -*-
from openerp import models, fields, api


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
        frontcover = fields.Html("Frontcover text", placeholder="Enter text for frontcover")
	backcover = fields.Html("Backcover text", placeholder="Enter text for backcover")

	quote_title = fields.Char("Quote title", help="Title that appears on the quote and in the subjext of the e-mail", required=True)


class sale_order_line(models.Model):
        _inherit = 'sale.order.line'
	tax_id = fields.Many2many(required=True)

	@api.onchange('discount')
	def onchange_discount(self):
	    # set auto-changing field
#	    ipdb.set_trace()	
	    self.discount = self.discount
	    # Can optionally return a warning and domains
#	    return {
#        	'warning': {
#	            'title': "Something bad happened",
#	            'message': "It was very bad indeed",
#	        }
#	    }
