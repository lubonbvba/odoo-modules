# -*- coding: utf-8 -*-
from openerp import http

# class HertsensPlanning(http.Controller):
#     @http.route('/hertsens_planning/hertsens_planning/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hertsens_planning/hertsens_planning/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hertsens_planning.listing', {
#             'root': '/hertsens_planning/hertsens_planning',
#             'objects': http.request.env['hertsens_planning.hertsens_planning'].search([]),
#         })

#     @http.route('/hertsens_planning/hertsens_planning/objects/<model("hertsens_planning.hertsens_planning"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hertsens_planning.object', {
#             'object': obj
#         })