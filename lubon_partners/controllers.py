# -*- coding: utf-8 -*-
from openerp import http

# class LubonPartners(http.Controller):
#     @http.route('/lubon_partners/lubon_partners/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lubon_partners/lubon_partners/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lubon_partners.listing', {
#             'root': '/lubon_partners/lubon_partners',
#             'objects': http.request.env['lubon_partners.lubon_partners'].search([]),
#         })

#     @http.route('/lubon_partners/lubon_partners/objects/<model("lubon_partners.lubon_partners"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lubon_partners.object', {
#             'object': obj
#         })