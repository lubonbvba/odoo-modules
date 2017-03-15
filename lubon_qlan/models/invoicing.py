# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api, _
import csv,os,string,pdb
#from path import path
import openerp.addons.decimal_precision as dp

class account_analytic_line(models.Model):
	_inherit= "account.analytic.line"
	onsite=fields.Boolean(string="On site", help="Tick if on site intervention")
	fullday=fields.Boolean(string="Full day", help="Tick if full day intervention")
	qty_invoice=fields.Float(help = "Quantity to be invoiced",compute='_calculate_qty_invoice')
	amount_hours=fields.Float(string="Amount work",compute='_calculate_invoicable', store=True)
	amount_travel=fields.Float(string="Travel costs",compute='_calculate_invoicable', store=True)
	amount_total=fields.Float(string= "Total line",compute='_calculate_invoicable', store=True)
	rate_work=fields.Float(string="Unit rate", help="Rate per hr/day used, depending on what is applicable")
	
	@api.multi
#	@api.one
#	@api.onchange('unit_amount',)
	def zzon_change_unit_amount(self, prod_id, quantity, company_id, unit=False, journal_id=False):
		if self.fullday:
			self.qty_invoice=1
		else:	
			self.qty_invoice = int((self.unit_amount * 4) + 0.99)
			self.qty_invoice = self.qty_invoice / 4
#		pdb.set_trace()
#		self = self.with_context(from_parent_object=True)
#		pdb.set_trace()
		return super(account_analytic_line, self.with_context(from_parent_object=True)).on_change_unit_amount(prod_id, quantity, company_id,unit,journal_id)

	@api.one 
	def _calculate_qty_invoice(self):
		if self.fullday:
			self.qty_invoice=1
		else:	
			self.qty_invoice = int((self.unit_amount * 4) + 0.99)
			self.qty_invoice = self.qty_invoice / 4

	@api.one 
	@api.depends('fullday', 'onsite', 'to_invoice')
	def _calculate_invoicable(self):
		if not self.invoice_id:
			#calculate fields only if no invoice exists
			self._calculate_qty_invoice()
			self.amount_travel=0
			if self.fullday:
				self.rate_work= self.account_id.partner_id.rate_day
			else:	
				self.rate_work=self.account_id.partner_id.rate_hr
				if self.onsite:	
					self.amount_travel	= self.account_id.partner_id.rate_travel

			self.amount_hours= self.qty_invoice * self.rate_work * (100-self.to_invoice.factor)/100	
			self.amount_total=self.amount_hours + self.amount_travel
			#self.write({'rate_work': 998})

class add_hours_wizard(models.TransientModel):
	_name="add_hours.wizard"
	def _default_partner(self):
#		pdb.set_trace() 
		return self.env['account.invoice'].browse(self.env['account.invoice']._context.get('active_id')).partner_id
	def _default_hours_ids(self):
		search_domain=[('account_id.partner_id', '=', self.env['account.invoice'].browse(self._context.get('active_id')).partner_id.id)]
		search_domain=search_domain + [('invoice_id','=',False)]
		search_domain=search_domain + [('to_invoice','!=',False)]

		return self.env['account.analytic.line'].search(search_domain)
	def _default_invoice(self):
		#pdb.set_trace() 
		return self.env['account.invoice'].browse(self.env['account.invoice']._context.get('active_id'))		

	def _default_product(self):
		#pdb.set_trace()
		return self.env['account.invoice'].browse(self.env['account.invoice']._context.get('active_id')).company_id.default_hours_product

	partner_id = fields.Many2one('res.partner', string="Customer", readonly=True, default=_default_partner)
	product_id = fields.Many2one('product.product', string="Product" , required=True, default=_default_product )
	invoice_id = fields.Many2one('account.invoice', readonly=True, string="Invoice", default=_default_invoice)
	hours_ids=fields.Many2many("account.analytic.line", default=_default_hours_ids)
	
	@api.multi
	def add_hours_to_invoice(self):
#		obj_invoice_lines=self.invoice_id.create({'product_id':self.product_id})
		total=0
		for l in self.hours_ids:
			l._calculate_invoicable()
			total= total + l.amount_total 
		obj_invoice_lines=self.env['account.invoice.line']
#		pdb.set_trace()
		invoice_line={
		('price_unit',total),
		('invoice_id',self.invoice_id.id),
		('name',self.product_id.name),
		('product_id',self.product_id.id),
		('uos_id',self.product_id.uom_id.id),
		('account_analytic_id',l.account_id.id),
		('account_id',self.product_id.property_account_income.id | self.product_id.categ_id.property_account_income_categ.id),
		#('invoice_line_tax_id',[(6, 0, self.product_id.taxes_id)]),
		}

		#pdb.set_trace()
		obj_invoice_lines=obj_invoice_lines.create(invoice_line)

		obj_invoice_lines.invoice_line_tax_id=self.env['account.fiscal.position'].browse(self.invoice_id.fiscal_position.id).map_tax(self.product_id.taxes_id)
		for l in self.hours_ids:
			l.write({'invoice_id': self.invoice_id.id})
#		self.write([l.id for l in self.hours_ids], {'invoice_id': self.invoice_id.id})
		self.env['account.invoice'].browse(self.invoice_id.id).button_reset_taxes()



class invoice(models.Model):
	_inherit="account.invoice"
	analytic_lines=fields.One2many( "account.analytic.line" ,"invoice_id" , domain=[('journal_id.type',"=",'general') ])
	has_discount=fields.Boolean(compute="_compute_has_discount", string="Discount?", help= "Contains line(s) with discount?")

	@api.one
	def _compute_has_discount(self):
		self.has_discount=False
		for line in self.invoice_line:
			if line.discount > 0:
				self.has_discount=True

	@api.one
	def remove_hours_from_invoice(self):
		#pdb.set_trace()
		for l in self.analytic_lines:
			l.write({'invoice_id': False})

    		#l.write({'invoice_id': False})

#	def launch_hours_wizard(self,cr, uid, ids, context=None):
	@api.multi
	def launch_hours_wizard(self):
		#pdb.set_trace()
		return {'name': _('Add Hours'),
	    	#'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'add_hours.wizard',
            'type': 'ir.actions.act_window',
            'default_invoice_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_product_id': self.company_id.default_hours_product.id,
            'target': 'new',
        }

class ResCompany(models.Model):
	_inherit = 'res.company'
	default_hours_product = fields.Many2one('product.product', string="Timesheet product",help="Product to be used when invoicing based upon timesheets")

 
class account_analytic_line(osv.osv):
    _inherit = 'account.analytic.line'
    def _check_inv(self, cr, uid, ids, vals):
        select = ids
        if isinstance(select, (int, long)):
            select = [ids]
        if ( not vals.has_key('invoice_id')) or vals['invoice_id' ] == False:
            for line in self.browse(cr, uid, select):
                if line.invoice_id:
                	if (line.invoice_id.state == 'draft'):
                		a=2 
                	else:
                		raise osv.except_osv(_('Error!'),
                			_('You cannot modify an invoiced analytic line! - lubon'))

        return True

# class account_invoice_cancel(models.TransientModel):
#     """
#     This wizard will cancel the all the selected invoices.
#     If in the journal, the option allow cancelling entry is not selected then it will give warning message.
#     """

#     _inherit = "account.invoice.cancel"
        
#     @api.one
#     def invoice_cancel(self):
#     	pdb.set_trace()
#     	return super(account_invoice_cancel, self.with_context(from_parent_object=True)).invoice_cancel()

class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"
    reduced_price=fields.Float(string="Eff. Price", compute="_compute_reduced_price", digits= dp.get_precision('Account'))

    @api.multi
    def _compute_reduced_price(self):
    	for line in self:
    		line.reduced_price=line.price_unit*(1-line.discount/100)