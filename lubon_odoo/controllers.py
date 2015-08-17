# -*- coding: utf-8 -*-
from openerp import http

# class LubonOdoo(http.Controller):
#     @http.route('/lubon_odoo/lubon_odoo/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lubon_odoo/lubon_odoo/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lubon_odoo.listing', {
#             'root': '/lubon_odoo/lubon_odoo',
#             'objects': http.request.env['lubon_odoo.lubon_odoo'].search([]),
#         })

#     @http.route('/lubon_odoo/lubon_odoo/objects/<model("lubon_odoo.lubon_odoo"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lubon_odoo.object', {
#             'object': obj
#         })