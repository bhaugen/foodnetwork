from django import forms
from django.http import Http404
from django.db.models.query import QuerySet
from django.forms.formsets import formset_factory

import datetime
import itertools

from models import *


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
            
    def clean_member_id(self):
        member_id = self.cleaned_data["member_id"]
        if member_id:
            dups = Party.objects.filter(member_id=member_id)
            if dups.count():
                if not dups[0].pk == self.instance.pk:
                    raise forms.ValidationError("Someone already has that member id")
            dups = Customer.objects.filter(member_id=member_id)
            if dups.count():
                if not dups[0].pk == self.instance.pk:
                    raise forms.ValidationError("Someone already has that member id")
        return member_id


class DistributorForm(forms.ModelForm):
    class Meta:
        model = Distributor
           
    def clean_member_id(self):
        member_id = self.cleaned_data["member_id"]
        if member_id:
            dups = Party.objects.filter(member_id=member_id)
            if dups.count():
                if not dups[0].pk == self.instance.pk:
                    raise forms.ValidationError("Someone already has that member id")
            dups = Customer.objects.filter(member_id=member_id)
            if dups.count():
                raise forms.ValidationError("Someone already has that member id")
        return member_id


class ProcessorForm(forms.ModelForm):
    class Meta:
        model = Processor
           
    def clean_member_id(self):
        member_id = self.cleaned_data["member_id"]
        if member_id:
            dups = Party.objects.filter(member_id=member_id)
            if dups.count():
                if not dups[0].pk == self.instance.pk:
                    raise forms.ValidationError("Someone already has that member id")
            dups = Customer.objects.filter(member_id=member_id)
            if dups.count():
                raise forms.ValidationError("Someone already has that member id")
        return member_id
    

class ProducerForm(forms.ModelForm):
    class Meta:
        model = Producer
           
    def clean_member_id(self):
        member_id = self.cleaned_data["member_id"]
        if member_id:
            dups = Party.objects.filter(member_id=member_id)
            if dups.count():
                if not dups[0].pk == self.instance.pk:
                    raise forms.ValidationError("Someone already has that member id")
            dups = Customer.objects.filter(member_id=member_id)
            if dups.count():
                raise forms.ValidationError("Someone already has that member id")
        return member_id


class CurrentWeekForm(forms.Form):
    current_week = forms.DateField(widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}" }))


class PaymentUpdateSelectionForm(forms.Form):
    producer = forms.ChoiceField(required=False)
    payment = forms.ChoiceField(required=False)
    def __init__(self, *args, **kwargs):
        super(PaymentUpdateSelectionForm, self).__init__(*args, **kwargs)
        self.fields['producer'].choices = [('', '----------')] + [(prod.id, prod.short_name) for prod in Party.subclass_objects.payable_members()]
        self.fields['payment'].choices = [('', 'New')] + [(payment.id, payment) for payment in EconomicEvent.objects.payments_to_members()]


class CustomerPaymentSelectionForm(forms.Form):
    customer = forms.ChoiceField(required=False)
    payment = forms.ChoiceField(required=False)
    def __init__(self, *args, **kwargs):
        super(CustomerPaymentSelectionForm, self).__init__(*args, **kwargs)
        self.fields['customer'].choices = [('', '----------')] + [(cust.id, cust.short_name) for cust in Customer.objects.all()]
        self.fields['payment'].choices = [('', 'New')] + [
            (payment.id, payment) for payment in CustomerPayment.objects.all()]


class PaymentTransactionForm(forms.Form):
    transaction_id = forms.CharField(widget=forms.HiddenInput)
    transaction_type=forms.CharField(widget=forms.HiddenInput)
    #order=forms.CharField(required=False, widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input'}))
    #product=forms.CharField(widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input'}))
    transaction_date=forms.CharField(widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input', 'size': '8'}))
    quantity=forms.DecimalField(required=False, widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input', 'size': '8'}))
    amount_due=forms.DecimalField(widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input', 'size': '8'}))
    notes = forms.CharField(required=False, widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input', 'size': '32', 'value': ''}))
    paid=forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'paid',}))


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        exclude = ('from_whom', 'notes')


class CustomerPaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        exclude = ('from_whom', 'to_whom', 'notes')


class CustomerPaymentTransactionForm(forms.Form):
    order_id = forms.CharField(widget=forms.HiddenInput)
    amount_due=forms.DecimalField(widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input', 'size': '8'}))
    paid=forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'paid',}))


def create_customer_payment_transaction_form(order, pay_all, data=None):
    if pay_all:
        paid = True
    else:
        paid = not not order.is_paid()
    the_form = CustomerPaymentTransactionForm(data, prefix=order.id, initial={
        'order_id': order.id,
        'amount_due': order.grand_total(),
        'paid': paid,
        })
    the_form.order = order
    the_form.delivery_date = order.delivery_date
    return the_form

def create_customer_payment_transaction_forms(customer=None, payment=None, data=None):
    form_list = []
    if not customer:
        if payment:
            customer = payment.from_whom
        else:
            return form_list
    pay_all = True
    if payment:
        pay_all = False

        for order in payment.orders_paid():
            form_list.append(create_customer_payment_transaction_form(order, pay_all, data))

    for order in Order.objects.filter(customer=customer):
        if not order.is_paid():
            form_list.append(create_customer_payment_transaction_form(order, pay_all, data))

    return form_list


def create_payment_transaction_form(inventory_transaction, pay_all, data=None):
    order = 'None'
    if inventory_transaction.order_item:
        order = ': '.join([str(inventory_transaction.order_item.order.id), inventory_transaction.order_item.order.customer.short_name])
    if pay_all:
        paid = True
    else:
        paid = not not inventory_transaction.is_paid()
    the_form = PaymentTransactionForm(data, prefix=inventory_transaction.id, initial={
        'transaction_id': inventory_transaction.id,
        'transaction_type': inventory_transaction.transaction_type,
        #'order': order,
        #'product': inventory_transaction.inventory_item.product.long_name, 
        'transaction_date': inventory_transaction.transaction_date,
        'quantity': inventory_transaction.amount,
        'amount_due': inventory_transaction.due_to_member(),
        'notes': inventory_transaction.notes,
        'paid': paid,
        })
    the_form.display_type = inventory_transaction.transaction_type
    the_form.order = order
    the_form.product = inventory_transaction.inventory_item.product.long_name
    return the_form

# todo: replace with ServiceTransactions
def create_processing_payment_form(service_transaction, pay_all, data=None):
   
    order = service_transaction.order_string()

    if pay_all:
        paid = True
    else:
        paid = not not service_transaction.is_paid()
    prefix = "".join(["proc", str(service_transaction.id)])
    the_form = PaymentTransactionForm(data, prefix=prefix, initial={
        'transaction_id': service_transaction.id,
        'transaction_type': 'Service',
        #'order': order,
        'transaction_date': service_transaction.transaction_date,
        'quantity': "",
        # todo: what shd this be?
        #'quantity': inventory_transaction.quantity,
        'amount_due': service_transaction.amount,
        'notes': service_transaction.notes,
        'paid': paid,
        })
    the_form.display_type = service_transaction.service_type
    the_form.order = order
    the_form.product = service_transaction.product_string()
    return the_form

# todo: replace with ServiceTransactions
def create_transportation_payment_form(transportation_tx, pay_all, data=None):

    if pay_all:
        paid = True
    else:
        paid = not not transportation_tx.is_paid()
    prefix = "".join(["transport", str(transportation_tx.id)])
    the_form = PaymentTransactionForm(data, prefix=prefix, initial={
        'transaction_id': transportation_tx.id,
        'transaction_type': 'Transportation',
        #'order': transportation_tx.order,
        'transaction_date': transportation_tx.transaction_date,
        'quantity': "",
        'amount_due': transportation_tx.amount,
        'notes': "",
        'paid': paid,
        })
    the_form.display_type = transportation_tx.service_type.name
    the_form.order = transportation_tx.order
    the_form.product = ""
    return the_form


def create_payment_transaction_forms(producer=None, payment=None, data=None):
    form_list = []
    if not producer:
        if payment:
            producer = payment.paid_to
        else:
            return form_list
    pay_all = True
    if payment:
        pay_all = False

        for p in payment.paid_inventory_transactions():
            form_list.append(create_payment_transaction_form(p, pay_all, data))

        for p in payment.paid_service_transactions():
            form_list.append(create_processing_payment_form(p, pay_all, data))

        for p in payment.paid_transportation_transactions():
            form_list.append(create_transportation_payment_form(p, pay_all, data))

    for d in InventoryTransaction.objects.filter(inventory_item__producer=producer):
        if d.should_be_paid():
            form_list.append(create_payment_transaction_form(d, pay_all, data))

    due3 = ServiceTransaction.objects.filter(
        from_whom=producer)
    for d in due3:
        if d.should_be_paid():
            form_list.append(create_processing_payment_form(d, pay_all, data))

    due4 = TransportationTransaction.objects.filter(from_whom=producer)
    for d in due4:
        if d.should_be_paid():
            form_list.append(create_transportation_payment_form(d, pay_all, data))
    return form_list

class InventoryHeaderForm(forms.Form):
    producer = forms.ChoiceField()
    avail_date = forms.DateField()
    def __init__(self, *args, **kwargs):
        super(InventoryHeaderForm, self).__init__(*args, **kwargs)
        self.fields['producer'].choices = [('', '----------')] + [(prod.id, prod.short_name) for prod in Party.objects.all().exclude(pk=1)]

class InventorySelectionForm(forms.Form):
    producer = forms.ChoiceField()
    avail_date = forms.DateField(
        widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))
    def __init__(self, *args, **kwargs):
        super(InventorySelectionForm, self).__init__(*args, **kwargs)
        self.fields['producer'].choices = [('', '----------')] + [(prod.id, prod.short_name) for prod in Party.subclass_objects.planned_producers()]

class DateSelectionForm(forms.Form):
    selected_date = forms.DateField(
        widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))


class DeliverySelectionForm(forms.Form):
    delivery_date = forms.DateField(
        widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))
    customer = forms.ChoiceField()
    def __init__(self, *args, **kwargs):
        super(DeliverySelectionForm, self).__init__(*args, **kwargs)
        self.fields['customer'].choices = [('0', 'All')] + [(cust.id, cust.short_name) for cust in Customer.objects.all()]

class PaymentSelectionForm(forms.Form):
    producer = forms.ChoiceField()
    from_date = forms.DateField(
        widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))
    to_date = forms.DateField(
        widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))
    due = forms.BooleanField(required=False)
    paid_member = forms.ChoiceField(choices=[
                                               ('both', 'Paid and Unpaid'),
                                               ('paid', 'Paid only'), 
                                               ('unpaid', 'Unpaid only'),
                                               ])
    def __init__(self, *args, **kwargs):
        super(PaymentSelectionForm, self).__init__(*args, **kwargs)
        self.fields['producer'].choices = [('0', 'All')] + [(prod.id, prod.short_name) for prod in Party.subclass_objects.payable_members()]
        

class StatementSelectionForm(forms.Form):
    from_date = forms.DateField(
        widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))
    to_date = forms.DateField(
        widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))
        

class DateRangeSelectionForm(forms.Form):
    from_date = forms.DateField(
        widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))
    to_date = forms.DateField(
        widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))


class PlanSelectionForm(forms.Form):
    member = forms.ChoiceField()
    plan_from_date = forms.DateField(
        widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))
    plan_to_date = forms.DateField(
        widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))
    list_type = forms.ChoiceField( widget=forms.RadioSelect(), choices=[
        ['M','Member Product List'],['A','All Products']] )

    def __init__(self, *args, **kwargs):
        super(PlanSelectionForm, self).__init__(*args, **kwargs)
        self.fields['member'].choices = [('', '----------')] + [
            (p.id, p.short_name) for p in Party.subclass_objects.all_planners()]

        
class PlanForm(forms.ModelForm):
    #parents = forms.CharField(required=False, widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input', 'size': '12'}))
    prodname = forms.CharField(widget=forms.HiddenInput)
    from_date = forms.DateField(widget=forms.TextInput(attrs={'size': '10'}))
    to_date = forms.DateField(widget=forms.TextInput(attrs={'size': '10'}))
    quantity = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'quantity-field', 'size': '10'}))
    item_id = forms.CharField(required=False, widget=forms.HiddenInput)
    inventoried = forms.BooleanField(required=False)

    class Meta:
        model = ProductPlan
        exclude = ('member', 'product', 'role')
        
    def __init__(self, member, *args, **kwargs):
        super(PlanForm, self).__init__(*args, **kwargs)
        sublist = list(Distributor.objects.all())
        sublist.append(member)
        #sublist.sort(lambda x, y: cmp(y.__class__, x.__class__))
        self.fields['distributor'].choices = [(party.id, party.short_name) for party in sublist]


class PlanRowForm(forms.Form):
    product_id = forms.CharField(widget=forms.HiddenInput)


class PlanCellForm(forms.Form):
    plan_id = forms.CharField(required=False, widget=forms.HiddenInput)
    product_id = forms.CharField(widget=forms.HiddenInput)
    from_date = forms.DateField(widget=forms.HiddenInput)
    to_date = forms.DateField(widget=forms.HiddenInput)
    quantity = forms.DecimalField(required=False, widget=forms.TextInput(attrs={
        'class': 'quantity-field', 'style':'width:45px'}))

        
def create_plan_forms(member, data=None):
    items = ProductPlan.objects.filter(member=member)
    item_dict = {}
    # todo: must allow for multiple ProductPlans per product
    for item in items:
        item_dict[item.product.id] = item
    #if member.is_customer():
    #    prods = list(Product.objects.filter(sellable=True))
    #else:
    #    prods = list(Product.objects.filter(plannable=True))
    prods = list(Product.objects.filter(plannable=True))
    for prod in prods:
        prod.parents = prod.parent_string()
    prods.sort(lambda x, y: cmp(x.parents, y.parents))
    form_list = []
    for prod in prods:
        try:
            item = item_dict[prod.id]
        except KeyError:
            item = False
        if item:
            this_form = PlanForm(member=member, data=data, prefix=prod.short_name, initial={
                'item_id': item.id,
                #'parents': prod.parents, 
                'prodname': prod.short_name,
                'from_date': item.from_date,
                'to_date': item.to_date,
                'quantity': item.quantity,
                'distributor': item.distributor.id,
                'inventoried': item.inventoried})
        else:
            this_form = PlanForm(member=member, data=data, prefix=prod.short_name, initial={
                #'parents': prod.parents, 
                'prodname': prod.short_name, 
                'from_date': datetime.date.today(),
                'to_date': datetime.date.today()  + datetime.timedelta(days=365),
                'quantity': 0})
        this_form.long_name = prod.long_name
        this_form.parents = prod.parents
        form_list.append(this_form)
    return form_list 

class InventoryItemForm(forms.ModelForm):
    prod_id = forms.CharField(widget=forms.HiddenInput)
    freeform_lot_id = forms.CharField(required=False,
                                      widget=forms.TextInput(attrs={'size': '16', 'value': ''}))
    field_id = forms.CharField(required=False,
                               widget=forms.TextInput(attrs={'size': '5', 'value': ''}))
    inventory_date = forms.DateField(widget=forms.TextInput(attrs={'size': '10'}))
    planned = forms.DecimalField(widget=forms.TextInput(attrs={'class':
                                                               'quantity-field',
                                                               'size': '6'}))
    received = forms.DecimalField(widget=forms.TextInput(attrs={'class':
                                                                'quantity-field',
                                                                'size': '6'}))
    notes = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': '32', 'value': ''}))
    item_id = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = InventoryItem
        exclude = ('producer', 'product', 'onhand', 'remaining', 'expiration_date')
        
    def __init__(self, *args, **kwargs):
        super(InventoryItemForm, self).__init__(*args, **kwargs)
        self.fields['custodian'].choices = [('', '------------')] + [(prod.id, prod.short_name) for prod in Party.subclass_objects.possible_custodians()]


def create_inventory_item_forms(producer, avail_date, plans, items, data=None):
    item_dict = {}
    for item in items:
        item_dict[item.product.id] = item
    form_list = []
    for plan in plans:
        custodian_id = ""
        try:
            item = item_dict[plan.product.id]
            if item.custodian:
                custodian_id = item.custodian.id
        except KeyError:
            item = False
        #import pdb; pdb.set_trace()
        if item:
            the_form = InventoryItemForm(data, prefix=item.product.id, initial={
                'item_id': item.id,
                'prod_id': item.product.id,
                'freeform_lot_id': item.freeform_lot_id,
                'field_id': item.field_id,
                'custodian': custodian_id,
                'inventory_date': item.inventory_date,
                'planned': item.planned,
                'received': item.received,
                'notes': item.notes})
        else:
            the_form = InventoryItemForm(data, prefix=plan.product.id, initial={
                'prod_id': plan.product.id, 
                'inventory_date': avail_date,
                'planned': 0,
                'received': 0,
                'notes': ''})
        the_form.description = plan.product.long_name
        try:
            the_form.plan_qty = plan.quantity
        except:
            the_form.plan_qty = 0
        form_list.append(the_form) 
    return form_list 


class MeatItemForm(forms.ModelForm):
    inventory_date = forms.DateField(widget=forms.TextInput(attrs={'size': '8'}))
    planned = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'quantity-field', 'size': '6'}))
    received = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'quantity-field', 'size': '6'}))
    notes = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': '32', 'value': ''}))
    processor = forms.ChoiceField(required=False)
    cost = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'quantity-field', 'size': '6'}))
    #prod_id = forms.CharField(widget=forms.HiddenInput)
    item_id = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = InventoryItem
        exclude = ('producer', 'onhand', 'remaining', 'expiration_date')
        
    def __init__(self, *args, **kwargs):
        super(MeatItemForm, self).__init__(*args, **kwargs)
        #self.fields['product'].choices = [(prod.id, prod.long_name) for prod in product_list]
        self.fields['custodian'].choices = [('', '------------')] + [(proc.id, proc.long_name) for proc in Party.objects.all().exclude(pk=1)]
        self.fields['processor'].choices = [('', '------------')] + [(proc.id, proc.long_name) for proc in Processor.objects.all()]


class ProductShortForm(forms.Form):
    total_ordered = forms.DecimalField(widget=forms.TextInput
        (attrs={'readonly':'true', 'class': 'read-only-input', 'size': '6', 'style': 'text-align: right;'}))
    quantity_short = forms.DecimalField(widget=forms.TextInput
        (attrs={'readonly':'true', 'class': 'read-only-input short', 'size': '6', 'style': 'text-align: right;'}))


class OrderItemShortForm(forms.ModelForm):
    item_id = forms.CharField(required=False, widget=forms.HiddenInput)
    quantity = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'quantity-field order-qty', 'size': '8'}))
    
    class Meta:
        model = OrderItem
        fields = ('quantity', )

class ShortsRow(object):
    def __init__(self, product, total_avail, product_form, cells, item_forms):
         self.product = product
         self.total_avail = total_avail
         self.product_form = product_form
         self.cells = cells
         self.item_forms = item_forms


class ShortsTable(object):
    def __init__(self, columns, rows):
         self.columns = columns
         self.rows = rows


def create_shorts_table(delivery_date, data=None):
    shorts_list = shorts_for_date(delivery_date)
    orders = []
    for short in shorts_list:
        for oi in short.order_items:
            orders.append(oi.order)
    orders = list(set(orders))
    cols = ["Product", "Avail", "Ordered", "Short"]
    #cols.extend(orders)
    for order in orders:
        cols.append(order.customer)
    rows = []
    for short in shorts_list:
        product_init = {
            "total_ordered": short.total_ordered,
            "quantity_short": short.quantity_short,
        }
        product_form = ProductShortForm(data, prefix=str(short.product.id), initial=product_init)
        row = ShortsRow(short.product, short.total_avail, product_form, [], [])
        cells = []
        for order in orders:
            cells.append("")
        for oi in short.order_items:
            cell = orders.index(oi.order)
            cell_init = {
                "item_id": oi.id,
                "quantity": oi.quantity,
            }
            pref = "-".join([str(short.product.id), str(oi.id)])
            item_form = OrderItemShortForm(data, prefix=pref, initial=cell_init)
            cells[cell] = item_form
            row.item_forms.append(item_form)
        row.cells.extend(cells)
        rows.append(row)
    return ShortsTable(cols, rows)

def create_short_forms(delivery_date):
    shorts_list = shorts_for_date(delivery_date)
    orders = []
    for short in shorts_list:
        for oi in short.order_items:
            orders.append(oi.order)
    orders = list(set(orders))
    cols = ["Product", "Avail", "Ordered", "Short"]
    cols.extend(orders)
    rows = []
    for short in shorts_list:
        row = [short.product, short.total_avail, short.total_ordered, short.quantity_short]
        for order in orders:
            row.append("")
        for oi in short.order_items:
            row_cell = orders.index(oi.order) + 4
            row[row_cell] = oi.quantity
        rows.append(row)
    return ShortsTable(cols, rows)
    

class OrderByLotForm(forms.ModelForm):
    order_item_id = forms.CharField(required=False, widget=forms.HiddenInput)
    lot_id = forms.CharField(widget=forms.HiddenInput)
    product_id = forms.CharField(widget=forms.HiddenInput)
    #lot_qty = forms.DecimalField(widget=forms.TextInput
    #    (attrs={'readonly':'true', 'class': 'read-only-input', 'size': '8', 'style': 'text-align: right;'}))
    lot_label = forms.CharField(required=False, widget=forms.TextInput
        (attrs={'readonly':'true', 'class': 'read-only-input', 'size': '80'}))
    avail = forms.DecimalField(widget=forms.TextInput
        (attrs={'readonly':'true', 'class': 'read-only-input', 'size': '6', 'style': 'text-align: right;'}))
    #ordered = forms.DecimalField(widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input total-ordered', 'size': '6', 'style': 'text-align: right;'}))
    quantity = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'quantity-field', 'size': '8'}))
    unit_price = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'unit-price-field', 'size': '8'}))
    
    class Meta:
        model = OrderItem
        exclude = ('order', 'product', 'fee')
        
    #def __init__(self, *args, **kwargs):
    #    super(OrderItemByLotForm, self).__init__(*args, **kwargs)


class DeliveryItemForm(forms.Form):
    #description = forms.CharField(widget=forms.TextInput
    #    (attrs={'readonly':'true', 'class': 'read-only-input', 'size': '24'}))
    order_qty = forms.DecimalField(widget=forms.TextInput
        (attrs={'readonly':'true', 'class': 'read-only-input', 'size': '8', 'style': 'text-align: right;'}))
    order_item_id = forms.CharField(widget=forms.HiddenInput)
    product_id = forms.CharField(widget=forms.HiddenInput)


class DeliveryForm(forms.ModelForm):
    amount = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'quantity-field', 'size': '8'}))

    class Meta:
        model = InventoryTransaction
        exclude = ('from_whom', 'to_whom', 'process', 'unit_price', 'order_item', 'transaction_type', 'transaction_date', 'notes')

def create_delivery_forms(thisdate, customer, data=None):
    # could this below all be done with inline formsets?
    # (which were not available when this was coded...)
    # might be doable...
    form_list = []
    if customer:
        orderitems = OrderItem.objects.filter(
            order__delivery_date=thisdate, 
            order__customer=customer
        ).exclude(order__state="Unsubmitted")
    else:
        orderitems = OrderItem.objects.filter(
            order__delivery_date=thisdate).exclude(order__state="Unsubmitted")
    for oi in orderitems:
        dtf = DeliveryItemForm(data, prefix=str(oi.id), initial=
            {'order_qty': oi.quantity, 'order_item_id': oi.id, 'product_id': oi.product.id})
        dtf.description = ": ".join([oi.order.customer.short_name, oi.product.long_name])
        # choices hack below was because
        # product.avail_items used to return a chain, not a queryset
        # does not support len(), and does not work for fields[].queryset
        # avail_items now does return a queryset
        # todo: maybe rethink some of this code, altho it does work
        avail_items = oi.product.avail_items(thisdate)
        if avail_items.count() == 1:
            choices = [(item.id, item.delivery_label()) for item in avail_items]
        else:
            choices = [('', '----------')] + [(item.id, item.delivery_label()) for item in avail_items]
        deliveries = oi.inventorytransaction_set.filter(transaction_type='Delivery')
        #import pdb; pdb.set_trace()
        delivery_count = len(deliveries)
        field_set_count = max(len(choices)-1, delivery_count)
        field_set_count = min(field_set_count, 4)
        if delivery_count:
            dtf.delivery_forms = []
            d = 0
            for delivery in deliveries:
                df = DeliveryForm(data, prefix=str(oi.id) + str(d), instance=delivery)
                selected = [(delivery.inventory_item.id, delivery.inventory_item.delivery_label()),]
                df.fields['inventory_item'].choices = selected
                dtf.delivery_forms.append(df)
                d += 1
            if delivery_count < 4:
                extras = [DeliveryForm
                    (data, prefix=str(oi.id) + str(x), 
                     instance=InventoryTransaction()) for x in range(delivery_count, field_set_count)]
                for df in extras:
                    df.fields['inventory_item'].choices = choices
                dtf.delivery_forms.extend(extras)
                field_count = field_set_count * 2
                dtf.empty_fields = ["---" for x in range(field_count, 8)]
            form_list.append(dtf)              
        else:
            # this next stmt is why the first lot in undelivered items has no initial inventory_item
            delform = DeliveryForm(data, prefix=str(oi.id) + '0', initial={'quantity': oi.quantity})
            dtf.delivery_forms = [delform,]
            dtf.delivery_forms.extend(
                [DeliveryForm(data, prefix=str(oi.id) + str(x), instance=InventoryTransaction()) for x in range(1, field_set_count)])
            for df in dtf.delivery_forms:
                df.fields['inventory_item'].choices = choices
            if not field_set_count:
                field_set_count = 1
            field_count = field_set_count * 2
            dtf.empty_fields = ["---" for x in range(field_count, 8)]
            form_list.append(dtf)
    return form_list

class OrderSelectionForm(forms.Form):
    customer = forms.ChoiceField()
    delivery_date = forms.DateField(
        widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))
    def __init__(self, *args, **kwargs):
        super(OrderSelectionForm, self).__init__(*args, **kwargs)
        self.fields['customer'].choices = [('', '----------')] + [(cust.id, cust.short_name) for cust in Customer.objects.all()]


class OrderForm(forms.ModelForm):
    transportation_fee = forms.DecimalField(required=False, widget=forms.TextInput(attrs={'size': '8'}))
    purchase_order = forms.CharField(required=False)

    class Meta:
        model = Order
        exclude = ('customer', 'state', 'paid', 'created_by', 'changed_by')
        
    def __init__(self, order=None, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        #sublist = list(Party.subclass_objects.all().exclude(pk=1))
        #sublist.sort(lambda x, y: cmp(y.__class__, x.__class__))
        self.fields['distributor'].choices = [(party.id, party.short_name) for party in Party.subclass_objects.all_distributors()]
        #import pdb; pdb.set_trace()
        if order:
            try:
                transportation_tx = TransportationTransaction.objects.get(order=order)
                self.initial['transportation_fee'] = transportation_tx.amount
            except TransportationTransaction.DoesNotExist:
                pass


class OrderItemForm(forms.ModelForm):
     #parents = forms.CharField(required=False, widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input', 'size': '12'}))
     prod_id = forms.CharField(widget=forms.HiddenInput)
     #description = forms.CharField(widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input'}))
     #producers = forms.CharField(required=False, widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input', 'size': '12'}))
     avail = forms.DecimalField(widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input', 'size': '6', 'style': 'text-align: right;'}))
     ordered = forms.DecimalField(widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input total-ordered', 'size': '6', 'style': 'text-align: right;'}))
     quantity = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'quantity-field', 'size': '8'}))
     unit_price = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'unit-price-field', 'size': '8'}))
     #fee = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'fee-field', 'size': '5'}))
     notes = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': '32', 'value': ''}))

     class Meta:
         model = OrderItem
         exclude = ('order', 'product', 'fee', 'orig_qty')


def create_order_item_forms(order, availdate, orderdate, data=None):
    form_list = []
    item_dict = {}
    if order:
        items = order.orderitem_set.all()
        for item in items:
            item_dict[item.product.id] = item
    prods = list(Product.objects.filter(sellable=True))
    for prod in prods:
        prod.parents = prod.parent_string()
    prods.sort(lambda x, y: cmp(x.parents, y.parents))
    for prod in prods:
        totavail = prod.total_avail(availdate)
        totordered = prod.total_ordered(orderdate)
        try:
            item = item_dict[prod.id]
        except KeyError:
            item = False
        if item:
            producers = prod.avail_producers(availdate)
            initial_data = {
                'prod_id': prod.id,
                'avail': totavail,
                'unit_price': item.formatted_unit_price(),
                'ordered': totordered,
            }
            oiform = OrderItemForm(data, prefix=prod.id, instance=item,
                                   initial=initial_data)
            oiform.producers = producers
            oiform.description = prod.long_name
            oiform.parents = prod.parents
            oiform.growing_method = prod.growing_method
            form_list.append(oiform)
        else:
            #fee = prod.decide_fee()
            if totavail > 0:
                producers = prod.avail_producers(availdate)
                oiform = OrderItemForm(data, prefix=prod.short_name, initial={
                    'prod_id': prod.id, 
                    'description': prod.long_name, 
                    'avail': totavail, 
                    'ordered': totordered, 
                    'unit_price': prod.unit_price_for_date(availdate), 
                    #'fee': fee,  
                    'quantity': 0})
                oiform.description = prod.long_name
                oiform.producers = producers
                oiform.parents = prod.parents
                oiform.growing_method = prod.growing_method
                form_list.append(oiform)
    return form_list


class EmailForm(forms.Form):
    email_address = forms.EmailField()
    subject = forms.CharField()
    message = forms.CharField(widget = forms.Textarea)


class ProcessSelectionForm(forms.Form):
    #process_date = forms.DateField(
    #    widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))
    process_type = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(ProcessSelectionForm, self).__init__(*args, **kwargs)
        self.fields['process_type'].choices = [('', '----------')] + [(pt.id, pt.name) for pt in ProcessType.objects.all()]


class InputLotSelectionForm(forms.Form):
    lot = forms.ChoiceField()
    quantity = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'quantity-field', 'size': '10'}))

    def __init__(self, input_lots, *args, **kwargs):
        super(InputLotSelectionForm, self).__init__(*args, **kwargs)
        self.fields['lot'].choices = [
            (lot.id, " ".join([lot.producer.short_name, lot.product.short_name, lot.lot_id()])) for lot in input_lots]


class InputLotCreationForm(forms.ModelForm):
    planned = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'quantity-field', 'size': '10'}))
    freeform_lot_id = forms.CharField(required=False,
                                      widget=forms.TextInput(attrs={'size': '16', 'value': ''}))
    field_id = forms.CharField(required=False,
                               widget=forms.TextInput(attrs={'size': '5', 'value': ''}))

    def __init__(self, input_types, *args, **kwargs):
        super(InputLotCreationForm, self).__init__(*args, **kwargs)
        #import pdb; pdb.set_trace()
        self.fields['product'].choices = [(prod.id, prod.long_name) for prod in input_types]
        # todo: shd be producers for input_types
        self.fields['producer'].choices = [('', '----------')] + [(prod.id, prod.short_name) for prod in Party.subclass_objects.planned_producers()]

    class Meta:
        model = InventoryItem
        exclude = ('custodian', 'inventory_date', 'expiration_date', 'remaining', 'received', 'onhand', 'notes')

class InputLotUpdateForm(forms.Form):
    lot_id = forms.ChoiceField()
    quantity = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'quantity-field', 'size': '10'}))


class OutputLotCreationForm(forms.ModelForm):
    planned = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'quantity-field', 'size': '10'}))
    freeform_lot_id = forms.CharField(required=False,
                                      widget=forms.TextInput(attrs={'size': '16', 'value': ''}))
    field_id = forms.CharField(required=False,
                               widget=forms.TextInput(attrs={'size': '5', 'value': ''}))

    def __init__(self, output_types, *args, **kwargs):
        super(OutputLotCreationForm, self).__init__(*args, **kwargs)
        self.fields['product'].choices = [(prod.id, prod.long_name) for prod in output_types]
        # todo: shd be producers for output_types
        self.fields['producer'].choices = [('', '----------')] + [(prod.id, prod.short_name) for prod in Party.subclass_objects.planned_producers()]

    class Meta:
        model = InventoryItem
        exclude = ('inventory_date', 'expiration_date', 'remaining', 'received', 'onhand', 'notes')

class OutputLotCreationFormsetForm(forms.ModelForm):
    planned = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'quantity-field', 'size': '10'}))
    producer = forms.ModelChoiceField(
        queryset=QuerySet(model=Producer),
        widget=forms.Select(attrs={'class': 'output_producer',}))
    freeform_lot_id = forms.CharField(required=False,
                                      widget=forms.TextInput(attrs={'size': '16', 'value': ''}))
    field_id = forms.CharField(required=False,
                               widget=forms.TextInput(attrs={'size': '5', 'value': ''}))

    def __init__(self, *args, **kwargs):
        super(OutputLotCreationFormsetForm, self).__init__(*args, **kwargs)
        # todo: shd be producers for output_types
        self.fields['producer'].choices = [('', '----------')] + [(prod.id, prod.short_name) for prod in Party.subclass_objects.planned_producers()]
        self.fields['custodian'].choices = [('', '----------')] + [(prod.id, prod.short_name) for prod in Party.subclass_objects.possible_custodians()]

    class Meta:
        model = InventoryItem
        exclude = ('inventory_date', 'expiration_date', 'remaining', 'received', 'onhand', 'notes')

class OutputLotUpdateForm(forms.Form):
    lot_id = forms.ChoiceField()
    quantity = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'quantity-field', 'size': '10'}))


class ProcessServiceForm(forms.ModelForm):
    amount = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'quantity-field', 'size': '10'}))
    
    def __init__(self, *args, **kwargs):
        super(ProcessServiceForm, self).__init__(*args, **kwargs)
        self.fields['from_whom'].choices = [('', '----------')] + [(proc.id, proc.short_name) for proc in Processor.objects.all()]

    class Meta:
        model = ServiceTransaction
        exclude = ('process', 'to_whom', 'transaction_date', 'payment', 'notes')


