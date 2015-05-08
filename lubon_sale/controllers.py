# -*- coding: utf-8 -*-
from openerp import http

# class LubonSale(http.Controller):
#     @http.route('/lubon_sale/lubon_sale/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lubon_sale/lubon_sale/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lubon_sale.listing', {
#             'root': '/lubon_sale/lubon_sale',
#             'objects': http.request.env['lubon_sale.lubon_sale'].search([]),
#         })

#     @http.route('/lubon_sale/lubon_sale/objects/<model("lubon_sale.lubon_sale"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lubon_sale.object', {
#             'object': obj
#         })