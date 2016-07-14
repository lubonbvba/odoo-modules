# -*- coding: utf-8 -*-

from openerp import models, fields, api
import pdb


class vehicle_planning_wizard(models.TransientModel):
	_name="vehicle.planning.wizard"
	ride_id=fields.Many2one('hertsens.rit')
	project_id=fields.Many2one('project.project')
	task_id=fields.Many2many('project.task')
	driver_id=fields.Many2one('res.users')
	name=fields.Char()
	dispatch_message=fields.Char()
	vehicle_type_id=fields.Many2one('fleet.vehicle.type')
	show_type_only=fields.Boolean(help="Show only vehicles of this type", default=True)
	show_free_only=fields.Boolean(help="Show only free vehicles", default=True)
	planning_vehicles_ids=fields.One2many('planning.vehicles','vehicle_planning_wizard_id')

	@api.model
	def create(self, vals=None):
		wiz=super(vehicle_planning_wizard,self).create(vals)
		wiz.set_candidates()
		return wiz




	@api.multi
#	@api.onchange('show_type_only')
	def set_candidates(self):
		for candidate in self.planning_vehicles_ids:
			candidate.unlink()
		candidates=self.env['project.project'].search(['|',('vehicle_type_id','=',self.vehicle_type_id.id),('false',"=",self.show_type_only)])	
		self.env['planning.vehicles'].new_candidates(self,candidates)	
		return {
                'name': 'Dispatch Wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'vehicle.planning.wizard',
                'domain': [],
                'context': self.env.context,
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
#                'nodestroy': True,
            }


  
class planning_vehicles(models.TransientModel):
	_name="planning.vehicles"
	_description="Available vehicles"

	vehicle_planning_wizard_id=fields.Many2one("vehicle.planning.wizard")
	name=fields.Char()
	vehicle_type_id=fields.Many2one('fleet.vehicle.type')
	project_id=fields.Many2one('project.project')	
	kanban_state=fields.Selection([('normal', 'tbd'),('blocked', 'In Use'),('done', 'Available')], 'Kanban State',
                                         track_visibility='onchange',
                                         help="A task's kanban state indicates special situations affecting it:\n"
                                              " * Tbd/gray to define (Repair?)\n"
                                              " * In use/red, performing a ride\n"
                                              " * Available/green: Free for dispatch",
                                         required=False, copy=False, default='normal')

	@api.multi
	def new_candidates(self,wizard,candidates):
#		pdb.set_trace()
		for candidate in candidates:
			self.create({
				'name':candidate.name,
				'kanban_state': candidate.kanban_state,
				'vehicle_type_id': candidate.vehicle_type_id.id,
				'vehicle_planning_wizard_id':wizard.id,
				'project_id':candidate.id,
			})

	@api.multi
	def select_candidate(self):
		#pdb.set_trace()
		dispatch_wizard=self.env['vehicle.dispatch.wizard'].create({
			'ride_id': self.vehicle_planning_wizard_id.ride_id.id,
			'project_id': self.project_id.id,
			'driver_id': self.project_id.driver_id.id
			})
		return {
               'name': 'Dispatch Wizard',
               'view_type': 'form',
               'view_mode': 'form',
               'res_model': 'vehicle.dispatch.wizard',
               'domain': [],
               'context': self.env.context,
               'res_id': dispatch_wizard.id,
               'type': 'ir.actions.act_window',
               'target': 'new',
#               'nodestroy': True,
            }



class vehicle_dispatch_wizard(models.TransientModel):
	_name='vehicle.dispatch.wizard'
	ride_id=fields.Many2one('hertsens.rit',required=True)
	project_id=fields.Many2one('project.project', required=True)
	driver_id=fields.Many2one('res.users')
	dispatch_message=fields.Char(size=160)

	@api.multi
	def confirm_dispatch(self):
		#pdb.set_trace()
		self.project_id.write({
			'driver_id':self.driver_id.id,
			'origin': self.ride_id.vertrek,
			'destination':self.ride_id.bestemming,
			'kanban_state':'blocked',
			})
		self.ride_id.write({
			'state':'dispatched',
			})
		self.env['project.task'].create({
			'name': self.ride_id.name_get(),
			'project_id': self.project_id.id,
			'user_id': self.driver_id.id,
			'ride_id':self.ride_id.id,		
			})

