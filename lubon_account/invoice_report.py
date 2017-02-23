select x.company_id,
       x.type,
       internal_number as invoice_number,
       date_invoice,
       x.period_id as invoice_period_id,
       amount_total,
       z.id,
       z.name,
       r.journal_id,
       r.date as date_reconcile,
       r.debit,
       r.credit,(amount_total-r.debit-r.credit) as amount_open,
       r.period_id as payment_period_id 
from (select l.company_id,l.id,i.date_invoice,i.type, i.internal_number,i.amount_total,l.reconcile_id, i.account_id,i.period_id 
   from account_move_line l  
   join account_invoice i on l.move_id=i.move_id and l.account_id=i.account_id) x 
left join account_move_line r on r.reconcile_id=x.reconcile_id and x.id!=r.id 
left join account_move_reconcile z on z.id=r.reconcile_id 
order by company_id,type,invoice_number
