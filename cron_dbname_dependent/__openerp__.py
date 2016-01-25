# -*- coding: utf-8 -*-
{
    'name': "Run cron job conditionally",

    'summary': """
        Makes the running of cron jobs dependent on the database name""",

    'description': """
        By installing this module an additional field is added to the definition of a cron job.
        If the database name is different from the value of the dbname parameter, the job will not run.
        If databases are duplicated, these cronjobs are disabled by default.
        This might be handy for jobs that check e-mail boxes, send mails to customers etc. 
    """,

    'author': "Lubon bvba",
    'website': "http://www.lubon.be",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '8.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'views/cron_dbname_dependent.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}