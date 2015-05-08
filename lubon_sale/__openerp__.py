# -*- coding: utf-8 -*-
{
    'name': "lubon_sale",

    'summary': """
        Implement lubon's modifications to sales and quotes 
	""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Lubon bvba",
    'website': "http://www.lubon.be",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','sale_margin'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
	'views/lubon_sale.xml',
	'reports/lubon_sale_reports.xml',
	'models.py',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
