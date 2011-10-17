import datetime
from decimal import *

from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User

from distribution.models import *

class EconomicEventTest(TestCase):
    def setUp(self):
        self.party_1 = Party(
            short_name="Somebody",
            long_name="Somebody",
        )
        self.party_1.save()
        self.client = Client()
        self.user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
        logged_in = self.client.login(username='john', password='johnpassword')
        #import pdb; pdb.set_trace()
        self.party_2 = Party(
            short_name="Somebody Else",
            long_name="Somebody Else",
        )
        self.party_2.save()


    def test_something(self):
        #import pdb; pdb.set_trace()
        pass

class FeesTest(TestCase):
    def setUp(self):
        self.fn = FoodNetwork(
            short_name="FN",
            long_name="Food Network",
            customer_fee=Decimal(".1"),
            producer_fee=Decimal(".1"),
        )
        self.fn.save()
        self.product=Product(
            short_name="Apples",
            long_name="Apples",
            price=Decimal("1.00"),
        )
        self.product.save()
        self.customer=Customer(
            short_name="Customer",
            long_name="Customer",
        )
        self.customer.save()
        producer=Producer(
            short_name="Producer",
            long_name="Producer",
        )
        producer.save()
        self.order=Order(
            customer=self.customer,
            order_date=datetime.date.today(),
            delivery_date=datetime.date.today()
        )
        self.order.save()
        order_item=OrderItem(
            order=self.order,
            product=self.product,
            quantity=Decimal("10.00"),
            unit_price=self.product.price,
        )
        order_item.save()
        lot=InventoryItem(
            product=self.product,
            producer=producer,
            inventory_date=datetime.date.today(),
            planned=order_item.quantity,
        )
        lot.save()
        delivery=InventoryTransaction(
            transaction_date=datetime.date.today(),
            from_whom=self.fn,
            to_whom=self.customer,
            amount=order_item.quantity,
            inventory_item=lot,
            order_item=order_item,
            unit_price=self.product.price,
        )
        delivery.save()

    def test_fees(self):
        order_item = self.order.orderitem_set.all()[0]
        delivery=order_item.inventorytransaction_set.all()[0]
        self.assertEqual(self.order.total_price(),Decimal('10.00'))
        self.assertEqual(self.order.customer_fee(),Decimal('1.00'))
        self.assertEqual(self.order.grand_total(),Decimal('11.00'))
        self.assertEqual(order_item.extended_producer_fee(),Decimal('1.00'))
        self.assertEqual(delivery.due_to_member(),Decimal('9.00'))
        #import pdb; pdb.set_trace()


