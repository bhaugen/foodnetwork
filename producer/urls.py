from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',
    url(r'^producerdashboard/$', "producer.views.producer_dashboard", name="producer_dashboard"),

    # avail
    url(r'^inventoryselection/$', "producer.views.inventory_selection", name="producer_inventory_selection"),
    url(r'^inventoryupdate/(?P<prod_id>\d+)/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$',
        "producer.views.inventory_update", name="producer_inventory_update"),
    url(r'^produceravail/(?P<prod_id>\d+)/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$',
        "producer.views.produceravail", name="producer_avail"),

    # processes
    url(r'^processselection/$',  "producer.views.process_selection",
        name="producer_process_selection"),
    url(r'^newprocess/(?P<process_type_id>\d+)/$',
        "producer.views.new_process", name="producer_new_process"),
    url(r'^process/(?P<process_id>\d+)/$',  "producer.views.process",
        name="producer_process"),
    url(r'^deleteprocessconfirmation/(?P<process_id>\d+)/$',
        "producer.views.delete_process_confirmation", name="producer_delete_process_confirmation"),
    url(r'^deleteprocess/(?P<process_id>\d+)/$',
        "producer.views.delete_process", name="producer_delete_process"),
    #url(r'^editprocess/(?P<process_id>\d+)/$',  "producer.views.edit_process",
    #    name="producer_edit_process"),

    #product lists
    #url(r'^listselection/$', "producer.views.list_selection", name="list_selection"),
    #url(r'^newproductlist/(?P<cust_id>\d+)/$',
    #    "producer.views.new_product_list", name="create_product_list"),
    #url(r'^editproductlist/(?P<list_id>\d+)/$',
    #    "producer.views.edit_product_list", name="edit_product_list"),

    #plans
    url(r'^planselection/$', "producer.views.plan_selection", name="plan_selection"),
    url(r'^planningtable/(?P<member_id>\d+)/(?P<list_type>\w{1})/(?P<from_date>\w{10})/(?P<to_date>\w{10})/$', 
        "producer.views.planning_table", name='producer_planning_table'),
    url(r'^supplydemand/(?P<from_date>\w{10})/(?P<to_date>\w{10})/$',
        "producer.views.supply_and_demand", name='supply_demand'),
    url(r'^membersupplydemand/(?P<from_date>\w{10})/(?P<to_date>\w{10})/(?P<member_id>\d+)/$',
        "producer.views.member_supply_and_demand", name='producer_supply_demand'),
    url(r'^income/(?P<from_date>\w{10})/(?P<to_date>\w{10})/$',
        "producer.views.income", name='producer_income'),
    #url(r'^supplydemandweek/(?P<week_date>\w{10})/$',
    #    "producer.views.supply_and_demand_week", name='supply_and_demand_week'),

)


