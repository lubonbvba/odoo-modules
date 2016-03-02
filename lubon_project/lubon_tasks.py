# -*- coding: utf-8 -*-

from openerp import models, fields, api,_
import pdb
import datetime

class lubon_tasks(models.Model):
	_name="project.task"
	_inherit = ["pad.common","project.task","mail.thread" ]
#     _name = 'lubon_project.lubon_project'

#     name = fields.Char()
	contact_person_id=fields.Many2one('res.partner',help="Contact person for this ticket", string="Contact")
	contact_person_phone=fields.Char(string="Phone", compute="set_contact_person_phone", help="User ddi or company phone")
	contact_person_mobile=fields.Char(string="Mobile", compute="set_contact_person_phone_mobile")
	contact_person_phone_office=fields.Char(string="Office phone" , compute = "set_contact_person_phone_office")
	description_edit=fields.Boolean(string="Edit")
	description_pad=fields.Char('Description PAD', pad_content_field='description')
	related_tasks_ids=fields.One2many('project.task.related','parent_task')
	
	def _calculate_date_deadline(self):
		#pdb.set_trace()
		#self.date_deadline=fields.Date.context_today(self)
		#pdb.set_trace()
		return fields.Date.context_today(self) #+ datetime.timedelta(days=1)

	date_deadline=fields.Date(default=_calculate_date_deadline)

	@api.depends('contact_person_id')
	@api.one
	def set_contact_person_phone(self):
		if self.contact_person_id.phone:
			self.contact_person_phone=self.contact_person_id.phone
		else:
			self.contact_person_phone=self.contact_person_id.parent_id.phone
	@api.depends('contact_person_id')
	@api.one
	def set_contact_person_phone_office(self):
		if self.contact_person_id.phone:
			self.contact_person_phone_office=self.contact_person_id.parent_id.phone
		else:
			self.contact_person_phone_office=""
	@api.depends('contact_person_id')
	@api.one
	def set_contact_person_phone_mobile(self):
		if self.contact_person_id.mobile:
			self.contact_person_mobile=self.contact_person_id.mobile
		else:
			self.contact_person_mobile=""



	@api.onchange('contact_person_id')
	@api.one
	def set_partner_id(self):
		if self.contact_person_id.parent_id:
			self.partner_id=self.contact_person_id.parent_id
		else:
			self.partner_id=self.contact_person_id
#		pdb.set_trace()	
#		self.env['project.task'].browse(self.env.context['params']['id']).message_subscribe([self.contact_person_id.id])

	
	@api.onchange('partner_id')
	@api.one
	def check_partner_id(self):
		if not(self.partner_id == self.project_id.partner_id):
			self.project_id=""

	@api.multi
	def write(self, vals):
		# set edit field to false
		vals.update({'description_edit':False})
		#pdb.set_trace()
		if 'contact_person_id' in vals.keys():
			self.message_subscribe([vals['contact_person_id']])
		return super(lubon_tasks, self).write(vals)

	# @api.multi
	# @api.onchange('partner_id')
	# def set_related_tasks(self):
	# 	#for task in self.related_tasks_ids:
	# 	#	task.unlink()
	# 	if self.partner_id and (len(self.related_tasks_ids)==0):
	# 		tasks=self.search([('partner_id',"=", self.partner_id.id),('stage_id.closed',"=", False)])
	# 		self.env['project.task.related'].create_related_tasks(self,tasks)
	# 	#self.env.invalidate_all()	
	# 	return "Ok"

	# tasks_related_dummy=fields.Char(compute=set_related_tasks,help="Dummy field to force calculation of related tasks")
	# def _message_get_auto_subscribe_fields(self, cr, uid, updated_fields, auto_follow_fields=None, context=None):
	# 	#pdb.set_trace()
	# 	if auto_follow_fields is None:
	# 		auto_follow_fields = ['user_id', 'reviewer_id']
	# 	return super(lubon_tasks, self)._message_get_auto_subscribe_fields(cr, uid, updated_fields, auto_follow_fields, context=context)







class project_tasks_related(models.TransientModel):
	_name="project.task.related"
	parent_task=fields.Many2one('project.task')
	name=fields.Char()
	related_task_id=fields.Many2one('project.task')
	@api.multi
	def create_related_tasks(self,task_id,tasks):
		for task in tasks:
			if task_id.id != task.id:
				self.create({'parent_task':task_id.id,
					'related_task_id':task.id,
					'name':task.name})
	@api.multi
	def merge_task(self):
		for message in self.related_task_id.message_ids:
 			pdb.set_trace()
