# -*- coding: utf-8 -*-
from openerp import http

# class LubonCredentials(http.Controller):
#     @http.route('/lubon_credentials/lubon_credentials/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lubon_credentials/lubon_credentials/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lubon_credentials.listing', {
#             'root': '/lubon_credentials/lubon_credentials',
#             'objects': http.request.env['lubon_credentials.lubon_credentials'].search([]),
#         })

#     @http.route('/lubon_credentials/lubon_credentials/objects/<model("lubon_credentials.lubon_credentials"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lubon_credentials.object', {
#             'object': obj
#         })