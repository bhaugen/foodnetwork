from django.forms.formsets import formset_factory
from django.core.urlresolvers import reverse

from distribution.models import *
from distribution.view_helpers import SupplyDemandTable, SuppliableDemandCell
from producer.forms import *


def create_inventory_item_forms(producer, avail_date, data=None):
    monday = avail_date - datetime.timedelta(days=datetime.date.weekday(avail_date))
    saturday = monday + datetime.timedelta(days=5)
    items = InventoryItem.objects.filter(
        producer=producer, 
        remaining__gt=0,
        inventory_date__range=(monday, saturday))
    item_dict = {}
    for item in items:
        item_dict[item.product.id] = item
    plans = ProductPlan.objects.filter(
        member=producer, 
        from_date__lte=avail_date, 
        to_date__gte=saturday)
    form_list = []
    for plan in plans:
        custodian_id = ""
        try:
            item = item_dict[plan.product.id]
            if item.custodian:
                custodian_id = item.custodian.id
        except KeyError:
            item = False
        if item:
            the_form = InventoryItemForm(data, prefix=item.product.id, initial={
                'item_id': item.id,
                'prod_id': item.product.id,
                'freeform_lot_id': item.freeform_lot_id,
                'field_id': item.field_id,
                'custodian': custodian_id,
                'inventory_date': item.inventory_date,
                'planned': item.planned,
                'notes': item.notes})
        else:
            the_form = InventoryItemForm(data, prefix=plan.product.id, initial={
                'prod_id': plan.product.id, 
                'inventory_date': avail_date,
                'planned': 0,
                'notes': ''})
        the_form.description = plan.product.long_name
        form_list.append(the_form) 
    return form_list 

def supply_demand_table(from_date, to_date, member):
    plans = ProductPlan.objects.all()
    cps = ProducerProduct.objects.filter(
        inventoried=False,
        default_quantity__gt=0,
    )
    constants = {}
    for cp in cps:
        constants.setdefault(cp.product, Decimal("0"))
        constants[cp.product] += cp.default_quantity
    pps = ProducerProduct.objects.filter(producer=member).values_list("product_id")
    pps = set(id[0] for id in pps)
    rows = {}    
    for plan in plans:
        wkdate = from_date
        product = plan.product.supply_demand_product()
        if product.id in pps:
            constant = Decimal('0')
            cp = constants.get(product)
            if cp:
                constant = cp
            row = []
            while wkdate <= to_date:
                row.append(constant)
                wkdate = wkdate + datetime.timedelta(days=7)
            row.insert(0, product)
            rows.setdefault(product, row)
            wkdate = from_date
            week = 0
            while wkdate <= to_date:
                if plan.from_date <= wkdate and plan.to_date >= wkdate:
                    if plan.role == "producer":
                        rows[product][week + 1] += plan.quantity
                    else:
                        rows[product][week + 1] -= plan.quantity
                wkdate = wkdate + datetime.timedelta(days=7)
                week += 1
    label = "Product/Weeks"
    columns = [label]
    wkdate = from_date
    while wkdate <= to_date:
        columns.append(wkdate)
        wkdate = wkdate + datetime.timedelta(days=7)
    rows = rows.values()
    rows.sort(lambda x, y: cmp(x[0].short_name, y[0].short_name))
    sdtable = SupplyDemandTable(columns, rows)
    return sdtable

def producer_suppliable_demand(from_date, to_date, producer):
    customer_plans = ProductPlan.objects.filter(role="consumer")
    producer_plans = ProductPlan.objects.filter(member=producer)
    rows = {}    
    for plan in producer_plans:
        wkdate = from_date
        row = []
        while wkdate <= to_date:
            row.append(SuppliableDemandCell(Decimal("0"), Decimal("0")))
            wkdate = wkdate + datetime.timedelta(days=7)
        product = plan.product.supply_demand_product()

        row.insert(0, product)
        rows.setdefault(product, row)
        wkdate = from_date
        week = 0
        while wkdate <= to_date:
            if plan.from_date <= wkdate and plan.to_date >= wkdate:
                rows[product][week + 1].supply += plan.quantity
            wkdate = wkdate + datetime.timedelta(days=7)
            week += 1
    pps = ProducerProduct.objects.filter(producer=producer).values_list("product_id")
    pps = set(id[0] for id in pps)
    for plan in customer_plans:
        wkdate = from_date
        product = plan.product.supply_demand_product()
        if product.id in pps:
            week = 0
            while wkdate <= to_date:
                if plan.from_date <= wkdate and plan.to_date >= wkdate:
                    rows[product][week + 1].demand += plan.quantity
                wkdate = wkdate + datetime.timedelta(days=7)
                week += 1
    rows = rows.values()
    fee = producer_fee()
    for row in rows:
        for x in range(1, len(row)):
            sd = row[x].suppliable()
            if sd >= 0:
                income = sd * row[0].price
                row[x] = income - (income * fee)
            else:
                row[x] = Decimal("0")
    income_rows = []
    for row in rows:
        total = Decimal("0")
        for x in range(1, len(row)):
            total += row[x]
            row[x] = row[x].quantize(Decimal('.1'), rounding=ROUND_UP)
        if total:
            row.append(total.quantize(Decimal('1.'), rounding=ROUND_UP))
            income_rows.append(row)
    label = "Item\Weeks"
    columns = [label]
    wkdate = from_date
    while wkdate <= to_date:
        columns.append(wkdate)
        wkdate = wkdate + datetime.timedelta(days=7)
    columns.append("Total")
    income_rows.sort(lambda x, y: cmp(x[0].long_name, y[0].short_name))
    sdtable = SupplyDemandTable(columns, income_rows)
    return sdtable


