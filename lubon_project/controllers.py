# -*- coding: utf-8 -*-
from openerp import http

# class LubonProject(http.Controller):
#     @http.route('/lubon_project/lubon_project/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lubon_project/lubon_project/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lubon_project.listing', {
#             'root': '/lubon_project/lubon_project',
#             'objects': http.request.env['lubon_project.lubon_project'].search([]),
#         })

#     @http.route('/lubon_project/lubon_project/objects/<model("lubon_project.lubon_project"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lubon_project.object', {
#             'object': obj
#         })