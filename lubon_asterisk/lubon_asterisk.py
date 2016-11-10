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
        dial_string+="&account="+user.internal_number+"-"+ast_server.server_tenant
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

    def _get_calling_number(self, cr, uid, context=None):

        user, ast_server, ast_manager = self._connect_to_asterisk(
            cr, uid, context=context)
        calling_party_number = False
        try:
            list_chan = ast_manager.Status()
            from pprint import pprint
            pprint(list_chan)
            _logger.debug("Result of Status AMI request: %s", list_chan)
            for chan in list_chan.values():
                sip_account = user.asterisk_chan_type + '/' + user.resource
                # 4 = Ring
                if (
                        chan.get('ChannelState') == '4' and
                        chan.get('ConnectedLineNum') == user.internal_number):
                    _logger.debug("Found a matching Event in 'Ring' state")
                    calling_party_number = chan.get('CallerIDNum')
                    break
                # 6 = Up
                if (
                        chan.get('ChannelState') == '6'
                        and sip_account in chan.get('BridgedChannel', '')):
                    _logger.debug("Found a matching Event in 'Up' state")
                    calling_party_number = chan.get('CallerIDNum')
                    break
                if (
                        chan.get('ChannelState') == '6' and
                        chan.get('ConnectedLineNum') == user.internal_number):
                    _logger.debug("Found a matching Event in 'Ring' state")
                    calling_party_number = chan.get('CallerIDNum')
                    break
                # Compatibility with Asterisk 1.4
                if (
                        chan.get('State') == 'Up'
                        and sip_account in chan.get('Link', '')):
                    _logger.debug("Found a matching Event in 'Up' state")
                    calling_party_number = chan.get('CallerIDNum')
                    break
        except Exception, e:
            _logger.error(
                "Error in the Status request to Asterisk server %s"
                % ast_server.ip_address)
            _logger.error(
                "Here are the details of the error: '%s'" % unicode(e))
            raise orm.except_orm(
                _('Error:'),
                _("Can't get calling number from  Asterisk.\nHere is the "
                    "error: '%s'" % unicode(e)))

        finally:
            ast_manager.Logoff()

        _logger.debug("Calling party number: '%s'" % calling_party_number)
        return calling_party_number