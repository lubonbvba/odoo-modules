# -*- coding: utf-8 -*-
from openerp import http

# class LubonBase(http.Controller):
#     @http.route('/lubon_base/lubon_base/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lubon_base/lubon_base/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lubon_base.listing', {
#             'root': '/lubon_base/lubon_base',
#             'objects': http.request.env['lubon_base.lubon_base'].search([]),
#         })

#     @http.route('/lubon_base/lubon_base/objects/<model("lubon_base.lubon_base"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lubon_base.object', {
#             'object': obj
#         })