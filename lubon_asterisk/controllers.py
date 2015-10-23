# -*- coding: utf-8 -*-
from openerp import http

# class LubonAsterisk(http.Controller):
#     @http.route('/lubon_asterisk/lubon_asterisk/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lubon_asterisk/lubon_asterisk/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lubon_asterisk.listing', {
#             'root': '/lubon_asterisk/lubon_asterisk',
#             'objects': http.request.env['lubon_asterisk.lubon_asterisk'].search([]),
#         })

#     @http.route('/lubon_asterisk/lubon_asterisk/objects/<model("lubon_asterisk.lubon_asterisk"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lubon_asterisk.object', {
#             'object': obj
#         })