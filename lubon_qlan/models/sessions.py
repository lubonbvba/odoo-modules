from openerp import tools, models, fields, api, _
import csv,os,string,pdb
import openerp.addons.decimal_precision as dp
import openerp
from datetime import datetime,timedelta

class lubon_qlan_xasessions(models.Model):
	_name = 'lubon_qlan.xasessions'
	_description = 'Xenapp Sessions'
	
	date_start=fields.Char()
	session_active=fields.Boolean()
	adaccount_id= fields.Many2one('lubon_qlan.adaccounts')
	asset_id=fields.Many2one('lubon_qlan.assets')
	sessionid=fields.Integer()
	SessionName=fields.Char()
	logontime=fields.Datetime()





class lubon_qlan_xasessions_details(models.TransientModel):
	_name = 'lubon_qlan.xasessions_details'
	_description = 'Xenapp Session details'
	
	date_start=fields.Char()

	SessionId=fields.Integer()
	SessionName=fields.Char()
	ServerName=fields.Char()
	AccountName=fields.Char()
	LogOnTime=fields.Char()
	ClientIPV4=fields.Char()
	ConnectTime=fields.Datetime()
	DisconnectTime=fields.Datetime()
	LastInputTime=fields.Datetime()
	CurrentTime=fields.Datetime()
	ClientType=fields.Char()
	def cmd_execute_method(self,cmd_execute):
		result=cmd_execute.execute({})
		for session in result:
			record=self.create({
				'SessionId': session['SessionId'],
				'SessionName': session['SessionName'],
				'ServerName': session['ServerName'],
				'AccountName': session['AccountName'].replace('Q\\',''),
				'ClientType': session['ClientType'],
				'ClientIPV4': session['ClientIPV4'],
				})
			if session['CurrentTime']:
					record.CurrentTime= fields.Datetime.to_string(datetime.utcfromtimestamp(int(session['CurrentTime'][6:19])/1000))
			if session['ConnectTime']:
					record.ConnectTime= fields.Datetime.to_string(datetime.utcfromtimestamp(int(session['ConnectTime'][6:19])/1000))
			if session['DisconnectTime']:
					record.DisconnectTime= fields.Datetime.to_string(datetime.utcfromtimestamp(int(session['DisconnectTime'][6:19])/1000))
			if session['LastInputTime']:
					record.LastInputTime=fields.Datetime.to_string(datetime.utcfromtimestamp(int(session['LastInputTime'][6:19])/1000))
			if session['LogOnTime']:
					record.LastInputTime=fields.Datetime.to_string(datetime.utcfromtimestamp(int(session['LogOnTime'][6:19])/1000))
			adaccount_id=self.env['lubon_qlan.adaccounts'].search([('samaccountname','=',record.AccountName)])
			asset_id=self.env['lubon_qlan.assets'].search([('asset_name','=',record.ServerName)])
			try:
				xasession=self.env['lubon_qlan.xasessions'].search([
													('session_active','=',True),
													('sessionid','=',record.SessionId),
													('adaccount_id','=',adaccount_id.id),
													('asset_id','=',asset_id.id)
													])
				if not xasession:
					xasession=self.env['lubon_qlan.xasessions'].create({
													'session_active': True,
													'sessionid':record.SessionId,
													'adaccount_id':adaccount_id.id,
													'asset_id':asset_id.id,
													'logontime': record.LogOnTime,
													'SessionName': record.SessionName
													})

			except:
				pdb.set_trace()
				pass
