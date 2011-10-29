import datetime
from decimal import *

from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User

from distribution.models import *

class EmptyDatabaseTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('alice', 'alice@whatever.com', 'password')
        logged_in = self.client.login(username='alice', password='password')

    def test_dashboard(self):
        response = self.client.get('/distribution/dashboard/', {})
        #import pdb; pdb.set_trace()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["food_net"], None)


class DistributionTabsTest(TestCase):

    fixtures = ["distribution_test.json"]

    def setUp(self):
        #self.fn = FoodNetwork(
        #    short_name="FN",
        #    long_name="Food Network",
        #    customer_fee=Decimal(".1"),
        #    producer_fee=Decimal(".1"),
        #)
        #self.fn.save()
        self.client = Client()
        self.user = User.objects.create_user('alice', 'alice@whatever.com', 'password')
        logged_in = self.client.login(username='alice', password='password')

    def test_dashboard(self):
        response = self.client.get('/distribution/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['food_network'].short_name, 'Demo' )
        self.assertEqual(response.context['shorts'][0].product.short_name, 'Cucumbers')
        self.assertEqual(response.context['order_changes'][0].product.short_name, 'Cucumbers')
        self.assertEqual(len(response.context['orders']), 2)
        self.assertEqual(len(response.context['items']), 11)
        #import pdb; pdb.set_trace()
        response = self.client.post('/distribution/resetdate/',
                               {'next_delivery_date': '2011-09-01', })
        self.assertEqual(response.status_code, 302)
        #import pdb; pdb.set_trace()
        response = self.client.get('/distribution/dashboard/')
        self.assertEqual(response.context['delivery_date'], datetime.date(2011, 9, 1))

    def test_avail_emails(self):
        response = self.client.get('/distribution/emailselection/')
        self.assertEqual(response.status_code, 200)
        #todo: emails based on today's date, won't work for testing

    def test_new_producer_inventory(self):
        response = self.client.get('/distribution/inventoryselection/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['available']), 11)
        response = self.client.post('/distribution/inventoryselection/',
                               {u'received': [u''], 
                                u'product': [u'37'], 
                                u'producer': [u''], 
                                u'new_producer_name': [u'New Producer'], 
                                u'custodian': [u'1'], 
                                u'notes': [u'Winesap'], 
                                u'field_id': [u'W3'], 
                                u'inventory_date': [u'2011-08-26'], 
                                u'submit-unplanned': [u'Add unplanned inventory'], 
                                u'planned': [u'200'], 
                                u'freeform_lot_id': [u'45678']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['available']), 12)
        avails = response.context['available']
        new_avail = None
        for avail in avails:
            if avail.producer.short_name == 'New Producer':
                new_avail = avail
        if new_avail:
            self.assertEqual(new_avail.notes, 'Winesap')
        else:
            self.fail("no new avail")        

    def test_add_one_producer_inventory(self):
        response = self.client.get('/distribution/inventoryselection/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['available']), 11)
        response = self.client.post('/distribution/inventoryselection/',
            {u'avail_date': [u'2011-08-26'], 
             u'producer': [u'29'], 
             u'submit-planned': [u'Add or change inventory ']})
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/distribution/inventoryupdate/29/2011/8/26/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['item_forms']), 4)
        response = self.client.post('/distribution/inventoryupdate/29/2011/8/26/',
            {u'81-freeform_lot_id': [u''], 
             u'81-notes': [u''], 
             u'46-field_id': [u''], 
             u'55-notes': [u''], 
             u'46-received': [u'0'], 
             u'60-notes': [u'With greens'], 
             u'46-item_id': [u''], 
             u'81-received': [u'0'], 
             u'55-planned': [u'0'], 
             u'60-expiration_date': [u'2011-09-01'], 
             u'81-item_id': [u''], 
             u'60-prod_id': [u'60'], 
             u'46-custodian': [u''], 
             u'46-inventory_date': [u'2011-08-26'], 
             u'55-prod_id': [u'55'], 
             u'81-prod_id': [u'81'], 
             u'46-freeform_lot_id': [u''], 
             u'60-received': [u'0'],
             u'81-expiration_date': [u'2011-09-01'], 
             u'55-field_id': [u''], 
             u'81-field_id': [u''], 
             u'46-notes': [u''], 
             u'55-received': [u'0'], 
             u'55-item_id': [u''], 
             u'46-planned': [u'0'], 
             u'producer-id': [u'29'], 
             u'avail-date': [u'Aug. 26, 2011'], 
             u'81-custodian': [u''], 
             u'46-expiration_date': [u'2011-09-01'], 
             u'60-field_id': [u'W2'], 
             u'55-expiration_date': [u'2011-09-01'], 
             u'55-custodian': [u''], 
             u'60-inventory_date': [u'2011-08-26'], 
             u'55-inventory_date': [u'2011-08-26'], 
             u'46-prod_id': [u'46'], 
             u'81-planned': [u'0'], 
             u'60-planned': [u'100'], 
             u'55-freeform_lot_id': [u''], 
             u'81-inventory_date': [u'2011-08-26'], 
             u'60-freeform_lot_id': [u'12345'], 
             u'60-item_id': [u''], 
             u'60-custodian': [u'']})
        #import pdb; pdb.set_trace()
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/distribution/inventoryselection/')
        self.assertEqual(response.status_code, 200)
        #import pdb; pdb.set_trace()
        avails = response.context['available']
        self.assertEqual(len(avails), 12)
        new_avail = None
        for avail in avails:
            if avail.producer.short_name == 'Driftwood':
                new_avail = avail
        if new_avail:
            self.assertEqual(new_avail.notes, 'With greens')
        else:
            self.fail("no new avail")

#todo: next, add and change some inventory, using all and one producer

    def test_change_one_producer_inventory(self):
        response = self.client.get('/distribution/inventoryselection/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['available']), 11)
        response = self.client.post('/distribution/inventoryselection/',
            {u'avail_date': [u'2011-08-26'], 
             u'producer': [u'35'], 
             u'submit-planned': [u'Add or change inventory ']})
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/distribution/inventoryupdate/35/2011/8/26/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['item_forms']), 2)
        response = self.client.post('/distribution/inventoryupdate/35/2011/8/26/',
            {u'55-notes': [u''], 
             u'76-prod_id': [u'76'], 
             u'55-planned': [u'0'], 
             u'76-freeform_lot_id': [u'54321'], 
             u'76-expiration_date': [u'2011-09-01'], 
             u'55-prod_id': [u'55'], 
             u'76-inventory_date': [u'2011-08-26'], 
             u'76-notes': [u'changed'], 
             u'76-custodian': [u''], 
             u'55-field_id': [u''], 
             u'76-received': [u'20'], 
             u'55-received': [u'0'], 
             u'55-item_id': [u''], 
             u'producer-id': [u'35'], 
             u'avail-date': [u'Aug. 26, 2011'], 
             u'55-expiration_date': [u'2011-09-01'], 
             u'76-field_id': [u'N3'], 
             u'55-custodian': [u''], 
             u'55-inventory_date': [u'2011-08-26'], 
             u'55-freeform_lot_id': [u''], 
             u'76-item_id': [u'95'], 
             u'76-planned': [u'22']})
        #import pdb; pdb.set_trace()
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/distribution/inventoryselection/')
        self.assertEqual(response.status_code, 200)
        #import pdb; pdb.set_trace()
        avails = response.context['available']
        self.assertEqual(len(avails), 11)
        changed_avail = None
        for avail in avails:
            if avail.producer.short_name == 'FV':
                changed_avail = avail
        if changed_avail:
            self.assertEqual(changed_avail.avail_qty(), 20)
        else:
            self.fail("no changed avail")

    def test_process(self):
        response = self.client.get('/distribution/processselection/')
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/distribution/processselection/',
                                    {'process_type': 5,})
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/distribution/newprocess/5/')
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/distribution/newprocess/5/',
                                   {u'output-1-freeform_lot_id': [u'98765'], 
                                    u'output-0-field_id': [u''], 
                                    u'service-1-from_whom': [u'12'], 
                                    u'output-1-producer': [u'29'], 
                                    u'output-0-product': [u'118'], 
                                    u'output-1-product': [u'117'], 
                                    u'service-MAX_NUM_FORMS': [u''], 
                                    u'output-0-producer': [u'29'], 
                                    u'output-1-field_id': [u''], 
                                    u'output-MAX_NUM_FORMS': [u''], 
                                    u'output-INITIAL_FORMS': [u'0'], 
                                    u'inputcreation-freeform_lot_id': [u'98765'], 
                                    u'inputcreation-product': [u'115'], 
                                    u'service-TOTAL_FORMS': [u'2'], 
                                    u'output-1-planned': [u'400'], 
                                    u'service-INITIAL_FORMS': [u'0'], 
                                    u'inputcreation-planned': [u'2000'], 
                                    u'output-1-custodian': [u'12'], 
                                    u'service-0-service_type': [u'1'], 
                                    u'output-0-custodian': [u'12'], 
                                    u'service-1-amount': [u'400'], 
                                    u'output-TOTAL_FORMS': [u'2'], 
                                    u'service-1-service_type': [u'2'], 
                                    u'service-0-amount': [u'300'], 
                                    u'service-0-from_whom': [u'12'], 
                                    u'inputcreation-field_id': [u''], 
                                    u'inputcreation-producer': [u'29'], 
                                    u'output-0-planned': [u'200'], 
                                    u'output-0-freeform_lot_id': [u'98765']}
                                   )
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/distribution/process/11/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['process'].id, 11)
        #import pdb; pdb.set_trace()

    def test_new_order(self):
        response = self.client.get('/distribution/orderselection/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['changeable_orders']), 6)
        self.assertEqual(len(response.context['unpaid_orders']), 8)
        response = self.client.get('/distribution/neworder/30/2011/8/26/')
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/distribution/neworder/30/2011/8/26/',
            {u'79-avail': [u'40'], 
             u'42-quantity': [u'0'], 
             u'95-prod_id': [u'95'], 
             u'42-prod_id': [u'42'], 
             u'118-notes': [u''], 
             u'54-quantity': [u'10'], 
             u'118-avail': [u'200'], 
             u'118-prod_id': [u'118'], 
             u'94-quantity': [u'0'], 
             u'88-quantity': [u'0'], 
             u'76-unit_price': [u'3.00'], 
             u'88-prod_id': [u'88'], 
             u'42-avail': [u'30'], 
             u'44-ordered': [u'10'], 
             u'92-avail': [u'30'], 
             u'54-ordered': [u'30'], 
             u'42-notes': [u''], 
             u'94-ordered': [u'4'], 
             u'distributor': [u'38'], 
             u'118-ordered': [u'90'], 
             u'117-ordered': [u'60'], 
             u'117-notes': [u''], 
             u'92-unit_price': [u'3.00'], 
             u'54-avail': [u'25'], 
             u'117-prod_id': [u'117'], 
             u'79-quantity': [u'0'], 
             u'42-ordered': [u'40'], 
             u'transportation_fee': [u'20'], 
             u'54-notes': [u'Brown please'], 
             u'76-ordered': [u'12'], 
             u'79-notes': [u''], 
             u'76-quantity': [u'0'], 
             u'purchase_order': [u''], 
             u'92-ordered': [u'0'], 
             u'79-prod_id': [u'79'], 
             u'44-avail': [u'40'], 
             u'92-quantity': [u'0'], 
             u'76-avail': [u'20'], 
             u'94-prod_id': [u'94'], 
             u'95-quantity': [u'0'], 
             u'92-notes': [u''], 
             u'95-notes': [u''], 
             u'79-unit_price': [u'3.00'], 
             u'88-ordered': [u'0'], 
             u'94-notes': [u''], 
             u'44-notes': [u''], 
             u'44-prod_id': [u'44'], 
             u'94-avail': [u'20'], 
             u'54-prod_id': [u'54'], 
             u'95-ordered': [u'10'], 
             u'order_date': [u'2011-10-28'],
             u'76-prod_id': [u'76'], 
             u'88-notes': [u''], 
             u'117-avail': [u'300'], 
             u'88-avail': [u'26'], 
             u'44-unit_price': [u'2.00'], 
             u'117-unit_price': [u'8.00'], 
             u'44-quantity': [u'0'], 
             u'95-avail': [u'45'], 
             u'95-unit_price': [u'0.00'], 
             u'42-unit_price': [u'2.00'], 
             u'117-quantity': [u'0'], 
             u'88-unit_price': [u'3.00'], 
             u'76-notes': [u''], 
             u'118-quantity': [u'20'], 
             u'79-ordered': [u'0'], 
             u'118-unit_price': [u'10.00'], 
             u'92-prod_id': [u'92'], 
             u'94-unit_price': [u'3.00'], 
             u'delivery_date': [u'2011-08-26'], 
             u'54-unit_price': [u'4.00']})
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/distribution/order/9/')
        self.assertEqual(response.status_code, 200)
        order = response.context['order']
        self.assertEqual(order.orderitem_set.all().count(), 2)
        item = order.orderitem_set.all()[1]
        self.assertEqual(item.quantity, 10)
        self.assertEqual(item.notes, 'Brown please')
        self.assertEqual(order.transportation_fee(), 20)
        self.assertEqual(order.grand_total(), Decimal('284.00'))

    def test_change_order(self):
        response = self.client.get('/distribution/orderselection/')
        self.assertEqual(response.status_code, 200)
        order = Order.objects.get(pk=8)
        items = order.orderitem_set.all()
        item_count = items.count()
        self.assertEqual(item_count, 3)
        item = order.orderitem_set.all()[2]
        self.assertEqual(item.quantity, 10)
        self.assertEqual(order.transportation_fee(), 22)
        self.assertEqual(order.grand_total(), Decimal('309.10'))
        response = self.client.get('/distribution/editorder/8/')
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/distribution/editorder/8/',
            {u'79-avail': [u'40'], 
             u'42-quantity': [u'0'], 
             u'95-prod_id': [u'95'], 
             u'42-prod_id': [u'42'], 
             u'118-notes': [u'trim that fat!'], 
             u'54-quantity': [u'15'], 
             u'118-avail': [u'200'], 
             u'118-prod_id': [u'118'], 
             u'94-quantity': [u'0'], 
             u'88-quantity': [u'0'], 
             u'76-unit_price': [u'3.00'], 
             u'88-prod_id': [u'88'], 
             u'42-avail': [u'30'], 
             u'44-ordered': [u'10'], 
             u'92-avail': [u'30'], 
             u'54-ordered': [u'25'], 
             u'42-notes': [u''], 
             u'94-ordered': [u'4'], 
             u'distributor': [u'37'], 
             u'118-ordered': [u'70'], 
             u'117-ordered': [u'60'], 
             u'117-notes': [u''], 
             u'92-unit_price': [u'3.00'], 
             u'54-avail': [u'25'], 
             u'117-prod_id': [u'117'], 
             u'79-quantity': [u'0'], 
             u'42-ordered': [u'40'], 
             u'transportation_fee': [u'33'], 
             u'54-notes': [u'Toasty brown ones, please.'], 
             u'76-ordered': [u'12'], 
             u'79-notes': [u''], 
             u'76-quantity': [u'7'], 
             u'purchase_order': [u'PO 54321'], 
             u'92-ordered': [u'0'],
             u'79-prod_id': [u'79'], 
             u'44-avail': [u'40'], 
             u'92-quantity': [u'0'], 
             u'76-avail': [u'20'], 
             u'94-prod_id': [u'94'], 
             u'95-quantity': [u'5'], 
             u'92-notes': [u''], 
             u'95-notes': [u''], 
             u'79-unit_price': [u'3.00'], 
             u'88-ordered': [u'0'], 
             u'94-notes': [u''], 
             u'44-notes': [u''], 
             u'44-prod_id': [u'44'], 
             u'94-avail': [u'20'], 
             u'54-prod_id': [u'54'], 
             u'95-ordered': [u'15'], 
             u'order_date': [u'2011-09-02'], 
             u'76-prod_id': [u'76'], 
             u'88-notes': [u''], 
             u'117-avail': [u'300'], 
             u'88-avail': [u'26'], 
             u'44-unit_price': [u'2.00'], 
             u'117-unit_price': [u'8.00'], 
             u'44-quantity': [u'0'], 
             u'95-avail': [u'45'], 
             u'95-unit_price': [u'0.00'], 
             u'42-unit_price': [u'2.00'], 
             u'117-quantity': [u'0'], 
             u'88-unit_price': [u'3.00'], 
             u'76-notes': [u'edible flowers?'], 
             u'118-quantity': [u'20'], 
             u'79-ordered': [u'0'], 
             u'118-unit_price': [u'10.00'], 
             u'92-prod_id': [u'92'], 
             u'94-unit_price': [u'3.00'], 
             u'delivery_date': [u'2011-08-26'], 
             u'54-unit_price': [u'4.00']}
            )
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/distribution/order/8/')
        self.assertEqual(response.status_code, 200)
        order = response.context['order']
        self.assertEqual(order.orderitem_set.all().count(), item_count + 1)
        item = order.orderitem_set.all()[2]
        self.assertEqual(item.quantity, 15)
        self.assertEqual(order.transportation_fee(), 33)
        self.assertEqual(order.grand_total(), Decimal('342.10'))

    def test_shorts(self):
        response = self.client.get('/distribution/shorts/2011/8/26/')
        self.assertEqual(response.status_code, 200)
        shorts_table = response.context['shorts_table']
        self.assertEqual(len(shorts_table.rows), 1)
        response = self.client.post('/distribution/shorts/2011/8/26/',
            {u'42-23-quantity': [u'30'], 
             u'42-total_ordered': [u'30'], 
             u'42-quantity_short': [u'0'], 
             u'42-23-item_id': [u'23']})
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/distribution/shortschanges/2011/8/26/')
        self.assertEqual(response.status_code, 200)
        changes = response.context['changed_items']
        self.assertEqual(len(changes), 1)
        item = changes[0]
        self.assertEqual(item.quantity, 30)
        self.assertEqual(item.orig_qty(), 40)
        

