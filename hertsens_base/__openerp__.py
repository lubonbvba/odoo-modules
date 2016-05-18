# -*- coding: utf-8 -*-
{
    'name': "hertsens_base",

    'summary': """
        Base modifications for Hertsens
        """,

    'description': """
        Modules will change stylesheets and change the invoice layout
    """,

    'author': "Lubon bvba",
    'website': "http://www.lubon",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.4',

    # any module necessary for this one to work correctly
    'depends': ['base','account', ],

    # always loaded
    'data': [
    'security/security.xml',
    'security/hertsens_account_security.xml',
    'security/ir.model.access.csv',
#	'static/src/js/lubon_base.js',
#	'static/src/css/lubon_base.css',
    'templates.xml',
	'views/hertsens_base.xml',
	'views/hertsens_partners.xml',
    'views/hertsens_menu.xml',
    'views/hertsens_users.xml',
    'views/hertsens_account.xml',
    'reports/hertsens_base_invoice.xml',
    'reports/hertsens_base_header.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
