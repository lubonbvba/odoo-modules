# -*- coding: utf-8 -*-
{
    'name': "lubon_asterisk",

    'summary': """
        Module to enable web dialer""",

    'description': """
        This module builds upon the asterisk asterisk_click2dial, it enables the webdialer of our private pbx.
    """,

    'author': "Lubon bvba",
    'website': "http://www.lubon.be",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','asterisk_click2dial'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'views/lubon_asterisk.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}