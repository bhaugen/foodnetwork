from django import forms
from django.db.models.query import QuerySet

import datetime

from distribution.models import *


class NewOrderSelectionForm(forms.Form):
    order_date = forms.DateField(
        widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))
    product_list = forms.ChoiceField()

    def __init__(self, customer, *args, **kwargs):
        super(NewOrderSelectionForm, self).__init__(*args, **kwargs)
        choices = [(plist.id, plist.list_name) for plist in
                   MemberProductList.objects.filter(member=customer)]
        choices.extend([(0, 'All Available Products')])
        self.fields['product_list'].choices = choices

class OrderForm(forms.ModelForm):
    transportation_fee = forms.DecimalField(required=False, widget=forms.TextInput(attrs={'size': '8'}))

    class Meta:
        model = Order
        exclude = ('customer', 'state', 'paid')
        
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
     avail = forms.DecimalField(widget=forms.TextInput(attrs={
         'readonly':'true', 
         'class': 'read-only-input', 
         'size': '5', 
         'style': 'text-align: right;',
     }))
     #ordered = forms.DecimalField(widget=forms.TextInput(attrs={
     #    'readonly':'true', 
     #    'class': 'read-only-input total-ordered', 
     #    'size': '5', 
     #    'style': 'text-align: right;',
     #}))
     quantity = forms.DecimalField(widget=forms.TextInput(attrs={
         'class': 'quantity-field', 
         'size': '5'
     }))
     unit_price = forms.DecimalField(widget=forms.TextInput(attrs={
         'class': 'read-only-input unit-price-field', 
         'size': '5',
         'style': 'text-align: right;',
     }))
     #fee = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'fee-field', 'size': '5'}))
     notes = forms.CharField(required=False, widget=forms.TextInput(attrs={
         'size': '32', 
         'value': '',
     }))

     class Meta:
         model = OrderItem
         exclude = ('order', 'product', 'fee', 'orig_qty')

class MemberPlanSelectionForm(forms.Form):
    plan_from_date = forms.DateField(
        widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))
    plan_to_date = forms.DateField(
        widget=forms.TextInput(attrs={"dojoType": "dijit.form.DateTextBox", "constraints": "{datePattern:'yyyy-MM-dd'}"}))
    list_type = forms.ChoiceField( widget=forms.RadioSelect(), choices=[
        ['M','My Product List'],['A','All Products']] )


class ProductListForm(forms.ModelForm):

    class Meta:
        model = MemberProductList
        exclude = ('member',)

class CustomerProductForm(forms.ModelForm):
    prod_id = forms.CharField(widget=forms.HiddenInput)
    default_quantity = forms.DecimalField(required=False, widget=forms.TextInput(attrs={
        'class': 'quantity-field', 
        'size': '5',
        'value': 0,
     }))
    added = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'added',}))

    class Meta:
        model = CustomerProduct
        exclude = ('customer', 'product', 'product_list')


class InlineCustomerProductForm(forms.ModelForm):

    class Meta:
        model = CustomerProduct
        exclude = ('customer', 'product_list')




