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

    #fixtures = ["distribution_test.json"]

    def setUp(self):
        self.fn = FoodNetwork(
            short_name="FN",
            long_name="Food Network",
            customer_fee=Decimal(".1"),
            producer_fee=Decimal(".1"),
        )
        self.fn.save()
        self.client = Client()
        self.user = User.objects.create_user('alice', 'alice@whatever.com', 'password')
        logged_in = self.client.login(username='alice', password='password')

    def test_dashboard(self):
        response = self.client.get('/distribution/dashboard/', {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['food_network'].short_name, 'FN' ) 
        response = self.client.post('/distribution/resetdate/',
                               {'next_delivery_date': '2011-09-01', })
        self.assertEqual(response.status_code, 302)
        #import pdb; pdb.set_trace()
        response = self.client.get('/distribution/dashboard/', {})
        self.assertEqual(response.context['delivery_date'], datetime.date(2011, 9, 1))

    def test_dashboard_again(self):
        response = self.client.get('/distribution/dashboard/', {})
        self.assertEqual(response.context['delivery_date'], datetime.date(2011, 9, 1))


