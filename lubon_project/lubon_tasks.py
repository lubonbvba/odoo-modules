# -*- coding: utf-8 -*-

from openerp import models, fields, api,_

class lubon_tasks(models.Model):
	_inherit="project.task"
#     _name = 'lubon_project.lubon_project'

#     name = fields.Char()
	contact_person_id=fields.Many2one('res.partner',help="Contact person for this ticket", string="Contact")
	contact_person_phone=fields.Char(string="Phone", help="User ddi or company phone")
	contact_person_mobile=fields.Char(string="Mobile")

	@api.onchange('contact_person_id')
	@api.one
	def set_phone_numbers(self):
		if self.contact_person_id.phone:
			self.contact_person_phone=self.contact_person_id.phone
		else:
			self.contact_person_phone=self.contact_person_id.parent_id.phone
		self.contact_person_mobile=self.contact_person_id.mobile
