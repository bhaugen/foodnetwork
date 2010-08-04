
from django.test import TestCase
from django.test import Client
from django import template
from django.db.models import get_model
from django.contrib.auth.models import User

class Testmaker(TestCase):
    """ Test Operational Tabs

        Created by TestMaker and then modified 
        to add logged in user, eliminate fixture reloads,
        and remove irrelevant assertions that did not work.
    """

    fixtures = ["distribution_testmaker.json"]


    def test_operational_tabs(self):
        john = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
        c = Client()
        logged_in = c.login(username='john', password='johnpassword')
        r = c.get('/dashboard/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['week_form']), u'<tr><th><label for="id_current_week">Current week:</label></th><td><input name="current_week" value="2010-01-18" type="text" id="id_current_week" dojoType="dijit.form.DateTextBox" constraints="{datePattern:&#39;yyyy-MM-dd&#39;}" /></td></tr>')
        self.assertEqual(unicode(r.context[-1]['item_list']), u'[<InventoryItem: Vegetable Producer Beets 2010-01-18>, <InventoryItem: Vegetable Producer Carrots 2010-01-18>, <InventoryItem: Meat Producer Steer 2010-01-18>, <InventoryItem: Meat Producer Beef Roast 2010-01-18>, <InventoryItem: Meat Producer Beef Steak 2010-01-18>]')
        self.assertEqual(unicode(r.context[-1]['food_network_name']), u'Demo Food Network')
        self.assertEqual(unicode(r.context[-1]['order_date']), u'2010-01-18')
    #def test_resetweek_126712782024(self):
        r = c.post('/resetweek/', {'current_week': '2010-02-22', })
    #def test_dashboard_126712782032(self):
        r = c.get('/dashboard/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['week_form']), u'<tr><th><label for="id_current_week">Current week:</label></th><td><input name="current_week" value="2010-02-22" type="text" id="id_current_week" dojoType="dijit.form.DateTextBox" constraints="{datePattern:&#39;yyyy-MM-dd&#39;}" /></td></tr>')
        self.assertEqual(unicode(r.context[-1]['item_list']), u'[]')
        self.assertEqual(unicode(r.context[-1]['food_network_name']), u'Demo Food Network')
        self.assertEqual(unicode(r.context[-1]['order_date']), u'2010-02-22')
    #def test_planselection_126712782479(self):
        r = c.get('/planselection/', {})
        self.assertEqual(r.status_code, 200)
    #def test_jsonproducer2_126712782987(self):
        r = c.get('/jsonproducer/2/', {})
        self.assertEqual(r.status_code, 200)
    #def test_planselection_126712783104(self):
        r = c.post('/planselection/', {'producer': '2', })
    #def test_planupdate2_126712783108(self):
        r = c.get('/planupdate/2/', {})
        self.assertEqual(r.status_code, 200)
    #def test_planupdate2_126712783342(self):
        r = c.post('/planupdate/2/', {'Beets-from_date': '2010-02-25', 'Beef Steak-quantity': '10000', 'Beef, Side-from_date': '2010-02-25', 'Beef, Side-to_date': '2010-02-25', 'Carrots-parents': 'Vegetables', 'Beef Steak-item_id': '2', 'Beef Steak-prodname': 'Beef Steak', 'Carrots-quantity': '0', 'Beef Roast-from_date': '2010-01-01', 'Steer-distributor': '5', 'Steer-parents': 'Live Animal', 'Carrots-item_id': '', 'Beef Steak-from_date': '2010-01-01', 'Beets-quantity': '0', 'Beef Roast-distributor': '5', 'Steer-from_date': '2010-01-01', 'Beets-item_id': '', 'Beets-prodname': 'Beets', 'Beef, Side-parents': 'Beef Section', 'Carrots-distributor': '5', 'Beets-parents': 'Vegetables', 'Beef Steak-to_date': '2011-01-11', 'Steer-quantity': '20000', 'Steer-prodname': 'Steer', 'Beef, Side-item_id': '', 'Beets-to_date': '2010-02-25', 'Steer-to_date': '2011-01-11', 'Beef, Side-prodname': 'Beef, Side', 'Steer-item_id': '3', 'Beef, Side-quantity': '0', 'Beef Steak-parents': 'Beef Cuts', 'Carrots-prodname': 'Carrots', 'Beef Steak-distributor': '5', 'Beef Roast-prodname': 'Beef Roast', 'producer-id': '2', 'Carrots-to_date': '2010-02-25', 'Beef Roast-to_date': '2011-01-11', 'Carrots-from_date': '2010-02-25', 'Beef Roast-parents': 'Beef Cuts', 'Beets-distributor': '5', 'Beef Roast-quantity': '10000', 'Beef Roast-item_id': '1', 'Beef, Side-distributor': '5', })
    #def test_producerplan2_126712783362(self):
        r = c.get('/producerplan/2/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['plans']), u'[<ProductPlan: Meat Producer Beef Roast 2010-01-01 2010-01-01 10000>, <ProductPlan: Meat Producer Beef Steak 2010-01-01 2010-01-01 10000>, <ProductPlan: Meat Producer Steer 2010-01-01 2010-01-01 20000>]')
        self.assertEqual(unicode(r.context[-1]['producer']), u'Meat Producer')
    #def test_inventoryselection_126712783645(self):
        r = c.get('/inventoryselection/', {})
        self.assertEqual(r.status_code, 200)
    #def test_jsonproducer3_126712784382(self):
        r = c.get('/jsonproducer/3/', {})
        self.assertEqual(r.status_code, 200)
    #def test_inventoryselection_126712784532(self):
        r = c.post('/inventoryselection/', {'avail_date': '2010-02-22', 'producer': '3', })
    #def test_inventoryupdate32010222_126712784541(self):
        r = c.get('/inventoryupdate/3/2010/2/22/', {})
        self.assertEqual(r.status_code, 200)
    #def test_inventoryupdate32010222_126712786991(self):
        r = c.post('/inventoryupdate/3/2010/2/22/', {'Beets-notes': 'Baby beets', 'Beets-custodian': '', 'Carrots-notes': 'Giant carrots', 'Carrots-item_id': '', 'Beets-inventory_date': '2010-02-22', 'Beets-received': '0', 'Carrots-received': '0', 'Carrots-planned': '200', 'Beets-planned': '100', 'Beets-item_id': '', 'Beets-prodname': 'Beets', 'Carrots-custodian': '', 'Carrots-prodname': 'Carrots', 'Carrots-inventory_date': '2010-02-22', 'producer-id': '3', 'avail-date': '2010-02-22', })
    #def test_produceravail32010222_126712786997(self):
        r = c.get('/produceravail/3/2010/2/22/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['producer']), u'Vegetable Producer')
        self.assertEqual(unicode(r.context[-1]['avail_date']), u'2010-02-22')
        self.assertEqual(unicode(r.context[-1]['inventory']), u'[<InventoryItem: Vegetable Producer Beets 2010-02-22>, <InventoryItem: Vegetable Producer Carrots 2010-02-22>]')
    #def test_processselection_126712787351(self):
        r = c.get('/processselection/', {})
        self.assertEqual(r.status_code, 200)
    #def test_processselection_126712788254(self):
        r = c.post('/processselection/', {'process_type': '1', })
    #def test_newprocess1_126712788258(self):
        r = c.get('/newprocess/1/', {})
        self.assertEqual(r.status_code, 200)
    #def test_newprocess1_126712792666(self):
        r = c.post('/newprocess/1/', {'output-TOTAL_FORMS': '2', 'service-1-from_whom': '8', 'service-1-service_type': '2', 'inputcreation-planned': '1000', 'service-0-from_whom': '4', 'service-0-service_type': '1', 'output-1-producer': '2', 'service-0-amount': '200', 'output-INITIAL_FORMS': '0', 'inputcreation-product': '5', 'service-1-amount': '400', 'output-0-product': '7', 'output-1-product': '6', 'output-0-custodian': '8', 'output-1-custodian': '8', 'inputcreation-producer': '2', 'output-0-planned': '400', 'output-0-producer': '2', 'service-TOTAL_FORMS': '2', 'output-1-planned': '200', 'service-INITIAL_FORMS': '0', })
    #def test_process5_12671279270(self):
        r = c.get('/process/5/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['process']), u'Slaughter and Cut Beef D2 Meat Producer Steer per lb 2010-02-22')
    #def test_orderselection_126712793065(self):
        r = c.get('/orderselection/', {})
        self.assertEqual(r.status_code, 200)
    #def test_jsoncustomer7_126712793828(self):
        r = c.get('/jsoncustomer/7/', {})
        self.assertEqual(r.status_code, 200)
    #def test_orderselection_126712794182(self):
        r = c.post('/orderselection/', {'customer': '7', 'order_date': '2010-02-22', })
    #def test_orderbylot72010222_12671279419(self):
        r = c.get('/orderbylot/7/2010/2/22/', {})
        self.assertEqual(r.status_code, 200)
    #def test_orderbylot72010222_126712796863(self):
        r = c.post('/orderbylot/7/2010/2/22/', {'form-0-product_id': '7', 'form-2-notes': '', 'form-1-lot_id': '19', 'form-0-order_item_id': '', 'form-2-avail': '100', 'form-0-quantity': '200', 'form-3-unit_price': '10', 'form-1-unit_price': '10', 'distributor': '5', 'form-2-order_item_id': '', 'form-1-product_id': '6', 'form-3-lot_id': '16', 'transportation_fee': '40', 'form-3-notes': '', 'form-0-notes': '', 'form-3-order_item_id': '', 'form-3-quantity': '100', 'form-2-lot_id': '15', 'paid': 'on', 'form-TOTAL_FORMS': '4', 'form-2-unit_price': '15', 'form-2-product_id': '10', 'form-INITIAL_FORMS': '4', 'form-0-lot_id': '18', 'form-0-unit_price': '8', 'form-1-quantity': '100', 'form-0-avail': '400', 'form-3-product_id': '8', 'form-3-avail': '200', 'form-1-order_item_id': '', 'form-1-notes': '', 'form-2-quantity': '50', 'form-1-avail': '200', })
    #def test_order3_126712796884(self):
        r = c.get('/order/3/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['order']), u'2010-02-22 Demo Hospital')
    #def test_ordertableselection_126712797388(self):
        r = c.get('/ordertableselection/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['dsform']), u'<tr><th><label for="id_selected_date">Selected date:</label></th><td><input name="selected_date" value="2010-02-22" type="text" id="id_selected_date" dojoType="dijit.form.DateTextBox" constraints="{datePattern:&#39;yyyy-MM-dd&#39;}" /></td></tr>')
    #def test_ordertableselection_126712797742(self):
        r = c.post('/ordertableselection/', {'selected_date': '2010-02-22', })
    #def test_ordertable2010222_126712797748(self):
        r = c.get('/ordertable/2010/2/22/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['date']), u'2010-02-22')
        self.assertEqual(unicode(r.context[-1]['item_list']), u'[<OrderItem: 2010-02-22 Demo Hospital Beef Roast 200>, <OrderItem: 2010-02-22 Demo Hospital Beef Steak 100>, <OrderItem: 2010-02-22 Demo Hospital Beets 50>, <OrderItem: 2010-02-22 Demo Hospital Carrots 100>]')
        self.assertEqual(unicode(r.context[-1]['heading_list']), u"['Customer', 'Order', 'Lot', 'Custodian', 'Order Qty']")
        self.assertEqual(unicode(r.context[-1]['datestring']), u'2010_02_22')
        self.assertEqual(unicode(r.context[-1]['orders']), u'[<Order: 2010-02-22 Demo Hospital>]')
    #def test_invoiceselection_126712798084(self):
        r = c.get('/invoiceselection/', {})
        self.assertEqual(r.status_code, 200)
    #def test_invoiceselection_126712798373(self):
        r = c.post('/invoiceselection/', {'customer': '0', 'order_date': '2010-02-22', })
    #def test_invoices02010222_126712798377(self):
        r = c.get('/invoices/0/2010/2/22/', {})
        self.assertEqual(r.status_code, 200)
    #def test_producerpaymentselection_126712798822(self):
        r = c.get('/producerpaymentselection/', {})
        self.assertEqual(r.status_code, 200)
    #def test_producerpaymentselection_126712799176(self):
        r = c.post('/producerpaymentselection/', {'from_date': '2010-02-15', 'paid_producer': 'both', 'to_date': '2010-02-27', 'producer': '0', })
    #def test_producerpayments02010_02_152010_02_270both_126712799181(self):
        r = c.get('/producerpayments/0/2010_02_15/2010_02_27/0/both/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['producers']), u'[<Party: Local Distributor>, <Party: Meat Processor>, <Party: Meat Producer>, <Party: Slicer and Dicer>, <Party: Vegetable Producer>]')
        self.assertEqual(unicode(r.context[-1]['from_date']), u'2010-02-15')
        self.assertEqual(unicode(r.context[-1]['to_date']), u'2010-02-27')
        self.assertEqual(unicode(r.context[-1]['show_payments']), u'True')
    #def test_producerpaymentselection_126712799697(self):
        r = c.get('/producerpaymentselection/', {})
        self.assertEqual(r.status_code, 200)
    #def test_producerpaymentselection_126712800418(self):
        r = c.post('/producerpaymentselection/', {'from_date': '2010-02-15', 'paid_producer': 'both', 'to_date': '2010-02-27', 'producer': '4', })
    #def test_producerpayments42010_02_152010_02_270both_126712800423(self):
        r = c.get('/producerpayments/4/2010_02_15/2010_02_27/0/both/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['from_date']), u'2010-02-15')
        self.assertEqual(unicode(r.context[-1]['to_date']), u'2010-02-27')
        self.assertEqual(unicode(r.context[-1]['producer']), u'Meat Processor')
        self.assertEqual(unicode(r.context[-1]['show_payments']), u'True')
    #def test_paymentupdateselection_126712800723(self):
        r = c.get('/paymentupdateselection/', {})
        self.assertEqual(r.status_code, 200)
    #def test_jsonpayments4_126712801261(self):
        r = c.get('/jsonpayments/4/', {})
        self.assertEqual(r.status_code, 200)
    #def test_jsonpayments5_126712801747(self):
        r = c.get('/jsonpayments/5/', {})
        self.assertEqual(r.status_code, 200)
    #def test_paymentupdateselection_126712801929(self):
        r = c.post('/paymentupdateselection/', {'payment': '', 'producer': '5', })
    #def test_paymentupdate50_126712801934(self):
        r = c.get('/paymentupdate/5/0/', {})
        self.assertEqual(r.status_code, 200)
    #def test_paymentupdate50_12671280256(self):
        r = c.post('/paymentupdate/5/0/', {'transport8-order': '2010-01-11 Demo Hospital', 'transport8-paid': 'on', 'to_whom': '5', 'reference': 'Check 1111', 'transport8-transaction_type': 'Transportation', 'transport33-order': '2010-02-22 Demo Hospital', 'transport33-paid': 'on', 'transport8-notes': '', 'transport33-notes': '', 'transport33-amount_due': '40', 'transport8-transaction_date': '2010-01-11', 'transport8-transaction_id': '8', 'amount': '80', 'transaction_date': '2010-02-25', 'transport33-quantity': '', 'transport33-transaction_date': '2010-02-22', 'transport33-transaction_id': '33', 'transport8-amount_due': '40', 'transport33-transaction_type': 'Transportation', 'transport8-quantity': '', })
    #def test_payment38_126712802573(self):
        r = c.get('/payment/38/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['payment']), u'2010-02-25 Local Distributor $80')
    #def test_paymentupdateselection_126712802941(self):
        r = c.get('/paymentupdateselection/', {})
        self.assertEqual(r.status_code, 200)
    #def test_jsonpayments4_126712803456(self):
        r = c.get('/jsonpayments/4/', {})
        self.assertEqual(r.status_code, 200)
    #def test_paymentupdateselection_126712803656(self):
        r = c.post('/paymentupdateselection/', {'payment': '', 'producer': '4', })
    #def test_paymentupdate40_126712803661(self):
        r = c.get('/paymentupdate/4/0/', {})
        self.assertEqual(r.status_code, 200)
    #def test_paymentupdate40_126712804339(self):
        r = c.post('/paymentupdate/4/0/', {'proc19-amount_due': '200', 'proc19-paid': 'on', 'proc19-transaction_date': '2010-01-18', 'reference': 'Check 2222', 'proc13-order': '', 'proc13-transaction_type': 'Processing', 'proc2-transaction_date': '2010-01-11', 'proc19-order': ' #2:Demo Hospital', 'proc2-transaction_type': 'Processing', 'proc13-paid': 'on', 'proc5-transaction_id': '5', 'proc5-quantity': '', 'proc13-quantity': '', 'proc13-transaction_id': '13', 'proc19-transaction_id': '19', 'proc2-paid': 'on', 'transaction_date': '2010-02-25', 'proc2-transaction_id': '2', 'proc19-notes': '', 'proc5-order': ' #1:Demo Hospital', 'proc13-notes': '', 'proc2-order': '', 'proc19-quantity': '', 'to_whom': '4', 'proc19-transaction_type': 'Processing', 'proc5-notes': '', 'proc13-transaction_date': '2010-01-11', 'proc5-amount_due': '100', 'proc5-paid': 'on', 'proc2-quantity': '', 'proc5-transaction_type': 'Processing', 'proc5-transaction_date': '2010-01-11', 'amount': '400', 'proc13-amount_due': '50', 'proc2-amount_due': '50', 'proc2-notes': '', })
    #def test_payment39_126712804359(self):
        r = c.get('/payment/39/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['payment']), u'2010-02-25 Meat Processor $400')
    #def test_paymentupdateselection_126712804706(self):
        r = c.get('/paymentupdateselection/', {})
        self.assertEqual(r.status_code, 200)
    #def test_jsonpayments2_126712805145(self):
        r = c.get('/jsonpayments/2/', {})
        self.assertEqual(r.status_code, 200)
    #def test_paymentupdateselection_126712805304(self):
        r = c.post('/paymentupdateselection/', {'payment': '', 'producer': '2', })
    #def test_paymentupdate20_126712805322(self):
        r = c.get('/paymentupdate/2/0/', {})
        self.assertEqual(r.status_code, 200)
    #def test_paymentupdate20_126712806129(self):
        r = c.post('/paymentupdate/2/0/', {'12-amount_due': '4700.00', '18-transaction_id': '18', 'reference': 'Check 3333', '1-transaction_date': '2010-01-11', '18-quantity': '1000', '18-amount_due': '4700.00', '1-quantity': '1000', '18-order': 'None', '12-paid': 'on', '12-notes': '', '12-transaction_type': 'Issue', '1-paid': 'on', '18-notes': '', '1-transaction_id': '1', '12-order': 'None', '1-amount_due': '4700.00', '1-notes': '', 'transaction_date': '2010-02-25', '18-paid': 'on', '12-transaction_id': '12', 'to_whom': '2', '18-transaction_type': 'Issue', '1-transaction_type': 'Issue', '1-order': 'None', 'amount': '14100', '18-transaction_date': '2010-01-18', '12-transaction_date': '2010-01-11', '12-quantity': '1000', })
    #def test_payment40_126712806152(self):
        r = c.get('/payment/40/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['payment']), u'2010-02-25 Meat Producer $14100')
    #def test_statementselection_126712806555(self):
        r = c.get('/statementselection/', {})
        self.assertEqual(r.status_code, 200)
    #def test_statementselection_126712807559(self):
        r = c.post('/statementselection/', {'from_date': '2010-02-18', 'to_date': '2010-02-26', })
    #def test_statements2010_02_182010_02_26_126712807564(self):
        r = c.get('/statements/2010_02_18/2010_02_26/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['payments']), u'[<Payment: 2010-02-25 Local Distributor $80>, <Payment: 2010-02-25 Meat Processor $400>, <Payment: 2010-02-25 Meat Producer $14100>]')
        self.assertEqual(unicode(r.context[-1]['network']), u'Demo')

