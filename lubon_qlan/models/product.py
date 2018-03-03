# -*- coding: utf-8 -*-

from openerp import models, fields, api
import pdb

class product(models.Model):
	_inherit = 'product.template'

	type=fields.Selection(selection_add=[('qsubscription','Subscription')])
	reference_model=fields.Many2one("ir.model", help="Model that van be used to refer to this product, eg asset, ad user, license, domain, phone number")
	valid_options=fields.Many2many('product.template', relation="lubon_qlan_product_valid_options",column1="product",column2="option")
	option_in=fields.Many2many('product.template', relation="lubon_qlan_product_valid_options",column2="product",column1="option")
	is_option=fields.Boolean(help="Tick if this product can be used as an option to another product")
	quantity_type=fields.Selection([('fixed','Fixed number'),('usage','Based on usage')], default='fixed', help="How is the quantitiy calculated? Fixed, or based on consumption, eg VRam, KWH ...")
	quantity_method=fields.Selection([('manual','Manual')] , help='How is the usage calculated', default='manual')
	cmd_create=fields.Many2one('cmd_execute.command', string="Create / enable command")
	cmd_delete=fields.Many2one('cmd_execute.command', string="Delete / disable command")
	cmd_modify=fields.Many2one('cmd_execute.command', string="Modify command")
