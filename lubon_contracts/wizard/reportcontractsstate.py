from openerp import models, fields, api, _
import pdb
import datetime

class ReportContractsState(models.TransientModel):
	_name = "lubon.contracts.state.wizard"
	date_end=fields.Date(default=datetime.date.today())
	date_printed=fields.Date(default=datetime.date.today())
	omit_invoiced=fields.Boolean(default=True, string="Omit invoiced lines")
	contract_lines=fields.One2many('lubon.contracts.state.lines.wizard','contract_id')
	contract_id=fields.Many2one("account.analytic.account")

	@api.multi
	def _get_start_date(self):
		#pdb.set_trace()
		return self.env['account.analytic.account'].browse(self.env.context['active_id']).date_cutoff
		#return datetime.date.today()

	date_start=fields.Date(default=_get_start_date)


	@api.multi
	def run_contracts_state(self):
		self.contract_id=self.env['account.analytic.account'].browse(self.env.context['active_id'])
		lines=self.env['account.analytic.line'].search([('account_id','=',self.env.context['active_id']),('invoice_id',"=",False),('date','>=',self.date_start),('date','<=',self.date_end) ])
		rsetlines=self.env['lubon.contracts.state.lines.wizard']
		for line in lines.sorted(key=lambda r: r.date):
			rsetlines.create({
				'contract_id':self.id,
				'date':line.date,
				'name':line.name,
				'user_id':line.user_id.id,
				'unit_amount': line.unit_amount,
				})

		datas = {'ids' : [self.id]}
		#pdb.set_trace()
		return {
            'type': 'ir.actions.report.xml',
            'report_name': 'lubon_contracts.report_contract_state',
            'datas': datas,
        }

class ReportContractsStateLines(models.TransientModel):
	_name = "lubon.contracts.state.lines.wizard"
	contract_id=fields.Many2one("lubon.contracts.state.wizard")
	date=fields.Date()
	user_id=fields.Many2one('res.users')
	unit_amount=fields.Float()
	name=fields.Char()
