# -*- coding: utf-8 -*-

from openerp import models, fields, api,_
import pdb
import datetime

class lubon_tasks(models.Model):
	_name="project.task"
	_inherit = ["pad.common","project.task" ]
#     _name = 'lubon_project.lubon_project'

#     name = fields.Char()
	contact_person_id=fields.Many2one('res.partner',help="Contact person for this ticket", string="Contact")
	contact_person_phone=fields.Char(string="Phone", help="User ddi or company phone")
	contact_person_mobile=fields.Char(string="Mobile", compute="set_phone_numbers")
	contact_person_phone_office=fields.Char(string="Office phone")
	description_edit=fields.Boolean(string="Edit")
	description_pad=fields.Char('Description PAD', pad_content_field='description')

	
	def _calculate_date_deadline(self):
		#pdb.set_trace()
		#self.date_deadline=fields.Date.context_today(self)
		#pdb.set_trace()
		return fields.Date.context_today(self) #+ datetime.timedelta(days=1)

	date_deadline=fields.Date(default=_calculate_date_deadline)

	@api.onchange('contact_person_id')
	@api.one
	def set_phone_numbers(self):
		if self.contact_person_id.phone:
			self.contact_person_phone=self.contact_person_id.phone
			self.contact_person_phone_office=self.contact_person_id.parent_id.phone
		else:
			self.contact_person_phone=self.contact_person_id.parent_id.phone
			self.contact_person_phone_office=""
		self.contact_person_mobile=self.contact_person_id.mobile
		if self.contact_person_id.parent_id:
			self.partner_id=self.contact_person_id.parent_id
		else:
			self.partner_id=self.contact_person_id

	
	@api.onchange('partner_id')
	@api.one
	def check_partner_id(self):
		if not(self.partner_id == self.project_id.partner_id):
			self.project_id=""

	@api.multi
	def write(self, vals):
		# set edit field to false
		vals.update({'description_edit':False})
		return super(lubon_tasks, self).write(vals)