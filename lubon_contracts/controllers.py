# -*- coding: utf-8 -*-
from openerp import http

# class LubonContracts(http.Controller):
#     @http.route('/lubon_contracts/lubon_contracts/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lubon_contracts/lubon_contracts/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lubon_contracts.listing', {
#             'root': '/lubon_contracts/lubon_contracts',
#             'objects': http.request.env['lubon_contracts.lubon_contracts'].search([]),
#         })

#     @http.route('/lubon_contracts/lubon_contracts/objects/<model("lubon_contracts.lubon_contracts"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lubon_contracts.object', {
#             'object': obj
#         })