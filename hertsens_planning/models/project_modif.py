from openerp import models, fields, api
import pdb


class project(models.Model):
	_inherit="project.project"
	
	vehicle_id=fields.Many2one('fleet.vehicle')
	vehicle_type_id=fields.Many2one('fleet.vehicle.type')
	driver_id=fields.Many2one('res.users')
	free_for_planning=fields.Boolean(help="Is vehicle free for planning")
	origin=fields.Char(help="Current origin")
	destination=fields.Char(help="Current destination")
	false=fields.Boolean(help="fake field for searching logic", default=False)

	kanban_state=fields.Selection([('normal', 'tbd'),('blocked', 'In Use'),('done', 'Available')], 'Kanban State',
                                         track_visibility='onchange',
                                         help="A task's kanban state indicates special situations affecting it:\n"
                                              " * Tbd/gray to define (Repair?)\n"
                                              " * In use/red, performing a ride\n"
                                              " * Available/green: Free for dispatch",
                                         required=False, copy=False, default='normal')
        
class task(models.Model):
	_inherit="project.task"
	ride_id=fields.Many2one('hertsens.rit')

	@api.one	
	def write(self, vals=None):
		# if 'stage_id' in vals:
		# 	new_stage=vals['stage_id']
		# 	if new_stage=self.env['ir.model.data'].xmlid_lookup('hertsens_planning.project_tt_exception')[3]:
		# 		#new state=exception
		# 	if new_stage=self.env['ir.model.data'].xmlid_lookup('hertsens_planning.project_tt_assigned')[3]:
		# 		#new state=assigned
		# 	if new_stage=self.env['ir.model.data'].xmlid_lookup('hertsens_planning.project_tt_accepted')[3]:
		# 		#new state=accepted

		super(task,self).write(vals)

