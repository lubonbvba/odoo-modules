# -*- coding: utf-8 -*-
{
    'name': "lubon_odoo",

    'summary': """
        Lubon's generic modifications""",

    'description': """
        This module changes generic odoo (mis)behaviour.
    """,

    'author': "Lubon bvba",
    'website': "http://www.lubon.be",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'views/lubon_odoo_partners.xml',
        'views/lubon_odoo_odoo.xml',
#        'views/lubon_odoo_sale.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}