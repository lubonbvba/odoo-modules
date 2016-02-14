# -*- coding: utf-8 -*-
{
    'name': "lubon_project",

    'summary': """
        Implement lubon project / tasks changes
        """,

    'description': """
        This module implements all qlan specific features.
    """,

    'author': "Lubon bvba",
    'website': "http://www.lubon.be",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Lubon',
    'version': '8.0.0.5.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'project','pad'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'views/lubon_project_tasks.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}