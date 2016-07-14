# -*- coding: utf-8 -*-

from openerp import models, fields, api
import pdb


class hertsens_rit(models.Model):
	_inherit="hertsens.rit"

	vehicle_type_id=fields.Many2one('fleet.vehicle.type')
	task_ids=fields.One2many('project.task','ride_id')
	
	@api.one
	def name_get(self):
		name=(self.vertrek or "") + " - " + (self.bestemming or "")
#		pdb.set_trace()
		if 'detailed' in self.env.context.keys():
			pdb.set_trace()

		return self.id, name		
	
	@api.multi	
	def dispatch_wizard(self):
		#pdb.set_trace()
		wiz=self.env['vehicle.planning.wizard'].create({
			'ride_id':self.id,
#			'name': self.name_get(),
			'vehicle_type_id': self.vehicle_type_id.id,
			})

		return {
                'name': 'Dispatch Wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'vehicle.planning.wizard',
                'domain': [],
                'context': self.env.context,
                'res_id': wiz.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
#                'nodestroy': True,
            }
