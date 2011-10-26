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

    def test_inventory(self):
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
        self.assertEqual(response.context['available'][9].producer.short_name,
                         'New Producer')
        #todo: next, add and change some inventory, using all and one producer

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








