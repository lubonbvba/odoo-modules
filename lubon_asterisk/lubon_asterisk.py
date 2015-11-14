# -*- coding: utf-8 -*-
from openerp.osv import fields, orm
from openerp.tools.translate import _
import logging
#from openerp import models, fields, api, _
import pdb
import urllib2
from openerp import models, fields, api, _
# class lubon_asterisk(models.Model):
#     _name = 'lubon_asterisk.lubon_asterisk'

#     name = fields.Char()
logger = logging.getLogger(__name__)

class AsteriskServer(models.Model):
    _inherit = 'asterisk.server'
    server_starturl=fields.Char(string="URL", placeholder="https://mypbx.qlan.eu/pbx/proxyapi.php")
    server_key=fields.Char(string="Key")
    server_tenant=fields.Char(string="Tenant")
    server_timeout=fields.Char(string="Timeout")
    server_cid=fields.Char(string="CID", help="Default caller id to use")

class PhoneCommon(orm.AbstractModel):
    _inherit = 'phone.common'
    
    def click2dial(self, cr, uid, erp_number, context=None):
    	#res = super(PhoneCommon, self).click2dial(self, cr, uid, erp_number, context)
    	logger.info('Click2Dial:' + erp_number + " originator:")
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        logger.info('Click2Dial:' + erp_number + " originator:" + user.name)
    	ast_server=self.pool['asterisk.server']._get_asterisk_server_from_user(cr, uid, context=context)
    	#ast_server = self._get_asterisk_server_from_user(
        #    cr, uid, context=context)
    	ast_number = self.convert_to_dial_number(cr, uid, erp_number, context=context)
    	dial_string="https://" + ast_server.ip_address + "/pbx/webcall.php?source="+ user.internal_number
    	dial_string+="&dest="+ast_number
    	dial_string+="&" + ast_server.alert_info
   
        dial_string=ast_server.server_starturl + "?key=" + ast_server.server_key
        dial_string+="&tenant="+ast_server.server_tenant
        dial_string+="&reqtype=DIAL"
        dial_string+="&source="+user.internal_number
        dial_string+="&destclid="+ast_server.server_cid
        dial_string+="&sourceclid="+ast_number + "<Dial:>"
        dial_string+="&dest="+ast_number
        if ast_server.server_timeout:
            dial_string+="&timeout="+ast_server.server_timeout
        
          

    	response = urllib2.urlopen(dial_string)
        #pdb.set_trace()
        logger.info('Call result:' + response.read())
     


    	html = response.read()
#    	pdb.set_trace()
#        if not erp_number:
#            raise orm.except_orm(
#                _('Error:'),
#                _('Missing phone number'))