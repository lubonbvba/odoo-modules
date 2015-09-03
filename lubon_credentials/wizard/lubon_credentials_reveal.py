from openerp import models, fields, api


class lubon_credentials_reveal(models.TransientModel):
    _name = 'lubon_credentials.reveal'

    def _default_credentials(self):
        return self.env['lubon_credentials.credentials'].browse(self._context.get('active_id'))

    credentials_id = fields.Many2one('lubon_credentials.credentials', string="Credentials", required=True, default=_default_credentials)
    description = fields.Char(string="Description", related="credentials_id.description", readonly=True)
    user = fields.Char(string="User", related="credentials_id.user", readonly=True)
