# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from collections import defaultdict
from openerp.osv import osv, fields
from openerp.report import report_sxw
import pdb
from openerp import models, fields, api

class report_rappel(report_sxw.rml_parse):
   
    _inherit = "account_followup.report.rappel"

    def _lines_get_with_partner(self, partner, company_id):
        pdb.set_trace()
        moveline_obj = self.pool['account.move.line']
        moveline_ids = moveline_obj.search(self.cr, self.uid, [
                            ('partner_id', '=', partner.id),
                            ('account_id.type', '=', 'receivable'),
                            ('reconcile_id', '=', False),
                            ('state', '!=', 'draft'),
                            ('company_id', '=', company_id),
                             '|', ('date_maturity', '=', False), ('date_maturity', '<=', fields.date.context_today(self, self.cr, self.uid)),
                        ])

        # lines_per_currency = {currency: [line data, ...], ...}
        lines_per_currency = defaultdict(list)
        for line in moveline_obj.browse(self.cr, self.uid, moveline_ids):
            currency = line.currency_id or line.company_id.currency_id
            line_data = {
                'name': line.move_id.name,
                'ref': line.ref,
                'date': line.date,
                'date_maturity': line.date_maturity,
                'balance': line.amount_currency if currency != line.company_id.currency_id else line.debit - line.credit,
                'blocked': line.blocked,
                'currency_id': currency,
            }
            lines_per_currency[currency].append(line_data)

        return [{'line': lines, 'currency': currency} for currency, lines in lines_per_currency.items()]        




class account_followup_print(models.TransientModel):
    _inherit = 'account_followup.print'
    
    #def do_process(self, cr, uid, ids, context=None):
    @api.multi
    def do_process(self):
    #, cr, uid, ids, context=None):
        pdb.set_trace()


