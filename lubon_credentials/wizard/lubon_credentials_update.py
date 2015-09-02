from openerp import models, fields, api


class lubon_credentials_update(models.TransientModel):
    _name = 'lubon_credentials.update'

    def _default_credentials(self):
        return self.env['lubon_credentials.credentials'].browse(self._context.get('active_id'))

    credentials_id = fields.Many2one('lubon_credentials.credentials', string="Credentials", default=_default_credentials)
    password = fields.Char(string="Password")

    @api.one
    def update_credentials(self):
        self.credentials_id.password = self.password
        return True
