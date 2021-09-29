# -*- coding: utf-8 -*-
{
    'name': "lubon_qlan",

    'summary': """
        Implement specfic qlan requirements
        """,

    'description': """
        This module is custom made to manage the data center operations of qlan
    """,

    'author': "Lubon bv",
    'website': "http://www.lubon.be",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Lubon customer',
    'version': '8.0.0.45.0',

    # any module necessary for this one to work correctly
    'depends': ['base','pad', 'analytic','stock','hr_timesheet_invoice', 'lubon_base','lubon_credentials','lubon_partners', 'cmd_execute','aws'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'templates.xml',
        'views/lubon_qlan.xml',
        'views/lubon_invoicing.xml',
        'views/restorepoints.xml',
        'views/lubon_qlan_vm_backup_config.xml',
        'views/licenses.xml',
        'views/lubon_qlan_partner.xml',
        'views/lubon_qlan_account_sync.xml',
        'views/lubon_qlan_adstuff.xml',
        'views/lubon_qlan_product.xml',
        'views/qlan_aws_glacier.xml',
        'reports/lubon_qlan_invoice.xml',
        'reports/restore_points.xml',
        'data/lubon_qlan_data.xml',
        'data/lubon_qlan_cron.xml',
        'data/lubon_qlan_sessions.xml',
        'data/lubon_qlan_account_sync.xml',

#	    'lubon_qlan.py',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
