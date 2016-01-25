# -*- coding: utf-8 -*-

from openerp import models, fields, api
import pdb, logging


_logger = logging.getLogger(__name__)

class ir_cron_dependent(models.Model):
	_inherit = 'ir.cron'
	valid_dbname = fields.Char(string="Run only in db", help="Enter the only database name where this jobe can be executed")

	def _callback(self, cr, uid, model_name, method_name, args, job_id):
		#callback only runs when valid_dbname is blank or valid_dbname is current database name.
		#schedule times are updated.
		job=self.pool.get('ir.cron').browse(cr,uid,[job_id])
		if (not job.valid_dbname) or (job.valid_dbname and (job.valid_dbname == cr.dbname)):
			_logger.info("Normal callback, job: %s", job.name)
			super(ir_cron_dependent,self)._callback(cr, uid, model_name, method_name, args, job_id)
		else:
			_logger.warning("No callback, job %s runs only in database: %s", job.name,job.valid_dbname)


