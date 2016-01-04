# -*- coding: utf-8 -*-
{
    'name': "lubon_contracts",

    'summary': """
        Modificatins of contract analytic accounts etc.""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Your Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account_analytic_analysis', 'lubon_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'views/lubon_contracts.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}