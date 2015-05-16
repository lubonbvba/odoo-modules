# -*- coding: utf-8 -*-
{
    'name': "lubon_qlan",

    'summary': """
        Implement specfic qlan requirements
        """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Lubon bvba",
    'website': "http://www.lubon.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Lubon customer',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','analytic'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'templates.xml',
        'views/lubon_qlan.xml',
	'models.py'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
