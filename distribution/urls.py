from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template

from distribution.views import *

urlpatterns = patterns('',
    url(r'^dashboard/$', dashboard, name="dashboard"),

    # orders
    url(r'^orderdeliveries/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$', orders_with_deliveries),
    (r'^orderselection/$', order_selection),
    url(r'^neworder/(?P<cust_id>\d+)/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$',
        new_order, name="new_order"),
    url(r'^editorder/(?P<order_id>\d+)/$', edit_order, name="staff_edit_order"),
    url(r'^orderupdate/(?P<cust_id>\d+)/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$', order_update),
    url(r'^orderbylot/(?P<cust_id>\d+)/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$', order_by_lot),
    url(r'^order/(?P<order_id>\d+)/$', order, name="distribution_order"),
    url(r'^orderwithlots/(?P<order_id>\d+)/$', order_with_lots),
    (r'^ordertableselection/$', order_table_selection),
    url(r'^ordertable/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$', order_table, name="order_table"),
    url(r'^ordertablebyproduct/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$', order_table_by_product, name="order_table_by_product"),
    url(r'^shorts/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$', shorts, name="shorts"),
    url(r'^shortschanges/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$', shorts_changes, name="shorts_changes"),
    url(r'^ordercsv/(?P<delivery_date>\w{10})/$', order_csv, name="export_orders_as_csv"),
    url(r'^ordercsvbyproduct/(?P<delivery_date>\w{10})/$', order_csv_by_product, name="order_csv_by_product"),
    url(r'^sendorderemails/(?P<cust_id>\d+)/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$',
        send_order_emails, name="send_order_emails"),

    # processes
    url(r'^processselection/$', process_selection, name="process_selection"),
    url(r'^newprocess/(?P<process_type_id>\d+)/$', new_process),
    url(r'^process/(?P<process_id>\d+)/$', process, name="process"),
    url(r'^deleteprocessconfirmation/(?P<process_id>\d+)/$', delete_process_confirmation, name="delete_process_confirmation"),
    url(r'^deleteprocess/(?P<process_id>\d+)/$', delete_process, name="delete_process"),
    url(r'^editprocess/(?P<process_id>\d+)/$', edit_process, name="edit_process"),

    # plans
    (r'^planselection/$', plan_selection),
    url(r'^planupdate/(?P<prod_id>\d+)/$', plan_update),
    url(r'^planningtable/(?P<member_id>\d+)/(?P<list_type>\w{1})/(?P<from_date>\w{10})/(?P<to_date>\w{10})/$', planning_table, name='planning_table'),
    url(r'^producerplan/(?P<prod_id>\d+)/$', producerplan),
    url(r'^supplydemand/(?P<from_date>\w{10})/(?P<to_date>\w{10})/$', supply_and_demand, name='supply_demand'),
    url(r'^membersupplydemand/(?P<from_date>\w{10})/(?P<to_date>\w{10})/(?P<member_id>\d+)/$',
        member_supply_and_demand, name='member_supply_demand'),
    url(r'^income/(?P<from_date>\w{10})/(?P<to_date>\w{10})/$', income, name='income'),
    url(r'^supplydemandweek/(?P<tabs>\w{1})/(?P<week_date>\w{10})/$', supply_and_demand_week, name='supply_and_demand_week'),

    # avail
    (r'^inventoryselection/$', inventory_selection),
    url(r'^inventoryupdate/(?P<prod_id>\d+)/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$', inventory_update),
    url(r'^allinventoryupdate/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$',
        all_inventory_update),
    url(r'^produceravail/(?P<prod_id>\d+)/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$', produceravail),
    url(r'^availcsv/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$',
        availability_csv, name="availability_csv"),

    # payments
    (r'^paymentselection/$', payment_selection),
    (r'^paymentupdateselection/$', payment_update_selection),
    url(r'^producerpayments/(?P<prod_id>\d+)/(?P<from_date>\w{10})/(?P<to_date>\w{10})/(?P<due>\d{1})/(?P<paid_member>\w+)/$', producer_payments),
    url(r'^paymentupdate/(?P<producer_id>\d+)/(?P<payment_id>\d+)/$', payment_update),
    url(r'^customerpaymentupdate/(?P<customer_id>\d+)/(?P<payment_id>\d+)/$',
        customer_payment_update),
    url(r'^payment/(?P<payment_id>\d+)/$', payment),
    url(r'^customerpayment/(?P<payment_id>\d+)/$', customer_payment),

    # deliveries
    (r'^deliveryselection/$', delivery_selection),
    url(r'^deliveryupdate/(?P<cust_id>\d+)/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$', delivery_update),
    
    # json
    url(r'^jsoncustomer/(?P<customer_id>\d+)/$', json_customer_info),
    url(r'^jsondistributor/(?P<distributor_id>\d+)/$', json_distributor_info),
    url(r'^jsonproducer/(?P<producer_id>\d+)/$', json_producer_info),    
    url(r'^jsonpayments/(?P<producer_id>\d+)/$', json_payments),
    url(r'^jsoncustomerpayments/(?P<customer_id>\d+)/$', json_customer_payments),
    
    # dojo
    url(r'^dojoproducts/$', dojo_products, name="dojo_products"),
    url(r'^jsonproducts/$', json_products, name="json_products"),
    url(r'^jsonproducts/(?P<product_id>\d+)$', json_products, name="json_products"),
    url(r'^dojoplanningtable/(?P<member_id>\d+)/(?P<list_type>\w{1})/(?P<from_date>\w{10})/(?P<to_date>\w{10})/$', 
        dojo_planning_table, name='dojo_planning_table'),
    url(r'^jsonplanningtable/(?P<member_id>\d+)/(?P<list_type>\w{1})/(?P<from_date>\w{10})/(?P<to_date>\w{10})/$', 
        json_planning_table, name='json_planning_table'),
    url(r'^jsonplanningtable/(?P<member_id>\d+)/(?P<list_type>\w{1})/(?P<from_date>\w{10})/(?P<to_date>\w{10})/(?P<row_id>\d+)$', 
        json_planning_table, name='json_planning_table'),
    url(r'^dojomemberplans/(?P<from_date>\w{10})/(?P<to_date>\w{10})/(?P<member_id>\d+)/$',
        dojo_member_plans, name='dojo_member_plans'),
    url(r'^jsonmemberplans/(?P<from_date>\w{10})/(?P<to_date>\w{10})/(?P<member_id>\d+)/$',
        json_member_plans, name='json_member_plans'),
    url(r'^dojosupplydemand/(?P<from_date>\w{10})/(?P<to_date>\w{10})/$',
        dojo_supply_and_demand, name='dojo_supply_demand'),
    url(r'^jsonsupplydemand/(?P<from_date>\w{10})/(?P<to_date>\w{10})/$',
        json_supply_and_demand, name='json_supply_demand'),
    url(r'^dojoincome/(?P<from_date>\w{10})/(?P<to_date>\w{10})/$', dojo_income,
        name='dojo_income'),
    url(r'^jsonincome/(?P<from_date>\w{10})/(?P<to_date>\w{10})/$', json_income,
        name='json_income'),
    url(r'^dojosupplydemandweek/(?P<tabs>\w{1})/(?P<week_date>\w{10})/$',
        dojo_supply_and_demand_week, name='dojo_supply_and_demand_week'),
    url(r'^jsonsupplydemandweek/(?P<week_date>\w{10})/$',
        json_supply_and_demand_week, name='json_supply_and_demand_week'),

    
    # invoices
    (r'^invoiceselection/$', invoice_selection),
    url(r'^invoices/(?P<order_state>\d{1})/(?P<cust_id>\d+)/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$',
        invoices, name="invoices"),
    url(r'^sendinvoices/(?P<cust_id>\d+)/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$',
        send_invoices, name="send_invoices"),

    # statements
    (r'^statementselection/$', statement_selection),
    url(r'^statements/(?P<from_date>\w{10})/(?P<to_date>\w{10})/$', statements),

    # reports
    (r'^reportselection/$', report_selection),
    url(r'^receiptsandsales/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$', receipts_and_sales, name="receipts_and_sales"),
    url(r'^orderedvsavailable/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$',
        ordered_vs_available, name="ordered_vs_available"),
    url(r'^monthlysales/(?P<from_date>\w{10})/(?P<to_date>\w{10})/$',
        monthly_sales, name='monthly_sales'),

    # emails
    url(r'^emailselection/$', email_selection, name="email_selection"),
    url(r'^availemailprep/(?P<cycles>\w+)/$', avail_email_prep, name="avail_email_prep"),
    url(r'^sendfreshlist/$', send_fresh_list, name="send_fresh_list"),
    url(r'^sendpickuplist/$', send_pickup_list, name="send_pickup_list"),
    url(r'^senddeliverylist/$', send_delivery_list, name="send_delivery_list"),
    url(r'^sendordernotices/$', send_order_notices, name="send_order_notices"),
    url(r'^sendshortchangenotices/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$', send_short_change_notices, name="send_short_change_notices"),
    
    url(r'^resetdate/$', reset_date, name='reset_date'),
    (r'^notices/', include('notification.urls')),


)

