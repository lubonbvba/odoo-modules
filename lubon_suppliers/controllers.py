# -*- coding: utf-8 -*-
from openerp import http

# class LubonSuppliers(http.Controller):
#     @http.route('/lubon_suppliers/lubon_suppliers/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lubon_suppliers/lubon_suppliers/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lubon_suppliers.listing', {
#             'root': '/lubon_suppliers/lubon_suppliers',
#             'objects': http.request.env['lubon_suppliers.lubon_suppliers'].search([]),
#         })

#     @http.route('/lubon_suppliers/lubon_suppliers/objects/<model("lubon_suppliers.lubon_suppliers"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lubon_suppliers.object', {
#             'object': obj
#         })