# -*- coding: utf-8 -*-

from openerp import models, fields, api,_
from openerp import tools
import pdb
import datetime

class lubon_task_type(models.Model):
	_name="project.task.type"
	_inherit="project.task.type"
	days_to_add=fields.Integer(string="Days to add", help="Business days starting from today to add to the duedate")

class lubon_project_partner(models.Model):
	_name='res.partner'
	_inherit='res.partner'

	tasks_related_count=fields.Integer('Related tasks',compute="_calculate_tasks_related_count")

	@api.one
	def _calculate_tasks_related_count(self):
		tasks_related_count=self.env['project.task'].search_count([('partner_id',"=",self.parent_id.id or self.id)])
		#pdb.set_trace()


class lubon_tasks(models.Model):
	_name="project.task"
	_inherit = ["pad.common","project.task","mail.thread" ]
#     _name = 'lubon_project.lubon_project'

#     name = fields.Char()
	contact_person_id=fields.Many2one('res.partner',help="Contact person for this ticket", string="Contact")
	requester_partner_id=fields.Many2one('res.partner',help="Who sent the original e-mail", string="Contact")
	contact_person_phone=fields.Char(string="Phone", compute="set_contact_person_phone", help="User ddi or company phone")
	contact_person_mobile=fields.Char(string="Mobile", compute="set_contact_person_phone_mobile")
	contact_person_phone_office=fields.Char(string="Office phone" , compute = "set_contact_person_phone_office")
	description_edit=fields.Boolean(string="Edit")
	description_pad=fields.Char('Description PAD', pad_content_field='description')
	related_tasks_ids=fields.One2many('project.task.related','parent_task')

	tickets_related_count=fields.Integer(string="Open tasks", compute="_calculate_tickets_related_count")	

	def _calculate_date_deadline(self):
		#pdb.set_trace()
		#self.date_deadline=fields.Date.context_today(self)
		#pdb.set_trace()
		return fields.Date.context_today(self) #+ datetime.timedelta(days=1)

	date_deadline=fields.Date(default=_calculate_date_deadline)

	@api.one
	def _calculate_tickets_related_count(self):
		self.tickets_related_count=self.project_id.tasks.search_count([('stage_id.closed','=',False),('project_id','=',self.project_id.id)])


		#pdb.set_trace()

	
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


	

	@api.one
	def check_due_date(self,new_stage_id):
		new_stage=self.env['project.task.type'].browse(new_stage_id)
		days_to_add=new_stage.days_to_add
		if (self.stage_id != new_stage_id) and days_to_add>0:
			new_date=datetime.datetime.now()
			while days_to_add>0:
				new_date+=datetime.timedelta(days=1)
				if new_date.weekday() < 5:
					days_to_add-=1
			self.date_deadline=new_date
			#pdb.set_trace()

	
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
		#if 'contact_person_id' in vals.keys():
		#	self.message_subscribe([vals['contact_person_id']])
		if 'stage_id' in vals.keys():
			self.check_due_date(vals['stage_id'])
		return super(lubon_tasks, self).write(vals)

	#@api.one	
	def message_new(self,cr,uid, msg, custom_values=None, context=None):
		#self.message_new_v8(cr,uid,msg)
		
		if custom_values is None:
			custom_values = {}
		#partner = self.pool.get('res.partner').browse(msg.get('author_id'))	
		
		defaults = {
			'requester_partner_id': msg.get('author_id'),
			'contact_person_id': msg.get('author_id'),
			'partner_id': self.pool.get('res.partner').browse(cr,uid,msg.get('author_id')).parent_id.id,
			'date_start': msg.get('date'),
			}
		defaults.update(custom_values)
		#pdb.set_trace()
		return super(lubon_tasks, self).message_new(cr,uid, msg,custom_values=defaults, context=context)	
	

	@api.multi
	def message_get_email_values(self, id, notif_mail=None, context=None):
#		pdb.set_trace()
#		res = super(lubon_tasks, self).message_get_email_values(id, notif_mail=notif_mail, context=context)
		res = super(lubon_tasks, self).message_get_email_values(id)[0]
		project_info= "<hr></b>Details: </b><br>"
		if self.project_id.name:
			project_info+= "Project: " + self.project_id.name + "<br>"
		if self.partner_id.name:	
			project_info+= "Customer: " + self.partner_id.name + "<br>"
		if self.contact_person_id.name:
			project_info+= "Contact: " + self.contact_person_id.name + "<br>"
		if self.date_deadline:
			project_info+= "Due date: " + self.date_deadline + "<br>"
		project_info+= "<hr>"

		new_body=tools.append_content_to_html(id.body, project_info, plaintext=False, container_tag='div')
#		pdb.set_trace()
		res.update({'body_html': new_body})
		#pdb.set_trace()
		return res

	@api.multi
	def set_related_tasks(self):
		for task in self.related_tasks_ids:
			task.unlink()

		if self.project_id and (len(self.related_tasks_ids)==0):
			tasks=self.search([('project_id',"=", self.project_id.id),('stage_id.closed',"=", False)])
			self.env['project.task.related'].create_related_tasks(self,tasks)
		#self.env.invalidate_all()	
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
		for attachment in self.env['ir.attachment'].search([('res_model','like','project.task'),('res_id','=',self.parent_task.id)]):
			attachment.res_id=self.related_task_id.id		
		for message in self.parent_task.message_ids:
			message.res_id=self.related_task_id
 			
 		self.parent_task.message_post(body= '%s %d'%(_("Merged with:"),self.related_task_id.id))
 		self.related_task_id.message_post(body= '%s %d'%(_("Added info from:"),self.parent_task.id))







