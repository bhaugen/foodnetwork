from django.forms.formsets import formset_factory

from distribution.models import *

from customer.forms import *

def create_new_product_list_forms(data=None):
    #todo: shd these be plannable instead of sellable?
    products = list(Product.objects.filter(sellable=True))
    #CustomerProductFormSet = formset_factory(CustomerProductForm, extra=0)
    form_list = []
    for prod in products:
        prod.parents = prod.parent_string()
    products.sort(lambda x, y: cmp(x.parents, y.parents))
    for prod in products:
        #if prod.id == 24:
        #    import pdb; pdb.set_trace()
        initial_data = {
                'prod_id': prod.id,
            }
        form = CustomerProductForm(data, prefix=prod.id, 
            initial=initial_data)
        form.product_name = prod.long_name
        form.category = prod.parents
        form_list.append(form)
    return form_list


def create_edit_product_list_forms(customer, data=None):
    return


def create_order_item_forms(order, product_list, availdate, data=None):
    form_list = []
    item_dict = {}
    if order:
        items = order.orderitem_set.all()
        for item in items:
            item_dict[item.product.id] = item
    products = list(Product.objects.filter(sellable=True))
    if product_list:
        listed_products = CustomerProduct.objects.filter(
            product_list=product_list).values_list("product_id")
        listed_products = set(id[0] for id in listed_products)
    prods = []
    for prod in products:
        ok = True
        if product_list:
            if not prod.id in listed_products:
                ok = False
        if ok:
            prod.parents = prod.parent_string()
            prods.append(prod)
    prods.sort(lambda x, y: cmp(x.parents, y.parents))
    for prod in prods:
        #totavail = prod.total_avail(availdate)
        totavail = prod.avail_for_customer(availdate)
        #totordered = prod.total_ordered(orderdate)
        try:
            item = item_dict[prod.id]
        except KeyError:
            item = False
        if item:
            #todo: these fields shd be form initial data 
            # (or can they be? got an instance)
            # cd also use formsets - see d.view_helpers.create_weekly_plan_forms
            # Can't find an example of instance + initial in a ModelForm in my
            # code, but see http://django-reversion.googlecode.com/svn/tags/1.1.2/src/reversion/admin.py
            # ModelForm(request.POST, request.FILES, instance=obj, initial=self.get_revision_form_data(request, obj, version))
            producers = prod.avail_producers(availdate)
            # maybe like this?
            initial_data = {
                'prod_id': prod.id,
                'avail': totavail,
                'unit_price': item.formatted_unit_price(),
                #'ordered': totordered,
            }
            oiform = OrderItemForm(data, prefix=prod.id, instance=item,
                                   initial=initial_data)
            #oiform.fields['prod_id'].widget.attrs['value'] = prod.id
            #oiform.fields['avail'].widget.attrs['value'] = totavail
            #oiform.fields['ordered'].widget.attrs['value'] = totordered
            oiform.producers = producers
            oiform.description = prod.long_name
            oiform.parents = prod.parents
            form_list.append(oiform)
        else:
            if totavail > 0:
                producers = prod.avail_producers(availdate)
                oiform = OrderItemForm(data, prefix=prod.id, initial={
                    'parents': prod.parents, 
                    'prod_id': prod.id, 
                    'description': prod.long_name, 
                    'avail': totavail, 
                    #'ordered': totordered, 
                    'unit_price': prod.formatted_unit_price_for_date(availdate), 
                    'quantity': 0})
                oiform.description = prod.long_name
                oiform.producers = producers
                oiform.parents = prod.parents
                form_list.append(oiform)
    return form_list

class DisplayTable(object):
    def __init__(self, columns, rows):
        self.columns = columns
        self.rows = rows


class HistoryRow(object):
    def __init__(self, product, quantity, extended_price):
        self.product = product
        self.quantity = quantity
        self.extended_price = extended_price

    def average_price(self):
        return self.extended_price / self.quantity


def create_history_table(customer, from_date, to_date):
    items = OrderItem.objects.filter(
        order__customer=customer, 
        order__delivery_date__range=(from_date, to_date),
        order__state__contains="Paid"
    )
    row_dict = {}
    for item in items:
        row_dict.setdefault(item.product, HistoryRow(item.product, Decimal("0"),
                                                     Decimal("0")))
        row = row_dict[item.product]
        row.quantity += item.quantity
        row.extended_price += item.extended_price()
    rows = row_dict.values()
    rows.sort(lambda x, y: cmp(x.product.short_name, y.product.short_name))
    return rows
