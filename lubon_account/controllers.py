# -*- coding: utf-8 -*-
from openerp import http

# class LubonAccount(http.Controller):
#     @http.route('/lubon_account/lubon_account/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lubon_account/lubon_account/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lubon_account.listing', {
#             'root': '/lubon_account/lubon_account',
#             'objects': http.request.env['lubon_account.lubon_account'].search([]),
#         })

#     @http.route('/lubon_account/lubon_account/objects/<model("lubon_account.lubon_account"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lubon_account.object', {
#             'object': obj
#         })