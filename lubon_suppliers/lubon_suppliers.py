# -*- coding: utf-8 -*-

from openerp import models, fields, api, registry, _
from os.path import expanduser
from datetime import datetime,date,timedelta
import ftplib, zipfile, logging,csv,tempfile,shutil, barcodenumber
import pdb

logger = logging.getLogger(__name__)

class res_partner(models.Model):
	_inherit = 'res.partner'

	supplier_cron_job= fields.Many2one('ir.cron',string="Schedule")
	supplier_fileimport = fields.Boolean(string="File Import", help="Supplier has pricelists",default=False)
	supplier_transfermethod = fields.Selection([('ftp', 'FTP'),('none','None')], default='none')
	supplier_transferserver=fields.Char(help='Server')
	supplier_transferlogin=fields.Char(help='Login name for server')
	supplier_transferpassword=fields.Char()
	supplier_file_source=fields.Char(string='Get file',help='File name to get from server')
	supplier_file_resulting=fields.Char(string='Prices file',help='File name to use in operation')
	supplier_file_zipped=fields.Boolean(string="Zipped", default=False, help='File to be unzipped?')
	supplier_file=fields.Char(string="File name",help="Name of the file that has to be imported, also the filename that is created by the previous step")
	supplier_prefix=fields.Char(string="Prefix")
	supplier_product_category_id=fields.Many2one('product.category', string="Default category", help="What product category will be used for products of this supplier")
	manufacturer=fields.Boolean(string="Manufacturer", help="Tick if manufacturer/brand", default=False)
	route_ids=fields.Many2many('stock.location.route', domain="[('product_selectable', '=', True)]")
	supplier_product_type=fields.Selection([('product', 'Stockable Product'), ('consu', 'Consumable'), ('service','Service')])
	supplier_product_cost_method=fields.Selection([('standard', 'Standard Price'), ('average', 'Average Price'), ('real','Real Price')])
	supplier_product_valuation_method=fields.Selection([('manual_periodic', 'Periodic (manual)'), ('real_time', 'Real Time (automated)')])
	stats_ids=fields.One2many('lubon_suppliers.import_stats', 'supplier_id')
	supplier_num=fields.Integer(string="Max records to process", help="0=Unlimited", default=0)
	supplier_delete_details=fields.Boolean(string="Delete import detail", default=False)
	brand_ids=fields.Many2many('res.partner',domain="[('manufacturer','=',True)]",relation="supplierbrands", column1="suppliers", column2="brands")
	supplier_header_line=fields.Integer(string="Header line", default=1, help="Line number to retrieve field names")
	supplier_delimiter=fields.Char(string="Delimiter",default=";",size=1)

	supplier_default_manufacturer=fields.Many2one('res.partner', domain="[('manufacturer','=',True)]")

	supplier_field_description=fields.Many2one('lubon_suppliers.fieldnames', domain="[('supplier_id','=',active_id)]")
	supplier_field_part_supplier=fields.Many2one('lubon_suppliers.fieldnames', domain="[('supplier_id','=',active_id)]")
	supplier_field_part_manufacturer=fields.Many2one('lubon_suppliers.fieldnames', domain="[('supplier_id','=',active_id)]")
	supplier_field_ean=fields.Many2one('lubon_suppliers.fieldnames', domain="[('supplier_id','=',active_id)]")
	supplier_field_price_purchase=fields.Many2one('lubon_suppliers.fieldnames', domain="[('supplier_id','=',active_id)]")
	supplier_field_price_list=fields.Many2one('lubon_suppliers.fieldnames', domain="[('supplier_id','=',active_id)]")
	supplier_field_manufacturer=fields.Many2one('lubon_suppliers.fieldnames', domain="[('supplier_id','=',active_id)]")
	supplier_field_categ01=fields.Many2one('lubon_suppliers.fieldnames', domain="[('supplier_id','=',active_id)]")
	supplier_field_categ02=fields.Many2one('lubon_suppliers.fieldnames', domain="[('supplier_id','=',active_id)]")
	supplier_field_categ03=fields.Many2one('lubon_suppliers.fieldnames', domain="[('supplier_id','=',active_id)]")

	issue_ids=fields.One2many('lubon_suppliers.info_import','issue_id')

	supplier_field_names=fields.One2many('lubon_suppliers.fieldnames','supplier_id')
	supplier_debug=fields.Boolean(string="Full debug", default=False)
	supplier_reinit=fields.Boolean(string="Reinit", default=False, help="Delete all non used products")
	@api.one
	def process_schedule(self):
		logger.info("Executing Schedule for:" + str(self.id))

		self.retrieve_prices()




	@api.multi
	def retrieve_prices(self):
		#test transfertype
		#self.env['product.template'].search([('active','=',False)]).activate_all()
		logger.info("Start retrieve_prices")
		starttime=datetime.now()
		if self.supplier_reinit:
			self.initsupplier()
			self.supplier_reinit=False
		table_stats=self.env['lubon_suppliers.import_stats']
		stats=table_stats.create({'supplier_id': self.id,
								'start': datetime.now(),
								'startfunc':'retrieve_prices',
								'name': self.supplier_prefix + "-" +datetime.now().strftime("%A, %d. %B %Y %I:%M%p") })
		self.getfile(stats)
		self.readfile(1,stats)
		stats.processbrands()
		stats.processproducts()
		stats.elap_total=(datetime.now()-starttime).seconds
		logger.info("End retrieve_prices")
	@api.multi	
	def readfile(self, x, supplier_stats=False):
		#This function imports the csv file in the database
		logger.info("Start readfile")
		starttime=datetime.now()
		table_stats=self.env['lubon_suppliers.import_stats']
		if not supplier_stats:
			supplier_stats=table_stats.create({'supplier_id': self.id,
									'startfunc':"readfile",
									'start': datetime.now(),
									'name': self.supplier_prefix + "-" +datetime.now().strftime("%A, %d. %B %Y %I:%M%p") })
		table_import=self.env['lubon_suppliers.info_import']
		table_import.processfile(supplier_stats)
		supplier_stats.stop_csv= datetime.now()
		supplier_stats.elap_csv=(datetime.now()-starttime).seconds
		logger.info("End readfile")
	@api.multi
	def getfile(self, stats=None):
		logger.info("Start getfile")
		if not stats:
			stats=table_stats.create({'supplier_id': self.id,
									'startfunc':"getfile",
									'start': datetime.now(),
									'name': self.supplier_prefix + "-" +datetime.now().strftime("%A, %d. %B %Y %I:%M%p") })
		if self.supplier_transfermethod == 'ftp':
			self.getfile_ftp(stats)
		logger.info("End getfile")
	def getfile_ftp(self,stats):
		#this function retrieves the file from the supplier, and extracts if necessery
		#the resulting file is put in 
		logger.info("Start getfile ftp")
		tempdir=tempfile.mkdtemp()+'/'
		try:
			ftp = ftplib.FTP(self.supplier_transferserver)
			result=ftp.login(self.supplier_transferlogin, self.supplier_transferpassword)
			logger.info('Logging in result: ' + result)
			basepath=tempdir+self.supplier_file_source

			result=download=open(basepath, 'wb')
			result=ftp.retrbinary("RETR " + self.supplier_file_source ,download.write)
			download.close()
			if self.supplier_file_zipped:
				zip=zipfile.ZipFile(basepath, "r")
				zip.extract(self.supplier_file_resulting, tempdir)
			shutil.copyfile(tempdir + self.supplier_file_resulting,self.supplier_file)
		except:
			logger.error("Error in ftp operation: " + result)
		#print "Error"
		#shutil.rmtree(tempdir)
		stats.update({'stop_transfer': datetime.now()})
		logger.info("End getfile ftp")
	@api.multi	
	def readfields(self):
		for field in self.supplier_field_names:
			field.unlink()
		with open (self.supplier_file, 'rb') as cleanfile:
			n=0
			reader = csv.reader(cleanfile, delimiter=str(self.supplier_delimiter))
			for row in reader:
				n+=1;
				if n>=self.supplier_header_line:
					for field in row:
						self.env['lubon_suppliers.fieldnames'].create({
								'supplier_id':self.id,
								'name':str(field),
								})
					break
		cleanfile.close()
	@api.one
	def initsupplier(self):
		logger.info("Start reinit")
		self.env['product.product'].search([('seller_id','=',self.id)]).delete_products(self.supplier_debug)
		logger.info("End reinit")



class lubon_suppliers_fieldnames(models.Model):
	_name='lubon_suppliers.fieldnames'
	name=fields.Char()
	supplier_id=fields.Many2one('res.partner')




class lubon_suppliers_info_import(models.Model):
	_name='lubon_suppliers.info_import'
	stats_id=fields.Many2one('lubon_suppliers.import_stats',ondelete='cascade')
#	supplier_info_id=fields.Many2one('product.supplierinfo')
	description=fields.Char()
	issue_id=fields.Many2one('res.partner')
	supplier_part=fields.Char(index=True)
	manuf_part=fields.Char()
	Class1=fields.Char()
	Class2=fields.Char()
	Class3=fields.Char()
	manufacturer=fields.Char(index=True)
	Version=fields.Char()
	Language=fields.Char()
	Media=fields.Char()
	Trend=fields.Char()
	PriceGroup=fields.Char()
	PriceCode=fields.Char()
	LP_Eur=fields.Char()
	DE_Eur=fields.Char()
	D1_Eur=fields.Char()
	D2_Eur=fields.Char()
	purchase_price=fields.Float()
	stock=fields.Char()
	BackorderDate=fields.Date()
	ModifDate=fields.Datetime()
	default_code=fields.Char(index=True)

	eancode=fields.Char(index=True)
	manufacturer_id=fields.Many2one('res.partner', domain="[('manufacturer','=',True)]")

	def processfile(self,stats):
		logger.info("Start processfile")
		n=0
		dummy=0
		with open (stats.supplier_id.supplier_file, 'rb') as cleanfile:
			reader = csv.DictReader(cleanfile, delimiter=';')
			for row in reader:
				n+=1
				#pdb.set_trace()
				imported=self.create({'stats_id':stats.id, 
					'description':row['Description'],
					'supplier_part': row['ArtID'],
					'manuf_part':row['PartID'],
					'Class1':row['Class1'],
					'Class2':row['Class2'],
					'Class3':row['Class3'],
					'manufacturer':row['PublisherName'],
					'Version':row['Version'],
					'Language':row['Language'],
					'LP_Eur':row['LP_Eur'],
					'Trend':row['Trend'],
					'PriceGroup':row['PriceGroup'],
					'purchase_price':row['PricePersonal_Eur'].replace(",","."),
					'stock':row['Stock'],
					'eancode':row['EanCode'],
					})
				try:
					imported.BackorderDate=datetime.strptime(row['BackorderDate'],"%d/%m/%Y").date()
				except:
					dummy+=1

					# do nothing
					#imported.BackorderDate=datetime.now().date()

				try:
					imported.ModifDate=datetime.strptime(row['ModifDate'],"%d/%m/%Y %H:%M:%S")
				except:
					imported.ModifDate=datetime.strptime(row['ModifDate'],"%d/%m/%Y %H:%M:%S")

				imported.default_code=stats.supplier_id.supplier_prefix + ("0" * (8-len(imported.supplier_part)) + imported.supplier_part)
				if imported.eancode:
					imported.eancode= "0" * (13-len(imported.eancode)) + imported.eancode
					if not barcodenumber.check_code('ean13',imported.eancode):
						imported.eancode=''
				if (stats.supplier_id.supplier_num >0  and  n>stats.supplier_id.supplier_num):
					break
			cleanfile.close()
			stats.numparts=n
		logger.info("End processfile")



class product_template(models.Model):
	_inherit = 'product.template'
#	_sql_constraints = [('default_code_unique','UNIQUE(default_code)',"Internal ref must be unique")]

	#default_code=fields.Char(index=True)
	#ean13=fields.Char(index=True)
	manuf_part=fields.Char(string="Partnr", index=True)
	manufacturer=fields.Many2one('res.partner')
	last_stats_id=fields.Many2one('lubon_suppliers.import_stats', string="Last Imported")

class product_product(models.Model):
	_inherit = 'product.product'
	
	invoice_lines=fields.One2many('account.invoice.line','product_id')
	sales_order_lines=fields.One2many('sale.order.line','product_id')
	purchase_order_lines=fields.One2many('purchase.order.line','product_id')
	procurement_order=fields.One2many('procurement.order','product_id')
	stock_inventory_line=fields.One2many('stock.inventory.line','product_id')

	@api.multi
	def activate_all(self):
		for p in self:
			p.active=True;
	@api.multi
	def delete_products(self, supplier_debug):
		#pdb.set_trace()
		number=len(self)
		n=0
		for p in self:
			n+=1
			if (supplier_debug and n> 1000):
				break
			if 	supplier_debug:
				logger.info("processing:%s %d/%d",p.default_code,n,number)
			if not (p.sales_order_lines or p.purchase_order_lines or p.invoice_lines or p.procurement_order or p.stock_inventory_line):
				p.unlink()

			

class lubon_suppliers_import_stats(models.Model):
	_name='lubon_suppliers.import_stats'
	name=fields.Char()
	startfunc=fields.Char(string="Start function")
	supplier_id=fields.Many2one('res.partner')
	filename=fields.Char()
	start=fields.Datetime()
	stop_transfer=fields.Datetime(help="Time End file transfer")
	stop_csv=fields.Datetime(help="Time end csv import")
	elap_csv=fields.Float(string ="Duration csv")
	stop_brands=fields.Datetime(help="Time end brands import")
	elap_brands=fields.Float(string ="Duration brands")
	stop_products=fields.Datetime(help="Time end products")
	elap_products=fields.Float(string ="Duration products")
	elap_total=fields.Float(string ="Duration")
	numbrands=fields.Integer(string="Brands added")
	numparts=fields.Integer(string="Parts imported")
	numupdated=fields.Integer(string="Parts Updated")
	numcreated=fields.Integer(string="Parts Created")
	numdeleted=fields.Integer(string="Parts Deactivated")
	parts_ids=fields.One2many('lubon_suppliers.info_import','stats_id')
	sql_query01=fields.Text()
	sql_query02=fields.Text()

	@api.multi
	def processbrands(self):
		logger.info("Start processbrands")
		starttime=datetime.now()
		tempcr=self.env['lubon_suppliers.import_stats'].env.cr
		tempcr.execute("SELECT DISTINCT manufacturer "
					"FROM lubon_suppliers_info_import "
					"WHERE stats_id="+str(self.id))
		table_partners=self.env['res.partner']
		#update brand names for this supplier
		for brand in tempcr.fetchall():
			search=brand[0].encode('utf-8')

			partner=table_partners.search([('name', '=like', search),
											('manufacturer','=',True)])
			if self.supplier_id.supplier_debug:
				logger.info(search)
			if not(partner):
				partner=table_partners.create({'name': search,
										'manufacturer': True,
										'supplier': False,
										'customer': False})
				self.numbrands+=1
			else:
				partner.supplier=False
				partner.customer=False

		logger.info("Start updating brands on import")

		#update only brands of intrest for this supplier, to improve speed.		
		for brand in self.supplier_id.brand_ids:		
			parts=self.parts_ids.search([('manufacturer', '=ilike', brand.name)])
			for part in parts:
				part.manufacturer_id=brand.id

		self.stop_brands= datetime.now()
		self.elap_brands= (datetime.now()-starttime).seconds
		logger.info("End processbrands")


	@api.multi
	def processproducts(self):
		logger.info("Start processproducts")
		starttime=datetime.now()
	#	self.env.invalidate_all()
		tempcr=self.env['lubon_suppliers.import_stats'].env.cr
		sql_statement="""select i.id, manufacturer_id,stats_id, i.default_code,i.description,i.eancode,i.supplier_part  from lubon_suppliers_info_import as i 
		left outer join product_product as p  on(p.default_code = i.default_code) 
		where manufacturer_id is not null and p.id is null and 
		stats_id=""" + str(self.id)
		self.sql_query01=sql_statement
		tempcr.execute(sql_statement)
		newparts=tempcr.fetchall()
		table_products_products=self.env['product.product']
		table_products=self.env['product.template']
		table_prod_supplier=self.env['product.supplierinfo']
		parts=self.parts_ids.search(['&',('manufacturer_id','in',self.supplier_id.brand_ids.ids),('stats_id',"=",self.id)])
		self.numcreated=0
		self.numupdated=0
		#process newparts
		for part in newparts:
			#pdb.set_trace()
			part_starttime=datetime.now()
			self.numcreated+=1
			operation="Direct create - without search"
			product=table_products.create({'name': part[4],
									'default_code': part[3],										#'manufacturer': part.manufacturer_id.id,
									'ean13': part[5],
									})
			table_prod_supplier.create({'name':self.supplier_id.id,
												'product_tmpl_id':product.id,
												'product_code': part[6],
												})
			if self.supplier_id.supplier_debug:
				logger.info("Number: %d, Part: %s,Operation: %s, Duration:, %d",self.numupdated,part[3], operation, (datetime.now()-part_starttime).microseconds)
		#process changed parts
		sql_statement="""select p.product_tmpl_id, p.default_code, purchase_price, i.manuf_part,i.manufacturer_id, prodprice.product_template_id, maxcostdate, activeprice  from
(select lastcostrecord.product_template_id, price.cost as activeprice, maxcostdate from 
(select product_template_id, max(datetime) as maxcostdate from product_price_history as pr group by product_template_id) as lastcostrecord
left join
product_price_history as price on lastcostrecord.product_template_id = price.product_template_id
and maxcostdate=datetime) as prodprice 
left join product_product as p on p.product_tmpl_id=prodprice.product_template_id
left join lubon_suppliers_info_import as i on p.default_code=i.default_code
where (activeprice != i.purchase_price) and stats_id=""" + str(self.id)
		self.sql_query02=sql_statement
		tempcr2=self.env['lubon_suppliers.import_stats'].env.cr
		tempcr2.execute(sql_statement)
		changedparts=tempcr2.fetchall()
		#pdb.set_trace()
		for part in changedparts:
			part_starttime=datetime.now()
			self.numupdated+=1
			product=table_products.browse(part[0])
			product.update({'standard_price': part[2],
							'manuf_part': part[3],
							'manufacturer': part[4],
							'active': True,
							'categ_id': self.supplier_id.supplier_product_category_id.id,
							'route_ids': self.supplier_id.route_ids.ids,
							'type':self.supplier_id.supplier_product_type,
							'cost_method':self.supplier_id.supplier_product_cost_method,
							'valuation':self.supplier_id.supplier_product_valuation_method,
							'last_stats_id': self.id,
							'seller_id': self.supplier_id,
							})
			if self.supplier_id.supplier_debug:
					logger.info("Number: %d Part: %s, Duration: %d",self.numupdated, part[1], (datetime.now()-part_starttime).microseconds)





		# for part in parts:
		# 	part_starttime=datetime.now()
		# 	self.numupdated+=1
		# 	operation="Update"
		# 	search=part.default_code
		# 	#self.supplier_id.supplier_prefix + ("0" * (8-len(part.supplier_part)) + part.supplier_part)

		# 	product=table_products.search([('default_code','=',search)])#,('active',"in", [True,False])])
			
		# 	if len(product) >1:
		# 		logger.error("Multiple products found: "+ search)
		# 		pdb.set_trace()
		# 		for x in product:
		# 			x.unlink()
		# 		#parts.issue_id=self.supplier_id.id
		# 	else:
		# 		if not product:
		# 			operation="Create"
		# 			product=product.create({'name': part.description,
		# 									'default_code': search,
		# 									#'manufacturer': part.manufacturer_id.id,
		# 									#'manuf_part': part.manuf_part,
		# 									'ean13': part.eancode,
		# 									#'categ_id': self.supplier_id.supplier_product_category_id.id,
		# 									})
		# 			table_prod_supplier.create({'name':self.supplier_id.id,
		# 										'product_tmpl_id':product.id,
		# 										'product_code': part.supplier_part,
		# 										})
		# 			self.numcreated+=1
		# 			self.numupdated-=1

		# 		product.update({'manufacturer': part.manufacturer_id.id,
		# 						'manuf_part': part.manuf_part,
		# 						'active': True,
		# 						'categ_id': self.supplier_id.supplier_product_category_id.id,
		# 						'route_ids': self.supplier_id.route_ids.ids,
		# 						'standard_price':part.purchase_price,
		# 						'type':self.supplier_id.supplier_product_type,
		# 						'cost_method':self.supplier_id.supplier_product_cost_method,
		# 						'valuation':self.supplier_id.supplier_product_valuation_method,
		# 						'last_stats_id': self.id,
		# 						'seller_id': self.supplier_id,
		# 						})
		# 		if self.supplier_id.supplier_debug:
		# 			logger.info("Part: %s,Operation: %s, Duration:, %d",search, operation, (datetime.now()-part_starttime).microseconds)


			
		#parts=table_products.search(['&','&',('last_stats_id',"!=",False),('seller_id','=',self.supplier_id.id),('last_stats_id', "!=",self.id)])
		
		#parts=table_products.search([('default_code', "ilike",'TD%'),('seller_ids','not in',[self.supplier_id.id])])
		#self.numdeleted=len(parts)
		#for part in parts:
		#	part.active=False
		
#		self.stop_products= datetime.now()
		self.elap_products= (datetime.now()-starttime).seconds
		logger.info("End processproducts")
	
#class supplierbrands(models.Model):
#	_inherit="lubon_suppliers.supplierbrands"
#	fullyimported=fields.Boolean(default=False)

