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
import openerp.http as http
from openerp.http import request, SUPERUSER_ID
import logging, pdb
from datetime import datetime
_logger = logging.getLogger(__name__)

class MyController(http.Controller):

    # @http.route('/sms/voxbone/receipt', type="http", auth="public")
    # def sms_voxbone_receipt(self, **kwargs):
    #     values = {}
    #     pdb.set_trace()
	# for field_name, field_value in kwargs.items():
    #         values[field_name] = field_value
        
    #     request.env['esms.voxbone'].sudo().delivery_receipt(values['AccountSid'], values['MessageSid'])
        
    #     return "<Response></Response>"
        
    @http.route('/qlan/disks/<asset>/', type="json", auth="public")
    def qlan_disk(self, asset):
        #pdb.set_trace()
        request.env['lubon_qlan.drives'].sudo().update_drives(asset,request.jsonrequest)
        _logger.info("End controller, returning 200")
        return 200
