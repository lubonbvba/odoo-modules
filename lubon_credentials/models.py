# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from openerp.http import request
from openerp.exceptions import ValidationError
from Crypto.PublicKey import RSA
import ast
import pdb

# class lubon_partners(models.Model):
#     _name = 'lubon_partners.lubon_partners'

#     name = fields.Char()
# -*- coding: utf-8 -*-
#from openerp import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'
    credential_ids = fields.One2many('lubon_credentials.credentials', 'partner_id', string='credentials')
    masterkey = fields.Char()

    @api.one
    def reveal_credentials(self, pin=None):

        require_pin = True

        def validate_retry():
            retry_count = request.session.get('lubon_pin_retry', 1)
            request.session['lubon_pin_retry'] = retry_count + 1
            if retry_count >= 3:
                request.session.logout()
                return False
            return True

        if require_pin and not pin:
            b=1
            raise ValidationError("PIN required!")

        if require_pin and pin != self.env.user.pin:
            if not validate_retry():
                return -1
            raise ValidationError("Incorrect PIN!")

        request.session['lubon_pin_retry'] = 1

        return [self.masterkey or '', self.env['ir.config_parameter'].get_param('lubon_credentials.reveal_credentials_timeout', '') or 15000]


class Users(models.Model):
    _inherit = 'res.users'
    pin = fields.Char()



class lubon_qlan_credentials(models.Model):
    _name = 'lubon_credentials.credentials'
    _rec_name = 'description'
    active=fields.Boolean()
    description = fields.Char(string="Description", required=True)
    user = fields.Char(string="User")
    password = fields.Char()
    hint = fields.Char()
    password01 = fields.Char(string="Pass")
    password02 = fields.Char(string="Conf")
    encrypted=fields.Char(string="Encrypted")
    is_saved=fields.Boolean(string="Saved")
    partner_id = fields.Many2one('res.partner',  ondelete='set null', string="Partner", index=True)
 #   credentials_type=fields.Selection([('tenant_admin','Tenant admin'),('wifi','Wifi'),('site_admin','Site admin'),('telephony','Telephony'),('general','General')], default='general')
    @api.one
    def show_password(self):
        raise exceptions.ValidationError(self.password)
        return True

    def _get_ipaddress(self, cr, uid, context=None):
        return request.httprequest.environ['REMOTE_ADDR']
    @api.one
    def reveal_credentials(self, pin=None):

        require_pin = True

        def validate_retry():
            retry_count = request.session.get('lubon_pin_retry', 1)
            request.session['lubon_pin_retry'] = retry_count + 1
            if retry_count >= 3:
                request.session.logout()
                return False
            return True

        if require_pin and not pin:
            raise ValidationError("PIN required!")

        if require_pin and pin != self.env.user.pin:
            if not validate_retry():
                return -1
            raise ValidationError("Incorrect PIN!")

        request.session['lubon_pin_retry'] = 1
        password=""
        if self.encrypted:
            f= open('/home/odoo/.odoo/private_key.pem','r')
            r = RSA.importKey(f.read())
            f.close()
            encrypted= ast.literal_eval(str(self.encrypted))
            password=r.decrypt(encrypted)
        return [password or '', self.env['ir.config_parameter'].get_param('lubon_credentials.reveal_credentials_timeout', '') or 15000]
    
    @api.one
    def encrypt(self):
        if not self.is_saved:
            self.password01=self.password
            self.password02=self.password
            self.encrypt_password(True)
            self.password=''
        return True


    
    @api.one
    @api.onchange('password01','password02')
    def encrypt_password(self, force=False):
        if (self.password01 and self.password02) or force:
            if self.password01 == self.password02:
                f= open('/home/odoo/.odoo/public_key.pem','r')
                r = RSA.importKey(f.read())
                f.close()
                #pdb.set_trace()
                encrypted=""
                if self.password01:
                    p=self.password01.encode('utf-8')
                    encrypted=r.encrypt(p,32)
                self.encrypted=encrypted
                self.password01=''
                self.password02=''
                self.is_saved=1
            else:
                raise ValidationError("Pls enter the same password twice")



class base_config_settings(models.TransientModel):
    _name = 'lubon_credentials.config.settings'
    _inherit = 'res.config.settings'

    def _get_default_reveal_credentials_timeout(self):
        return self.env['ir.config_parameter'].get_param('lubon_credentials.reveal_credentials_timeout', '') or 15000

    reveal_credentials_timeout = fields.Integer('Reveal Credentials Timeout (ms)', required=True, default=_get_default_reveal_credentials_timeout)

    @api.model
    def set_reveal_credentials_timeout(self, ids):
        config = self.browse(ids[0])
        icp = self.env['ir.config_parameter']
        icp.set_param('lubon_credentials.reveal_credentials_timeout', config.reveal_credentials_timeout)
