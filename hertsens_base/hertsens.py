# -*- coding: utf-8 -*-
#from openerp.osv import osv
from openerp import exceptions,models, fields, api, _
import csv,os,string,pdb
from path import path
from datetime import date
import time

# class account_analytic_line(models.Model):
# 	_inherit= "account.analytic.line"

# 	cmr=fields.Char(help="CMR Nummer")
# 	datum=fields.Date()
# 	wachttijd=fields.Float(help="Prijs wachttijd")
# 	ritprijs=fields.Float()
# 	vertrek=fields.Char(help="Vertrek plaats")
# 	bestemming=fields.Char(help="Bestemming plaats")
# 	refklant=fields.Char(help="Referentie opgegeven door klant")	


class hertsens_rit(models.Model):
	_name="hertsens.rit"
#	_inherits= {"account.analytic.line":"line_id"}
	_order = "datum desc"

#	line_id=fields.Many2one('account.analytic.line', required=True, ondelete="cascade")
	partner_id=fields.Many2one('res.partner', string="Company", required=True)
	company_id=	fields.Many2one( 'res.company', string="Customer", required=True)
	cmr=fields.Char(string="CMR", help="CMR Nummer")
	datum=fields.Date(required=True)
	wachttijd=fields.Float(help="Prijs wachttijd")
	ritprijs=fields.Float()
	vertrek=fields.Char(help="Vertrek plaats")
	bestemming=fields.Char(help="Bestemming plaats")
	refklant=fields.Char(string="Ref", help="Referentie opgegeven door klant")
	charges_vat=fields.Float(help="Reimbursements vat")
	charges_exvat=fields.Float(help="Reimbursements vat exempt")
	invoice_id=fields.Many2one('account.invoice')
	destination_ids=fields.One2many('hertsens.destination','rit_id')
	finished=fields.Boolean(help="Tick if ride is finished")
	state=fields.Selection([('quoted','Quote'),('planned','Planned'),('dispatched','Dispatched'),('cancelled', 'Cancelled'),('completed','Completed'),('waiting','Waiting for info'),('toinvoice','To be invoiced'),('invoiced','Invoiced')], required=True, default='planned')
	on=fields.Char(required=True,default="on")
	# @api.onchange('partner_id')
	# def _checkcompany(self):
	# 	self.company_id=self.partner_id.company_id
	# @api.multi
	# def unlink(self):
	# 	pdb.set_trace()
	# 	for ride in self:
	# 		if ride.state not in ('draft', 'cancel'):
	# 			raise Warning(_('You cannot delete an invoice which is not draft or cancelled. You should refund it instead.'))
	# 			return models.Model.unlink(self)


	@api.one
	@api.onchange('ritprijs','wachttijd')
	def _calculate_total(self):
		self.total_ride_price=self.ritprijs + self.wachttijd

	total_ride_price=fields.Float(string="Total price", compute=_calculate_total)

	@api.one
	@api.onchange('partner_id')
	def _set_company(self):
		self.company_id=self.partner_id.company_id
	


	@api.one
	@api.onchange('finished','refklant','ritprijs', 'datum','cmr')
	def _checkstate(self):
		flagvalid=True
		if self.ritprijs==0:
			flagvalid=False
		if not self.cmr:
			flagvalid=False
		if self.partner_id.ref_required and not self.refklant:
			flagvalid=False
		if self.finished:
			if flagvalid:
				self.state='toinvoice'
			else:
				self.state='waiting'
		else:
			if fields.Date.context_today(self)>self.datum:
				self.state='completed'
			else:
				self.state='planned'

	@api.multi
	def _prepare_cost_invoice(self, partner_id):
		invoice_name = self.partner_id.name
		return {
        'name': "%s - %s" % (time.strftime('%d/%m/%Y'), invoice_name),
        'partner_id': partner_id,
        'company_id': self.company_id,
        'payment_term': self.partner_id.property_payment_term.id or False,
        'account_id': self.partner_id.property_account_receivable.id,
		#            'currency_id': currency_id,
		#            'date_due': date_due,
		'fiscal_position': self.partner_id.property_account_position.id
		}


#        account_payment_term_obj = self.pool['account.payment.term']
#        invoice_name = self.partner_id.name
		
        # date_due = False
        # if partner.property_payment_term:
        #     pterm_list = account_payment_term_obj.compute(cr, uid,
        #             partner.property_payment_term.id, value=1,
        #             date_ref=time.strftime('%Y-%m-%d'))
        #     if pterm_list:
        #         pterm_list = [line[0] for line in pterm_list]
        #         pterm_list.sort()
        #         date_due = pterm_list[-1]


	@api.multi
	def invoice_cost_create(self, data):
		invoice_grouping = {}
		invoices = []

		for line in self:
		    key = (line.company_id.id,
		           line.partner_id.id)
		    invoice_grouping.setdefault(key, []).append(line)
		for (company_id, partner_id), rides in invoice_grouping.items():
		#	curr_invoice = self._prepare_cost_invoice(partner_id)
			#pdb.set_trace()
			ride=rides[0]
			curr_invoice = {
			'name': "%s - %s" % (time.strftime('%d/%m/%Y'), ride.partner_id.name),
        	'partner_id': ride.partner_id.id,
        	'company_id': ride.company_id.id,
        	'payment_term': ride.partner_id.property_payment_term.id or False,
        	'date': data['date'],
        	'account_id': ride.partner_id.property_account_receivable.id,
		#            'currency_id': currency_id,
		#            'date_due': date_due,
			'fiscal_position': ride.partner_id.property_account_position.id,
			'reference_type:': ride.partner_id.out_inv_comm_type
			}
			#pdb.set_trace()
			new_invoice=self.env['account.invoice'].create(curr_invoice)
			invoices.append(new_invoice.id)
			ntotal=0
			nchargesvat=0
			ncharges_exvat=0
			for ride in rides:
				ntotal=ntotal + ride.ritprijs + ride.wachttijd
				nchargesvat=nchargesvat+ride.charges_vat
				ncharges_exvat=ncharges_exvat+ride.charges_exvat
		 		ride.invoice_id=new_invoice
		 		ride.state='invoiced'
		 	if ntotal > 0:
		 		self._create_invoice_line(new_invoice, ntotal,ride.company_id.default_rides_product)
		 		if ride.partner_id.diesel > 0:
		 			self._create_invoice_line(new_invoice, ntotal * (ride.partner_id.diesel/100),ride.company_id.default_diesel_product)
		 	if nchargesvat > 0:
		 		self._create_invoice_line(new_invoice, nchargesvat,ride.company_id.default_charges_vat_product)

		 	if ncharges_exvat > 0:
		 		self._create_invoice_line(new_invoice, ncharges_exvat,ride.company_id.default_charges_exvat_product)
		 	new_invoice.button_reset_taxes()


		
		return invoices

	def _create_invoice_line(self,curr_invoice, nprice_unit,product):
		taxes = product.taxes_id or product.categ_id.property_account_income_categ.tax_ids
		tax = self.env['account.fiscal.position'].browse(curr_invoice.fiscal_position.id).map_tax(taxes)
		new_line={
		'invoice_id': curr_invoice.id,
		'price_unit': nprice_unit,
		'quantity': 1,
		'product_id': product.id,
		'uom_id': product.uom_id.id,
		'name': product.name,
		'account_id': product.property_account_income.id or product.categ_id.property_account_income_categ.id,
		'invoice_line_tax_id': tax
		}
		
		new_invoice_line=self.env['account.invoice.line'].create(new_line)
		

		new_invoice_line.invoice_line_tax_id=self.env['account.fiscal.position'].browse(curr_invoice.fiscal_position.id).map_tax(taxes)
		



class herstens_destination (models.Model):
	_name="hertsens.destination"
	_order="sequence"
	_rec_name = 'destination'

	
	destination=fields.Char()
	rit_id=fields.Many2one('hertsens.rit')
	sequence=fields.Integer()

class invoice(models.Model):
	_inherit="account.invoice"
	rides_ids=fields.One2many( "hertsens.rit" ,"invoice_id")
	on=fields.Char(required=True,default="on")
	@api.one
	def action_cancel(self,vals=None,context=None):
		#pdb.set_trace()	
		# code om te vermijden dat uitgaande facturen worden geannuleerd als er al ritten aanhangen.
		# voor inkomende facturen verandert er niets.
		if self.type == 'in_invoice':
			return super(invoice, self.with_context(from_parent_object=True)).action_cancel()
		if self.state == 'draft':
			for ride in self.rides_ids:
				#self.env['hertsens.rit']
				ride.sudo().state='toinvoice'
				ride.sudo().invoice_id=""
			return super(invoice, self.with_context(from_parent_object=True)).action_cancel()
		else:
			raise exceptions.Warning(_("Annuleren onmogelijk in deze factuurstatus."))

class invoice_line(models.Model):
	_inherit="account.invoice.line"
	on=fields.Char(required=True,default="on")

class account_move(models.Model):
	_inherit="account.move"
	on=fields.Char(required=True,default="on")

class bank_statement(models.Model):
	_inherit="account.bank.statement"
	on=fields.Char(required=True,default="on")






class res_company(models.Model):
	_inherit= "res.company"
	default_rides_product=fields.Many2one('product.product', string="Product rides", help="Product to use for rides")
	default_diesel_product=fields.Many2one('product.product', string="Product diesel surcharge",help="Product to use for diesel surcharge")
	default_charges_vat_product=fields.Many2one('product.product', string="Product charges vat",help="Product to use for charges including vat")
	default_charges_exvat_product=fields.Many2one('product.product', string="Product charges ex vat", help="Product to use for charges with vat exempt")

class res_partner(models.Model):
	_inherit= "res.partner"

	ref_required=fields.Boolean(string="Ref required",help="Customer reference mandatory?")
	diesel=fields.Float(help="Dieseltoeslag")
	ritten_count=fields.Float(compute="_ritten_count")
	partner_id=fields.Many2one('res.partner', required=True)
	ride_ids=fields.One2many('hertsens.rit','partner_id')
	@api.one
	def _ritten_count(self):
		self.ritten_count=0
		for f in self.ride_ids:
			self.ritten_count=self.ritten_count+1
		return 	

class hertsens_invoice_create(models.TransientModel):
	_name='hertsens.invoice.create'
	date=fields.Date(string="Invoice date",required=True, default=date.today())
	oneline=fields.Boolean(default=True,help="1 invoice line for all rides?")
	allrides_valid=fields.Boolean(default=False)
	def _default_rides(self):
		return self._context.get('active_ids')
	rides_ids=fields.Many2many('hertsens.rit', default=_default_rides)

	@api.onchange('rides_ids')
	def _check_validity(self):
		self.allrides_valid=True
		for ride in self.rides_ids:	
			if not ride.state == 'toinvoice':
				self.allrides_valid=False

	# @api.multi
	# def do_create(self):
	# 	invs = []
	# 	mod_obj = self.env['ir.model.data']
	# 	act_obj = self.env['ir.actions.act_window']
	# 	mod_ids = mod_obj.search([('name', '=', 'action_invoice_tree1')])
	# 	res_id = mod_obj.browse(mod_ids)
	# 	act_win = act_obj.browse(res_id)
	# 	pdb.set_trace()
	# 	act_win.domain = [('id','in',invs),('type','=','out_invoice')]
	# 	pdb.set_trace()
	# 	act_win['name'] = _('Invoices')
	# 	pdb.set_trace()
	# 	return act_win
	def do_create(self, cr, uid, ids, context=None):
		data = self.read(cr, uid, ids, context=context)[0]
		# Create an invoice based on selected timesheet lines
		invs = self.pool.get('hertsens.rit').invoice_cost_create(cr, uid, context['active_ids'], data, context=context)
		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')
		mod_ids = mod_obj.search(cr, uid, [('name', '=', 'action_invoice_tree1')], context=context)
		res_id = mod_obj.read(cr, uid, mod_ids, ['res_id'], context=context)[0]['res_id']
		act_win = act_obj.read(cr, uid, [res_id], context=context)[0]
		act_win['domain'] = [('id','in',invs),('type','=','out_invoice')]
#		act_win['domain'] = [('type','=','out_invoice')]
		act_win['name'] = _('Invoices')
		return act_win