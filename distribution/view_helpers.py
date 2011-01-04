from decimal import *
import datetime

from django.forms.formsets import formset_factory

from models import *
from forms import *

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# shd plan_weeks go to the view and include headings?
# somebody needs headings!
def create_weekly_plan_forms(rows, data=None):
    form_list = []
    PlanCellFormSet = formset_factory(PlanCellForm, extra=0)

    for row in rows:
        product = row[0]
        row_form = PlanRowForm(data, prefix=product.id, initial={'product_id': product.id})
        row_form.product = product.long_name
        cells = row[1:len(row)]
        initial_data = []
        for cell in cells:
            plan_id = ""
            if cell.plan:
                plan_id = cell.plan.id
            dict = {
                'plan_id': plan_id,
                'product_id': cell.product.id,
                'from_date': cell.from_date,
                'to_date': cell.to_date,
                'quantity': cell.quantity,
            }
            initial_data.append(dict)
        row_form.formset = PlanCellFormSet(data, prefix=product.id, initial=initial_data)
        form_list.append(row_form)
    return form_list
        

class SupplyDemandTable(object):
    def __init__(self, columns, rows):
         self.columns = columns
         self.rows = rows

def supply_demand_table(from_date, to_date, member=None):
    plans = ProductPlan.objects.all()
    cps = ProducerProduct.objects.filter(
        inventoried=False,
        default_quantity__gt=0,
    )
    constants = {}
    for cp in cps:
        constants.setdefault(cp.product, Decimal("0"))
        constants[cp.product] += cp.default_quantity
    if member:
        plans = plans.filter(member=member)
    rows = {}    
    for plan in plans:
        wkdate = from_date
        product = plan.product.supply_demand_product()
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

def supply_demand_weekly_table(week_date):
    # does plannable make sense here? how did it get planned in the first place?
    plans = ProductPlan.objects.filter(
        product__plannable=True,
        from_date__lte=week_date,
        to_date__gte=week_date,
    ).order_by("-role", "member__short_name")
    columns = []
    rows = {}
    for plan in plans:
        if not plan.member in columns:
            columns.append(plan.member)
    columns.insert(0, "Product\Member")
    columns.append("Balance")
    for plan in plans:
        if not rows.get(plan.product):
            row = []
            for i in range(0, len(columns)-1):
                row.append(Decimal("0"))
            row.insert(0, plan.product)
            rows[plan.product] = row
        if plan.role == "producer":
            rows[plan.product][columns.index(plan.member)] += plan.quantity
            rows[plan.product][len(columns)-1] += plan.quantity
        else:
            rows[plan.product][columns.index(plan.member)] -= plan.quantity
            rows[plan.product][len(columns)-1] -= plan.quantity
    rows = rows.values()
    rows.sort(lambda x, y: cmp(x[0].short_name, y[0].short_name))
    sdtable = SupplyDemandTable(columns, rows)
    return sdtable

class SuppliableDemandCell(object):
    def __init__(self, supply, demand):
         self.supply = supply
         self.demand = demand

    def suppliable(self):
        answer = Decimal("0")
        if self.supply and self.demand:
            if self.supply > self.demand:
                answer = self.demand
            else:
                answer = self.supply
        return answer

def suppliable_demand(from_date, to_date, member=None):
    plans = ProductPlan.objects.all()
    if member:
        plans = plans.filter(member=member)
    rows = {}    
    for plan in plans:
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
                if plan.role == "producer":
                    rows[product][week + 1].supply += plan.quantity
                else:
                    rows[product][week + 1].demand += plan.quantity
            wkdate = wkdate + datetime.timedelta(days=7)
            week += 1
    rows = rows.values()
    cust_fee = customer_fee()
    for row in rows:
        for x in range(1, len(row)):
            sd = row[x].suppliable()
            if sd >= 0:
                income = sd * row[0].price
                row[x] = income
            else:
                row[x] = Decimal("0")
    income_rows = []
    for row in rows:
        base = Decimal("0")
        total = Decimal("0")
        for x in range(1, len(row)):
            cell = row[x]
            base += cell
            cell += cell * cust_fee
            total += cell
            row[x] = cell.quantize(Decimal('.1'), rounding=ROUND_UP)            
        if total:
            net = base * cust_fee + (base * producer_fee())
            net = net.quantize(Decimal('1.'), rounding=ROUND_UP)
            total = total.quantize(Decimal('1.'), rounding=ROUND_UP)
            row.append(total)
            row.append(net)
            income_rows.append(row)
    label = "Item\Weeks"
    columns = [label]
    wkdate = from_date
    while wkdate <= to_date:
        columns.append(wkdate)
        wkdate = wkdate + datetime.timedelta(days=7)
    columns.append("Total")
    columns.append("Net")
    income_rows.sort(lambda x, y: cmp(x[0].long_name, y[0].short_name))
    sdtable = SupplyDemandTable(columns, income_rows)
    return sdtable



class PlannedWeek(object):
    def __init__(self, product, from_date, to_date, quantity):
         self.product = product
         self.from_date = from_date
         self.to_date = to_date
         self.quantity = quantity
         self.plan = None

def plan_weeks(member, products, from_date, to_date):
    plans = ProductPlan.objects.filter(member=member)
    #if member.is_customer():
    #    products = CustomerProduct.objects.filter(customer=member, planned=True)
    #else:
    #    products = ProducerProduct.objects.filter(producer=member, planned=True)
    #if not products:
    #    products = Product.objects.filter(plannable=True)
    rows = {}    
    for pp in products:
        try:
            product = pp.product
        except:
            product = pp
        wkdate = from_date
        row = [product]
        while wkdate <= to_date:
            enddate = wkdate + datetime.timedelta(days=6)
            row.append(PlannedWeek(product, wkdate, enddate, Decimal("0")))
            wkdate = enddate + datetime.timedelta(days=1)
        #row.insert(0, product)
        rows.setdefault(product, row)
    for plan in plans:
        product = plan.product
        wkdate = from_date
        week = 0
        while wkdate <= to_date:
            enddate = wkdate + datetime.timedelta(days=6)
            if plan.from_date <= wkdate and plan.to_date >= wkdate:
                rows[product][week + 1].quantity = plan.quantity
                rows[product][week + 1].plan = plan
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

def plans_for_dojo(member, products, from_date, to_date):
    plans = ProductPlan.objects.filter(member=member)
    rows = {}    
    for pp in products:
        try:
            product = pp.product
        except:
            product = pp
        wkdate = from_date
        row = {}
        row["product"] = product.long_name
        row["id"] = product.id
        row["member_id"] = member.id
        row["from_date"] = from_date.strftime('%Y-%m-%d')
        row["to_date"] = to_date.strftime('%Y-%m-%d')
        while wkdate <= to_date:
            enddate = wkdate + datetime.timedelta(days=6)
            #row.append(PlannedWeek(product, wkdate, enddate, Decimal("0")))
            row[wkdate.strftime('%Y-%m-%d')] = "0"
            wkdate = enddate + datetime.timedelta(days=1)
        rows.setdefault(product, row)
    for plan in plans:
        product = plan.product
        wkdate = from_date
        week = 0
        while wkdate <= to_date:
            enddate = wkdate + datetime.timedelta(days=6)
            if plan.from_date <= wkdate and plan.to_date >= wkdate:
                #rows[product][week + 1].quantity = plan.quantity
                #rows[product][week + 1].plan = plan
                rows[product][wkdate.strftime('%Y-%m-%d')] = str(plan.quantity)
                rows[product][":".join([wkdate.strftime('%Y-%m-%d'), "plan_id"])] = plan.id
            wkdate = wkdate + datetime.timedelta(days=7)
            week += 1
    label = "Product"
    columns = [label]
    wkdate = from_date
    while wkdate <= to_date:
        columns.append(wkdate.strftime('%Y-%m-%d'))
        wkdate = wkdate + datetime.timedelta(days=7)
    rows = rows.values()
    rows.sort(lambda x, y: cmp(x["product"], y["product"]))
    sdtable = SupplyDemandTable(columns, rows)
    return sdtable

