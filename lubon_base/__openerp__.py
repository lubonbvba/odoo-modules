# -*- coding: utf-8 -*-
{
    'name': "lubon_base",

    'summary': """
        Trigger for lubon updates""",

    'description': """
        By making other modules dependent on this on -u lubon_base makes sure that all
        relevant modules are updated.
    """,

    'author': "Lubon bvba",
    'website': "http://www.lubon.be",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Lubon bvba',
    'version': '8.0.0.4.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
#	'static/src/js/lubon_base.js',
	   'static/src/css/lubon_base.css',
        'templates.xml',
    	'views/lubon_base.xml',
        'reports/lubon_base_invoice.xml',
        'reports/lubon_base_header.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
