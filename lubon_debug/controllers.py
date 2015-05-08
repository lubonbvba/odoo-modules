# -*- coding: utf-8 -*-
from openerp import http

# class LubonDebug(http.Controller):
#     @http.route('/lubon_debug/lubon_debug/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lubon_debug/lubon_debug/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lubon_debug.listing', {
#             'root': '/lubon_debug/lubon_debug',
#             'objects': http.request.env['lubon_debug.lubon_debug'].search([]),
#         })

#     @http.route('/lubon_debug/lubon_debug/objects/<model("lubon_debug.lubon_debug"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lubon_debug.object', {
#             'object': obj
#         })