# -*- coding: utf-8 -*-
from openerp import http

# class LubonQlan(http.Controller):
#     @http.route('/lubon_qlan/lubon_qlan/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lubon_qlan/lubon_qlan/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lubon_qlan.listing', {
#             'root': '/lubon_qlan/lubon_qlan',
#             'objects': http.request.env['lubon_qlan.lubon_qlan'].search([]),
#         })

#     @http.route('/lubon_qlan/lubon_qlan/objects/<model("lubon_qlan.lubon_qlan"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lubon_qlan.object', {
#             'object': obj
#         })