# -*- coding: utf-8 -*-
from openerp.osv import fields, orm
from openerp.tools.translate import _
import logging
#from openerp import models, fields, api, _
import pdb
import urllib2

# class lubon_asterisk(models.Model):
#     _name = 'lubon_asterisk.lubon_asterisk'

#     name = fields.Char()
class PhoneCommon(orm.AbstractModel):
    _inherit = 'phone.common'
    
    def click2dial(self, cr, uid, erp_number, context=None):
    	#res = super(PhoneCommon, self).click2dial(self, cr, uid, erp_number, context)
    	user = self.pool['res.users'].browse(cr, uid, uid, context=context)
    	ast_server=self.pool['asterisk.server']._get_asterisk_server_from_user(cr, uid, context=context)
    	#ast_server = self._get_asterisk_server_from_user(
        #    cr, uid, context=context)
    	ast_number = self.convert_to_dial_number(cr, uid, erp_number, context=context)
    	dial_string="https://" + ast_server.ip_address + "/pbx/webcall.php?source="+ user.internal_number
    	dial_string+="&dest="+ast_number
    	dial_string+="&" + ast_server.alert_info
    	response = urllib2.urlopen(dial_string)
    	html = response.read()
#    	pdb.set_trace()
#        if not erp_number:
#            raise orm.except_orm(
#                _('Error:'),
#                _('Missing phone number'))