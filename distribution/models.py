import datetime
from decimal import *
import itertools
from operator import attrgetter

from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.localflavor.us.models import PhoneNumberField
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _

from notification.models import NoticeType

def food_network():
    try:
        return FoodNetwork.objects.all()[0]
    except IndexError:
        raise FoodNetwork.DoesNotExist()

def customer_fee():
    try:
        answer = food_network().customer_fee
    except FoodNetwork.DoesNotExist:
        answer = Decimal("0")
    return answer

def producer_fee():
    try:
        answer = food_network().producer_fee
    except FoodNetwork.DoesNotExist:
        answer = Decimal("0")
    return answer

def next_delivery_date():
    answer = datetime.date.today()
    try:
        answer = food_network().next_delivery_date
    except FoodNetwork.DoesNotExist:
        answer = datetime.date.today()
    return answer

def ordering_by_lot():
    try:
        answer = food_network().order_by_lot
    except FoodNetwork.DoesNotExist:
        answer = False
    return answer

def use_plans_for_ordering():
    try:
        answer = food_network().use_plans_for_ordering
    except FoodNetwork.DoesNotExist:
        answer = False
    return answer

def default_product_expiration_days():
    try:
        answer = food_network().default_product_expiration_days
    except FoodNetwork.DoesNotExist:
        answer = 6
    return answer

def customer_terms():
    return food_network().customer_terms


def member_terms():
    return food_network().member_terms

class ProductAndProducers(object):
     def __init__(self, product, qty, price, producers):
         self.product = product
         self.qty = qty
         self.price = price
         self.producers = producers

         
class ProductAndLots(object):
     def __init__(self, product, qty, price, lots):
         self.product = product
         self.qty = qty
         self.price = price
         self.lots = lots


class ProductQuantity(object):
     def __init__(self, product, qty):
         self.product = product
         self.qty = qty


class ProductOrderedAndAvailable(object):
     def __init__(self, product, ordered, lots):
         self.product = product
         self.ordered = ordered
         self.lots = lots


class ProductReceiptsAndSales(object):
     def __init__(self,
                  product,
                  receipts_qty_week,
                  receipts_money_week,
                  sales_qty_week,
                  sales_money_week,
                  receipts_qty_month,
                  receipts_money_month,
                  sales_qty_month,
                  sales_money_month
                 ):
         self.product = product
         self.receipts_qty_week = receipts_qty_week
         self.receipts_money_week = receipts_money_week
         self.sales_qty_week = sales_qty_week
         self.sales_money_week = sales_money_week
         self.receipts_qty_month = receipts_qty_month
         self.receipts_money_month = receipts_money_month
         self.sales_qty_month = sales_qty_month
         self.sales_money_month = sales_money_month


class CustomerProductAvailability(object):
     def __init__(self, product, price, qty, inventory_date, expiration_date):
         self.product = product
         self.price = price
         self.qty = qty
         self.inventory_date = inventory_date
         self.expiration_date = expiration_date


class StaffProductAvailability(object):
     def __init__(self, product, price, avail, ordered, inventory_date, expiration_date):
         self.product = product
         self.price = price
         self.avail = avail
         self.ordered = ordered
         self.inventory_date = inventory_date
         self.expiration_date = expiration_date


class PickupCustodian(object):
     def __init__(self, custodian, address, products):
         self.custodian = custodian
         self.address = address
         self.products = products
 
         
class PickupDistributor(object):
     def __init__(self, distributor, email, custodians):
         self.distributor = distributor
         self.email = email
         self.custodians = custodians
         
         
class OrderToBeDelivered(object):
     def __init__(self, customer, address, products):
         self.customer = customer
         self.address = address
         self.products = products
         
class DeliveryDistributor(object):
     def __init__(self, distributor, email, customers):
         self.distributor = distributor
         self.email = email
         self.customers = customers

# inheritance approach based on
# http://www.djangosnippets.org/snippets/1034/
class SubclassingQuerySet(QuerySet):
    def __getitem__(self, k):
        result = super(SubclassingQuerySet, self).__getitem__(k)
        if isinstance(result, models.Model):
            return result.as_leaf_class()
        else:
            return result
    def __iter__(self):
        for item in super(SubclassingQuerySet, self).__iter__():
            yield item.as_leaf_class()

    
class PartyManager(models.Manager):
    
    def get_query_set(self):
        return SubclassingQuerySet(self.model)
    
    def planned_producers(self):
        producers = []
        all_prods = Party.subclass_objects.all()
        for prod in all_prods:
            if prod.is_producer():
                if prod.producer_products.all().count():
                    producers.append(prod)
        return producers

    def all_distributors(self):
        parties = Party.objects.all()
        dists = []
        for party in parties:
            if isinstance(party.as_leaf_class(), Distributor):
                dists.append(party)
        dists.append(food_network())
        return dists

    def all_planners(self):
        parties = Party.objects.all()
        dists = []
        for party in parties:
            if isinstance(party.as_leaf_class(), Producer):
                dists.append(party)
            if isinstance(party.as_leaf_class(), Customer):
                dists.append(party)
        return dists


    def payable_members(self):
        parties = Party.objects.all().exclude(pk=1)
        pms = []
        for party in parties:
            if not isinstance(party.as_leaf_class(), Customer):
                pms.append(party)
        return pms

    def possible_custodians(self):
        parties = Party.objects.all().exclude(pk=1)
        pcs = []
        for party in parties:
            if isinstance(party.as_leaf_class(), Processor) or isinstance(party.as_leaf_class(), Distributor):
                pcs.append(party)
        pcs.append(food_network())
        return pcs

    def producers_and_processors(self):
        parties = Party.objects.all().exclude(pk=1)
        pcs = []
        for party in parties:
            if isinstance(party.as_leaf_class(), Processor) or isinstance(party.as_leaf_class(), Producer):
                pcs.append(party)
        return pcs

    
class Party(models.Model):
    member_id = models.CharField(_('member id'), max_length=12, blank=True)
    short_name = models.CharField(_('short name'), max_length=32, unique=True)
    long_name = models.CharField(_('long name'), max_length=64)
    contact = models.CharField(_('contact'), max_length=64, blank=True)
    phone = PhoneNumberField(_('phone'), blank=True)
    cell = PhoneNumberField(_('cell'), blank=True)
    fax = PhoneNumberField(_('fax'), blank=True)
    address = models.TextField(_('address'), blank=True)
    email_address = models.EmailField(_('email address'), max_length=96, blank=True, null=True)
    description = models.TextField(_('description'), blank=True)
    content_type = models.ForeignKey(ContentType,editable=False,null=True)
    
    objects = models.Manager()
    subclass_objects = PartyManager()

    def __unicode__(self):
        return self.short_name
    
    @property
    def email(self):
        return self.email_address

    class Meta:
        ordering = ('short_name',)
        
    def as_leaf_class(self):
        if self.content_type:
            content_type = self.content_type
            model = content_type.model_class()
            if (model == Party):
                return self
            return model.objects.get(id=self.id)
        else:
            return self

    def is_customer(self):
        if isinstance(self.as_leaf_class(), Customer):
            return True
        else:
            return False

    def is_producer(self):
        if isinstance(self.as_leaf_class(), Producer):
            return True
        else:
            return False

    def is_processor(self):
        if isinstance(self.as_leaf_class(), Processor):
            return True
        else:
            return False

        
    def save(self, *args, **kwargs):
        #import pdb; pdb.set_trace()
        if not self.content_type:
            self.content_type = ContentType.objects.get_for_model(self.__class__)
        self.save_base(*args, **kwargs)
        

# todo: obsolete?
class PartyUser(models.Model):
    party = models.ForeignKey(Party, related_name="users", verbose_name=_('party'))
    user = models.ForeignKey(User, related_name="parties", verbose_name=_('user'))

class EmailIntro(models.Model):
    message = models.TextField(_('message'), blank=True)
    notice_type = models.ForeignKey(NoticeType, related_name="email_intro",
                                    verbose_name=_('email type'))

def avail_email_intro():
    nt = NoticeType.objects.get(label='distribution_fresh_list')
    intro = EmailIntro.objects.filter(notice_type=nt)
    if intro.count():
        intro = intro[0]
    else:
        intro = EmailIntro(message="", notice_type=nt)
    return intro

class FoodNetwork(Party):
    billing_contact = models.CharField(_('billing contact'), max_length=64, blank=True)
    billing_phone = PhoneNumberField(_('billing phone'), blank=True, null=True)
    billing_address = models.TextField(_('billing address'), blank=True)
    billing_email_address = models.EmailField(_('billing email address'), max_length=96, blank=True, null=True)
    customer_terms = models.IntegerField(_('customer terms'), default=0,
        help_text=_('Net number of days for customer to pay invoice'))
    member_terms = models.IntegerField(_('member terms'), blank=True, null=True,
        help_text=_('Net number of days for network to pay member'))
    customer_fee = models.DecimalField(_('customer fee'), max_digits=3, decimal_places=2, default=Decimal("0"),
        help_text=_('Customer Fee is a decimal fraction, not a percentage - for example, .05 instead of 5%. It is a markup, added to the price of an order as a separate line item on invoices'))
    producer_fee = models.DecimalField(_('producer fee'), max_digits=3, decimal_places=2, default=Decimal("0"),
        help_text=_('Producer Fee is a decimal fraction, not a percentage. It is a margin, subtracted from the price, giving the pay price to the producer.'))
    transportation_fee = models.DecimalField(_('transportation fee'), max_digits=8, decimal_places=2, default=Decimal("0"),
        help_text=_('This fee will be added to all orders unless overridden on the Customer'))
    #current_week = models.DateField(_('current week'), default=datetime.date.today, 
    #    null=True, blank=True,
    #    help_text=_('You may use Current week or Next delivery date'))
    next_delivery_date = models.DateField(_('next delivery date'), default=datetime.date.today, 
        help_text=_('Next delivery date for availability and orders'))
    order_by_lot = models.BooleanField(_('order by lot'), default=False, 
        help_text=_('Assign lots when ordering, or assign them later'))
    use_plans_for_ordering = models.BooleanField(_('use plans for ordering'), default=False, 
        help_text=_('If checked, production plan quantities will be available for ordering instead of inventory items'))
    default_product_expiration_days = models.IntegerField(_('expiration days'), default=6,
        help_text=_('This will be the default expiration days for new Products'))


    class Meta:
        ordering = ('short_name',)


    def __unicode__(self):
        return self.short_name
   
    @property
    def email(self):
        return self.email_address

    def receipts_sales(self, thisdate):
        month_start = datetime.date(thisdate.year, thisdate.month, 1)
        week_start = thisdate - datetime.timedelta(days=datetime.date.weekday(thisdate))
        start = min(month_start, week_start)
        items = InventoryItem.objects.filter(
            inventory_date__gte=start)
        products = {}
        for item in items:
            if not item.product.id in products:
                products[item.product.id] =  ProductReceiptsAndSales(
                    item.product,
                    Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"),
                    Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"),
                )
            pras = products[item.product.id]
            qty = item.received
            if not qty:
                qty = item.planned
            money = qty * item.product.price
            money -= money * producer_fee()
            if item.inventory_date >= week_start:
                pras.receipts_qty_week += qty
                pras.receipts_money_week += money
            if item.inventory_date >= month_start:
                pras.receipts_qty_month += qty
                pras.receipts_money_month += money
            ois = OrderItem.objects.filter(
                product = item.product,
                order__delivery_date__gte=start)
            for oi in ois:
                if oi.order.delivery_date >= week_start:
                    pras.sales_qty_week += oi.quantity
                    pras.sales_money_week += oi.extended_price()
                if oi.order.delivery_date >= month_start:
                    pras.sales_qty_month += oi.quantity
                    pras.sales_money_month += oi.extended_price()
        report_lines = products.values()
        report_lines.sort(lambda x, y: cmp(x.product.short_name,
                                           y.product.short_name))
        return report_lines

    def ordered_available(self, delivery_date):
        #todo: combine order qties.
        items = OrderItem.objects.filter(
            order__delivery_date=delivery_date)
        products = {}
        for item in items:
            if not item.product.id in products:
                products[item.product.id] = ProductOrderedAndAvailable(
                    item.product, Decimal("0"), [])
            products[item.product.id].ordered += item.quantity
        items = products.values()
        for item in items:
            item.lots = [lot for lot in
                    item.product.ready_items_today(delivery_date)]
        return items                
    
    # deprecated
    def fresh_list(self, thisdate = None):
        if not thisdate:
            thisdate = next_delivery_date()
        # todo: no need to go thru all products,
        # shd just use InventoryItems or ProductPlans (not by product)
        # see avail_items_for_customer
        prods = Product.objects.all()
        item_list = []
        for prod in prods:
            if self.use_plans_for_ordering:
                items = prod.production_plans(thisdate)
                avail_qty = sum(item.quantity for item in items)
            else:
                items = prod.avail_items_today(thisdate)
                avail_qty = sum(item.avail_qty() for item in items)
            if avail_qty > 0:
                price = prod.price.quantize(Decimal('.01'), rounding=ROUND_UP)
                #producers = []
                #for item in items:
                #    producer = item.producer.long_name
                #    if not producer in producers:
                #        producers.append(producer)
                #item_list.append(ProductAndProducers(prod.long_name, avail_qty, price, producers))
                item_list.append(ProductAndLots(prod.long_name, avail_qty, price, items))
        return item_list

    # deprecated
    def avail_list(self, delivery_date):
        # todo: no need to go thru all products,
        # shd just use InventoryItems or ProductPlans (not by product)
        # see avail_items_for_customer
        prods = Product.objects.all()
        item_list = []
        for prod in prods:
            if self.use_plans_for_ordering:
                items = prod.production_plans(thisdate)
                avail_qty = sum(item.quantity for item in items)
            else:
                items = prod.avail_items_today(thisdate)
                avail_qty = sum(item.avail_qty() for item in items)
            if avail_qty > 0:
                price = prod.price.quantize(Decimal('.01'), rounding=ROUND_UP)
                item_list.append(ProductAndLots(prod.long_name, avail_qty, price, items))
        return item_list
    
    # deprecated
    def pickup_list(self, thisdate = None):
        if not thisdate:
            thisdate = next_delivery_date()
        prods = Product.objects.all()
        distributors = {}
        network = self
        for prod in prods:
            items = prod.ready_items(thisdate)            
            for item in items:
                distributor = item.distributor()
                if not distributor:
                    distributor = network
                if item.custodian:
                    custodian = item.custodian.long_name
                    address = item.custodian.address
                else:
                    custodian = item.producer.long_name
                    address = item.producer.address
                # eliminate items to be delivered by producer or custodian
                if not distributor.id == item.producer.id:
                    if not distributor in distributors:
                        if distributor.email_address:
                            email = distributor.email_address
                        else:
                            email = network.email_address
                        distributors[distributor] = PickupDistributor(distributor.long_name, email, {})
                    this_distributor = distributors[distributor]
                    if not custodian in this_distributor.custodians:
                        this_distributor.custodians[custodian] = PickupCustodian(custodian, address, [])
                    this_distributor.custodians[custodian].products.append(ProductQuantity(item.pickup_label(), item.planned))
        return distributors
        
    def delivery_list(self, thisdate = None):
        if not thisdate:
            thisdate = next_delivery_date()
        weekstart = thisdate - datetime.timedelta(days=datetime.date.weekday(thisdate))
        weekend = weekstart + datetime.timedelta(days=5)
        ois = OrderItem.objects.filter(order__delivery_date__range=(weekstart, weekend))
        
        #customers = {}
        #product_producers = {}
        
        distributors = {}
        network = self
        for oi in ois:
            customer = oi.order.customer.long_name
            product = oi.product.id
            txs = oi.inventorytransaction_set.all()
            # what if no txs, i.e. no lot assignments?
            lots = []
            for tx in txs:
                lots.append(tx.inventory_item)
            for lot in lots:
                distributor = lot.distributor()
                if not distributor:
                    distributor = network
                if not distributor in distributors:
                    if distributor.email_address:
                        email = distributor.email_address
                    else:
                        email = network.email_address
                    distributors[distributor] = DeliveryDistributor(distributor.long_name, email, {})
                this_distributor = distributors[distributor]
                
                if not customer in this_distributor.customers:
                    this_distributor.customers[customer] = OrderToBeDelivered(customer, oi.order.customer.address, {})
                otbd = this_distributor.customers[customer]
                if not product in otbd.products:
                    otbd.products[product] = ProductAndLots(oi.product.long_name, oi.quantity, oi.product.price,[])
                otbd.products[product].lots.append(lot)
        for dist in distributors:
            dd = distributors[dist]
            for cust in dd.customers:
                otbd = dd.customers[cust]
                otbd.products = otbd.products.values()
        return distributors

    # deprecated but used
    def all_avail_items(self, thisdate=None):
        if not thisdate:
            thisdate = next_delivery_date()
        #weekstart = thisdate - datetime.timedelta(days=datetime.date.weekday(thisdate))
        #expired_date = weekstart + datetime.timedelta(days=5)
        expired_date = thisdate
        #import pdb; pdb.set_trace()
        items = InventoryItem.objects.filter(
            inventory_date__lte=expired_date,
            expiration_date__gt=expired_date)
        items = items.filter(Q(remaining__gt=0) |
                             Q(onhand__gt=0)).order_by("producer__short_name",
                                                       "product__short_name")
        return items

    def avail_items_for_customer(self, delivery_date):
        items = InventoryItem.objects.filter(
            inventory_date__lte=delivery_date,
            expiration_date__gt=delivery_date)
        items = items.filter(Q(remaining__gt=0) |
                             Q(onhand__gt=0)).order_by("producer__short_name",
                                                       "product__short_name")
        return items

    def customer_availability(self, delivery_date):
        avail = []
        products = {}
        if self.use_plans_for_ordering:
            plans = ProductPlan.objects.filter(
                role="producer",
                from_date__lte=delivery_date, 
                to_date__gte=delivery_date)
            for plan in plans:
                if plan.product.id not in products:
                    products[plan.product.id] = CustomerProductAvailability(plan.product,
                        Decimal("0"), Decimal("0"), plan.from_date, plan.to_date)
                products[plan.product.id].qty += plan.quantity
        else:
            items = self.avail_items_for_customer(delivery_date)
            for item in items:
                if item.product.id not in products:
                    products[item.product.id] = CustomerProductAvailability(item.product,
                         Decimal("0"), Decimal("0"), item.inventory_date, item.expiration_date)
                pa = products[item.product.id]
                pa.qty += item.avail_qty()
                if pa.inventory_date < item.inventory_date:
                    pa.inventory_date = item.inventory_date
                if pa.expiration_date > item.expiration_date:
                    pa.expiration_date = item.expiration_date
        for pa in products.values():
            pa.qty -= pa.product.total_ordered_for_timespan(
                pa.inventory_date, pa.expiration_date)
            if pa.qty > 0:
                pa.category = pa.product.parent_string()
                pa.product_name = pa.product.short_name
                pa.price = pa.product.unit_price_for_date(delivery_date).quantize(Decimal('.01'), rounding=ROUND_UP)
                avail.append(pa)
        avail = sorted(avail, key=attrgetter('product_name'))
        return avail

    def staff_availability(self, delivery_date):
        avail = []
        products = {}
        if self.use_plans_for_ordering:
            plans = ProductPlan.objects.filter(
                role="producer",
                from_date__lte=delivery_date, 
                to_date__gte=delivery_date)
            for plan in plans:
                if plan.product.id not in products:
                    products[plan.product.id] = StaffProductAvailability(plan.product,
                        Decimal("0"), Decimal("0"), Decimal("0"), plan.from_date, plan.to_date)
                products[plan.product.id].avail += plan.quantity
        else:
            items = self.avail_items_for_customer(delivery_date)
            for item in items:
                if item.product.id not in products:
                    products[item.product.id] = StaffProductAvailability(item.product,
                         Decimal("0"), Decimal("0"), Decimal("0"), item.inventory_date, item.expiration_date)
                pa = products[item.product.id]
                pa.avail += item.avail_qty()
                if pa.inventory_date < item.inventory_date:
                    pa.inventory_date = item.inventory_date
                if pa.expiration_date > item.expiration_date:
                    pa.expiration_date = item.expiration_date
        for pa in products.values():
            pa.ordered = pa.product.total_ordered_for_timespan(
                pa.inventory_date, pa.expiration_date)
            if pa.avail > 0:
                pa.category = pa.product.parent_string()
                pa.product_name = pa.product.short_name
                pa.price = pa.product.unit_price_for_date(delivery_date).quantize(Decimal('.01'), rounding=ROUND_UP)
                avail.append(pa)
        avail = sorted(avail, key=attrgetter('category'))
        return avail

    # deprecated
    def all_active_items(self, thisdate = None):
        # todo: this and dashboard need work
        # e.g. shows steers with no avail or orders, but some were consumed
        # delivery column commented out because order-by-lot delivers at same time as ordered
        if not thisdate:
            thisdate = next_delivery_date()
        weekstart = thisdate - datetime.timedelta(days=datetime.date.weekday(thisdate))
        weekend = weekstart + datetime.timedelta(days=5)
        return InventoryItem.objects.filter(
            inventory_date__lte=weekend,
            expiration_date__gt=weekend)
          

class ProducerManager(models.Manager):

    def planned_producers(self):
        producers = []
        all_prods = Producer.objects.all()
        for prod in all_prods:
            if prod.product_plans.all().count():
                producers.append(prod)
        return producers


class Producer(Party):
    delivers = models.BooleanField(_('delivers'), default=False,
        help_text=_('Delivers products directly to customers?'))


class Processor(Party):
    pass


class Distributor(Party):
    transportation_fee = models.DecimalField(_('transportation fee'), max_digits=8, decimal_places=2, default=Decimal("0"),
        help_text=_('Anything but a zero here overrides the Food Network default transportation fee for this distributor.'))


class NextDeliveryCycle(object):
    def __init__(self, cycle, delivery_date):
        self.cycle = cycle
        self.delivery_date = delivery_date
    
    def order_closing(self):
        return self.cycle.order_closing(self.delivery_date)


class Customer(Party):
    customer_transportation_fee = models.DecimalField(_('customer transportation fee'), max_digits=8, decimal_places=2, default=Decimal("0"),
        help_text=_('Any value but 0 in this field will override the default fee from the Food Network'))
    apply_transportation_fee = models.BooleanField(_('apply transportation fee'), default=True,
        help_text=_('Add transportation fee to all orders for this customer, or not?'))

    def __unicode__(self):
        return self.short_name
    
    def distributor(self):
        #todo: revise when 5S distributor assignments are clear
        # maybe add distributor field to Customer or some logic on FoodNetwork
        ds = Distributor.objects.all()
        if ds.count():
            return Distributor.objects.all()[0]
        else:
            return None

    def transportation_fee(self):
        if self.apply_transportation_fee:
            if self.customer_transportation_fee:
                return self.customer_transportation_fee
            else:
                return food_network().transportation_fee
        else:
            return Decimal("0")

    def next_delivery_date(self, date_and_time=None):
        if not date_and_time:
            date_and_time = datetime.datetime.now()
        cycles = self.delivery_cycles.all()
        dd = None
        if cycles.count() == 1:
            cycle = cycles[0].delivery_cycle
            dd = cycle.next_delivery_date()
            if date_and_time > cycle.order_closing(dd):
                dd = dd + datetime.timedelta(days=1)
                dd = cycle.next_delivery_date(dd)
        elif cycles:
            for c in cycles:
                cycle = c.delivery_cycle
                dd = cycle.next_delivery_date()
                if cycle.order_closing(dd) > date_and_time:
                    break
        return dd

    def next_delivery_cycle(self,  date_and_time=None):
        if not date_and_time:
            date_and_time = datetime.datetime.now()
        cycles = self.delivery_cycles.all()
        answer = None
        if cycles.count() == 1:
            cycle = cycles[0].delivery_cycle
            dd = cycle.next_delivery_date()
            oc = cycle.order_closing(dd)
            answer = NextDeliveryCycle(cycle, dd)
            if date_and_time > oc:
                dd = dd + datetime.timedelta(days=1)
                dd = cycle.next_delivery_date(dd)
                answer = NextDeliveryCycle(cycle, dd)
        elif cycles:
            for c in cycles:
                cycle = c.delivery_cycle
                dd = cycle.next_delivery_date()
                if cycle.order_closing(dd) > date_and_time:
                    answer = NextDeliveryCycle(cycle, dd)
                    break
        return answer

    @property
    def email(self):
        return self.email_address

    class Meta:
        ordering = ('short_name',)


class CustomerContact(models.Model):
    customer = models.ForeignKey(Customer,
        verbose_name=_('customer'), related_name='contacts')
    name = models.CharField(_('name'), max_length=64)
    email = models.EmailField(_('email address'), max_length=96, blank=True, null=True)
    phone = PhoneNumberField(_('phone'), blank=True)
    cell = PhoneNumberField(_('cell'), blank=True)
    login_user = models.OneToOneField(User, related_name='customer_contact',
        blank=True, null=True)


# based on dfs from threaded_comments
def nested_objects(node, all_nodes):
     to_return = [node,]
     for subnode in all_nodes:
         if subnode.parent and subnode.parent.id == node.id:
             to_return.extend([nested_objects(subnode, all_nodes),])
     return to_return

def flattened_children(node, all_nodes, to_return):
     to_return.append(node)
     for subnode in all_nodes:
         if subnode.parent and subnode.parent.id == node.id:
             flattened_children(subnode, all_nodes, to_return)
     return to_return


class Product(models.Model):
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children',
        limit_choices_to = {'is_parent': True}, verbose_name=_('parent'))
    short_name = models.CharField(_('short name'), max_length=32, unique=True)
    long_name = models.CharField(_('long name'), max_length=64)
    growing_method = models.CharField(_('growing method'), max_length=255,
        blank=True)
    sellable = models.BooleanField(_('sellable'), default=True,
        help_text=_('Should this product appear in Order form?'))
    plannable = models.BooleanField(_('plannable'), default=True,
        help_text=_('Should this product appear in Plan form?'))
    stockable = models.BooleanField(_('inventoried'), default=True,
        help_text=_('Should this product be stored as Inventory Items?'))
    is_parent = models.BooleanField(_('is parent'), default=False,
        help_text=_('Should this product appear in parent selections?'))
    price = models.DecimalField(_('price'), max_digits=8, decimal_places=2, default=Decimal(0))
    customer_fee_override = models.DecimalField(_('customer fee override'), max_digits=3, decimal_places=2, blank=True, null=True, 
        help_text=_('Enter override as a decimal fraction, not a percentage - for example, .05 instead of 5%. Note: you cannot override to zero here, only on Order Items.'))
    pay_producer = models.BooleanField(_('pay producer'), default=True,
        help_text=_('If checked, the Food Network pays the producer for issues, deliveries and damages of this product.'))
    pay_producer_on_terms = models.BooleanField(_('pay producer on terms'), default=False,
        help_text=_('If checked, producer paid on member terms. If not, producers paid based on customer order payments. Note: Issues always paid on member terms.'))
    expiration_days = models.IntegerField(_('expiration days'), default=default_product_expiration_days,
        help_text=_('Inventory Items (Lots) of this product will expire in this many days.'))

    def __unicode__(self):
        return self.long_name

    def formatted_unit_price(self):
        return self.price.quantize(Decimal('.01'), rounding=ROUND_UP)

    def formatted_unit_price_for_date(self, date):
        return self.unit_price_for_date(date).quantize(Decimal('.01'), rounding=ROUND_UP)
    
    def unit_price_for_date(self, date):
        up = self.price
        specials = Special.objects.filter(
            product=self,
            from_date__lte=date,
            to_date__gte=date)
        if specials:
            special = specials[0]
            up = special.price
        return up

    # suspect but used
    #shd be based on delivery cycle
    #changed temporarily to dup avail_items_today
    def avail_items(self, thisdate):
        #import pdb; pdb.set_trace()
        #weekstart = thisdate - datetime.timedelta(days=datetime.date.weekday(thisdate))
        #weekend = weekstart + datetime.timedelta(days=5)
        #expired_date = weekstart + datetime.timedelta(days=5)
        #items = InventoryItem.objects.filter(product=self,
        #    inventory_date__lte=thisdate,
        #    expiration_date__gt=expired_date)
        #items = items.filter(Q(remaining__gt=0) | Q(onhand__gt=0))
        #return items
        return self.avail_items_today(thisdate)

    # ok
    def avail_items_today(self, thisdate):
        """
        means all available inventory items not reduced by orders?
        """
        items = InventoryItem.objects.filter(product=self,
            inventory_date__lte=thisdate,
            expiration_date__gt=thisdate)
        items = items.filter(Q(remaining__gt=0) | Q(onhand__gt=0))
        return items

    def ready_items_today(self, thisdate):
        """
        means all non-received ready inventory items
        """
        items = InventoryItem.objects.filter(product=self,
            inventory_date__lte=thisdate,
            expiration_date__gt=thisdate)
        items = items.filter(received=Decimal("0"), planned__gt=0)
        return items


    def production_plans(self, thisdate):
        weekstart = thisdate - datetime.timedelta(days=datetime.date.weekday(thisdate))
        weekend = weekstart + datetime.timedelta(days=5)
        plans = ProductPlan.objects.select_related(depth=1).filter(
            product=self,
            role="producer",
            from_date__lte=thisdate, 
            to_date__gte=weekend)
        return plans

    #suspect - probably obsolete
    def current_items(self, thisdate):
        weekstart = thisdate - datetime.timedelta(days=datetime.date.weekday(thisdate))
        weekend = weekstart + datetime.timedelta(days=5)
        expired_date = weekstart + datetime.timedelta(days=5)
        items = InventoryItem.objects.filter(product=self, 
            inventory_date__lte=weekend,
            expiration_date__gt=expired_date)
        #items = items.filter(Q(remaining__gt=0) | Q(onhand__gt=0))
        return items

    # suspect - used once
    def ready_items(self, thisdate):
        weekstart = thisdate - datetime.timedelta(days=datetime.date.weekday(thisdate))
        weekend = weekstart + datetime.timedelta(days=5)
        items = InventoryItem.objects.filter(product=self, 
            inventory_date__range=(weekstart, weekend),
            planned__gt=0, onhand__exact=0,  received__exact=0)
        return items

    #suspect - used a lot - ok if meaning is correct for use
    def total_avail(self, thisdate):
        """
        means quantity available on this date, not reduced by orders
        """
        if use_plans_for_ordering():
            return sum(plan.quantity for plan in self.production_plans(thisdate))
        else:
            return sum(item.avail_qty() for item in self.avail_items(thisdate))

    # dup of total_avail? no, because it uses avail_items_today
    def total_avail_today(self, thisdate):
        """
        means quantity available on this date, not reduced by orders
        """
        if use_plans_for_ordering():
            return sum(plan.quantity for plan in self.production_plans(thisdate))
        else:
            return sum(item.avail_qty() for item in self.avail_items_today(thisdate))
           
    #suspect    
    def avail_producers(self, thisdate):
        producers = []
        myavails = self.avail_items_today(thisdate)
        for av in myavails:
            producers.append(av.producer.short_name)
        producers = list(set(producers))
        producer_string = ", ".join(producers)
        return producer_string

    #suspect
    def active_producers(self, thisdate):
        producers = []
        myavails = self.avail_items_today(thisdate)
        for av in myavails:
            producers.append(av.producer.short_name)
        deliveries = self.deliveries_this_week(thisdate)
        for delivery in deliveries:
            producers.append(delivery.inventory_item.producer.short_name)
        producers = list(set(producers))
        producer_string = ", ".join(producers)
        return producer_string

    def current_orders_for_timespan(self, from_date, to_date):
        return OrderItem.objects.filter(product=self,
            order__delivery_date__range=(from_date, to_date))
    
    def total_ordered_for_timespan(self, from_date, to_date):
        return sum(order.unfilled_quantity() for order in
            self.current_orders_for_timespan(from_date, to_date))

    # deprecated - used a little
    def current_orders(self, thisdate):
        #todo: this date range shd be changed
        # maybe something based on DeliveryCycle?
        return OrderItem.objects.filter(product=self,
                                        order__delivery_date=thisdate)

    #dup - used alot
    #shd differentiate, one shd be all ordered including filled and unfilled?
    def total_ordered(self, thisdate):
        return sum(order.unfilled_quantity() for order in self.current_orders(thisdate))

    # temp - differentiated
    def total_order_quantity(self, thisdate):
        return sum(order.quantity for order in self.current_orders(thisdate))

    #dup - used once below
    def total_unfilled(self, thisdate):
        myorders = self.current_orders(thisdate)
        return sum(order.unfilled_quantity() for order in myorders)

    # ok
    def avail_for_customer(self, thisdate):
        """
        means quantity available for this date, reduced by quantity ordered
        """
        if use_plans_for_ordering():
            avail = sum(plan.quantity for plan in self.production_plans(thisdate))
        else:
            avail = self.total_avail_today(thisdate)
        return avail - self.total_unfilled(thisdate)

    #suspect - used twice
    def deliveries_this_week(self, thisdate):
        weekstart = thisdate - datetime.timedelta(days=datetime.date.weekday(thisdate))
        weekend = weekstart + datetime.timedelta(days=5)
        deliveries = InventoryTransaction.objects.filter(transaction_type="Delivery")
        return deliveries.filter(
            order_item__product=self, transaction_date__range=(weekstart, weekend))

    #suspect - not used
    def total_delivered(self, thisdate):
        deliveries = self.deliveries_this_week(thisdate)
        return sum(delivery.amount for delivery in deliveries)
    
    def decide_fee(self):
        prod_fee = self.customer_fee_override
        if prod_fee:
            my_fee = prod_fee
        else:
            my_fee = customer_fee()
        return my_fee
    
    def parent_string(self):
        answer = ''
        prod = self
        parents = []
        while prod.parent:
            if prod.parent.id == prod.id:
                break
            parents.append(prod.parent.short_name)
            prod = prod.parent
        if len(parents) > 0:
            parents.reverse()
            answer = ', '.join(parents)
        return answer

    def supply_demand_product(self):
        answer = self
        prod = self
        while prod.parent:
            if prod.parent.plannable:
                answer = prod.parent
                break
            else:
                prod = prod.parent
        return answer

    def sellable_children(self):
        kids = flattened_children(self, Product.objects.all(), [])
        sellables = []
        for kid in kids:
            if kid.sellable:
                sellables.append(kid)
        return sellables

    def plannable_children(self):
        kids = flattened_children(self, Product.objects.all(), [])
        plannables = []
        for kid in kids:
            if kid.plannable:
                plannables.append(kid)
        return plannables

    def stockable_children(self):
        kids = flattened_children(self, Product.objects.all(), [])
        stockables = []
        for kid in kids:
            if kid.stockable:
                stockables.append(kid)
        return stockables

    def producer_totals(self):
        return sum(producer.default_quantity for producer in self.product_producers.all())

    class Meta:
        ordering = ('short_name',)


class Special(models.Model):
    product = models.ForeignKey(Product, 
        limit_choices_to = {'sellable': True}, verbose_name=_('product'), 
        related_name="specials")
    price = models.DecimalField(_('price'), max_digits=8, decimal_places=2, default=Decimal(0))
    headline = models.CharField(_('headline'), max_length=128)
    description = models.TextField(_('description'))
    from_date = models.DateField(_('from date'), )
    to_date = models.DateField(_('to date'), )

    class Meta:
        ordering = ('-from_date',)

    def formatted_price(self):
        return self.price.quantize(Decimal('.01'), rounding=ROUND_UP)


PLAN_ROLE_CHOICES = (
    ('consumer', _('consumer')),
    ('producer', _('producer')),
)


class ProductPlan(models.Model):
    member = models.ForeignKey(Party, 
        related_name="product_plans", verbose_name=_('member')) 
    product = models.ForeignKey(Product, 
        limit_choices_to = {'plannable': True}, verbose_name=_('product'))
    from_date = models.DateField(_('from date'), )
    to_date = models.DateField(_('to date'), )
    quantity = models.DecimalField(_('Qty per week'), max_digits=8, decimal_places=2,
        default=Decimal('0'))
    role = models.CharField(_('role'), max_length=12, choices=PLAN_ROLE_CHOICES,
                            default="producer")
    inventoried = models.BooleanField(_('inventoried'), default=True,
        help_text=_("If not inventoried, the planned qty per week will be used for ordering"))
    distributor = models.ForeignKey(Party, related_name="plan_distributors", 
        blank=True, null=True, verbose_name=_('distributor'))
    
    def __unicode__(self):
        return " ".join([
            self.member.short_name,
            self.product.short_name,
            self.from_date.strftime('%Y-%m-%d'),
            self.to_date.strftime('%Y-%m-%d'),
            str(self.quantity)])
        
    class Meta:
        ordering = ('product', 'member', 'from_date')

    @property
    def producer(self):
        if self.role=="producer":
            return self.member
        else:
            return None


class ProducerProduct(models.Model):
    producer = models.ForeignKey(Party, 
        related_name="producer_products", verbose_name=_('producer')) 
    product = models.ForeignKey(Product, 
        related_name="product_producers", verbose_name=_('product'))
    #todo: maybe default_quantity shd be renamed qty_per_year
    default_quantity = models.DecimalField(max_digits=8, decimal_places=2,
        default=Decimal('0'), verbose_name=_('Qty per year'))
    default_avail_qty = models.DecimalField(max_digits=8, decimal_places=2,
        default=Decimal('0'), verbose_name=_('Default available qty'),
        help_text = _("Used only if this producer-product is not inventoried"))
    inventoried = models.BooleanField(_('inventoried'), default=True,
        help_text=_("If not inventoried, an Inventory Item using the default available qty will be created automatically every week "))
    planned = models.BooleanField(_('planned'), default=True,
        help_text=_('Should this product appear in Plan forms?'))
    distributor = models.ForeignKey(Party, related_name="producer_distributors", 
        blank=True, null=True, verbose_name=_('distributor'))
    
    def __unicode__(self):
        return " ".join([
            self.producer.short_name,
            self.product.short_name])
        
    class Meta:
        ordering = ('producer', 'product')


class MemberProductList(models.Model):
    member = models.ForeignKey(Party, 
        related_name="product_lists", verbose_name=_('member'))
    list_name = models.CharField(_('list name'), max_length=64)
    description = models.CharField(_('description'), max_length=255)

    def __unicode__(self):
        return " ".join([
            self.member.short_name,
            self.list_name,])


class CustomerProduct(models.Model):
    customer = models.ForeignKey(Party, 
        related_name="customer_products", verbose_name=_('customer')) 
    product = models.ForeignKey(Product, 
        limit_choices_to = {'plannable': True}, verbose_name=_('product'))
    product_list = models.ForeignKey(MemberProductList, blank=True, null=True,
        help_text=_('You may separate products into different lists.'),
        verbose_name=_('product_list'))
    default_quantity = models.DecimalField(max_digits=8, decimal_places=2,
        default=Decimal('0'), verbose_name=_('Default quantity per week or order'))
    planned = models.BooleanField(_('planned'), default=True,
        help_text=_('Should this product appear in Plan forms?'))

        
    class Meta:
        ordering = ('customer', 'product')

    def __unicode__(self):
        return " ".join([
            self.customer.short_name,
            self.product.short_name,])


class InventoryItem(models.Model):
    freeform_lot_id = models.CharField(_("Lot Id"), max_length=64, blank=True,
        help_text=_('Optional - if you do not enter a Lot Id, one will be created.'))
    producer = models.ForeignKey(Party, 
        related_name="inventory_items", verbose_name=_('producer'))
    field_id = models.CharField(_("Field"), max_length=12, blank=True)
    #owner = models.ForeignKey(Party, blank=True, null=True, 
    #    related_name="owned_items", verbose_name=_('owner'))
    custodian = models.ForeignKey(Party, blank=True, null=True, 
        related_name="custody_items", verbose_name=_('custodian'))
    product = models.ForeignKey(Product, 
        limit_choices_to = {'stockable': True}, verbose_name=_('product'))
    inventory_date = models.DateField(_('inventory date'))
    expiration_date = models.DateField(_('expiration date'))
    planned = models.DecimalField(_("Ready"), max_digits=8, decimal_places=2, default=Decimal('0'))
    remaining = models.DecimalField(_('remaining'), max_digits=8, decimal_places=2, default=Decimal('0'),
        help_text=_('If you change Ready here, you most likely should also change Remaining. The Avail Update page changes Remaining automatically when you enter Ready, but this Admin form does not.'))
    received = models.DecimalField(_('received'), max_digits=8, decimal_places=2, default=Decimal('0'))
    onhand = models.DecimalField(_('onhand'), max_digits=8, decimal_places=2, default=Decimal('0'),
        help_text=_('If you change Received here, you most likely should also change Onhand. The Avail Update page changes Onhand automatically when you enter Received, but this Admin form does not.'))
    notes = models.CharField(_('notes'), max_length=64, blank=True)
    
    class Meta:
        ordering = ('product', 'producer', 'inventory_date')

    def __unicode__(self):
        return " ".join([
            self.producer.short_name,
            self.product.short_name,
            self.inventory_date.strftime('%Y-%m-%d')])

    def lot_id(self):
        if self.freeform_lot_id:
            return self.freeform_lot_id
        else:
            return " ".join([
                self.producer.member_id,
                self.producer.short_name,
                self.product.short_name,
                self.inventory_date.strftime('%Y-%m-%d')])

    def where(self):
        if self.custodian:
            return self.custodian
        else:
            return self.producer
    
    def avail_qty(self):
        if self.onhand:
            return self.onhand
        else:
            return self.remaining

    def qty(self):
        return self.avail_qty()
        
    def ordered_qty(self):
        return self.delivered_qty()

    def deliveries(self):
        return self.inventorytransaction_set.filter(transaction_type="Delivery")
        
    def delivered_qty(self):
        return sum(delivery.amount for delivery in self.deliveries())

    def issues(self):
        return self.inventorytransaction_set.filter(transaction_type="Issue")
        
    def issued_qty(self):
        return sum(delivery.amount for delivery in self.issues())

    def delivery_label(self):
        return " ".join([
            self.producer.short_name,
            'qty', str(self.avail_qty()),
            'at', self.inventory_date.strftime('%m-%d')])
            
    def pickup_label(self):
        return self.lot_id()
        
    def distributor(self):
        plans = ProductPlan.objects.filter(
            product = self.product,
            producer = self.producer,
            from_date__lte=self.inventory_date,
            to_date__gte=self.inventory_date)
        if plans:
            return plans[0].distributor
        else:
            return None
        
    def customers(self):
        buyers = []
        for delivery in self.deliveries():
            if delivery.order_item:
                buyers.append(delivery.order_item.order.customer.short_name)
        buyers = list(set(buyers))
        buyer_string = ", ".join(buyers)
        return buyer_string
            
    def update_from_transaction(self, qty): 
        """ update remaining or onhand

        Onhand trumps remaining.
        Qty could be positive or negative.
        """

        if self.onhand + self.received > Decimal('0'):
            # to deal with Django bug, fixed in 1.1
            onhand = Decimal(self.onhand)
            onhand += qty
            self.onhand = max([Decimal("0"), onhand])
            self.save()
        else:
            # to deal with Django bug, fixed in 1.1
            remaining = Decimal(self.remaining)
            #print self, "remaining:", remaining, "qty:", qty
            remaining += qty
            self.remaining = max([Decimal("0"), remaining])
            self.save()
                
    def save(self, *args, **kwargs):
        if not self.pk:
            if not self.expiration_date:
                self.expiration_date = self.inventory_date + datetime.timedelta(days=self.product.expiration_days)
        super(InventoryItem, self).save(*args, **kwargs)

# EconomicEventType is not ripe
#class EconomicEventType(models.Model):
#    name = models.CharField(max_length=255)

class EconomicEventManager(models.Manager):
    
    def get_query_set(self):
        return SubclassingQuerySet(self.model)

    def all_payments(self):
        events = EconomicEvent.raw_objects.all()
        payments = []
        for event in events:
            if isinstance(event.as_leaf_class(), Payment):
                payments.append(event)
        return payments

    def payments_to_party(self, party):
        events = EconomicEvent.raw_objects.filter(to_whom=party)
        payments = []
        for event in events:
            if isinstance(event.as_leaf_class(), Payment):
                payments.append(event)
        return payments

    def payments_from_party(self, party):
        events = EconomicEvent.raw_objects.filter(from_whom=party)
        payments = []
        for event in events:
            if isinstance(event.as_leaf_class(), Payment):
                payments.append(event)
        return payments

    def payments_to_members(self):
        fn = food_network()
        payments = Payment.objects.all().exclude(to_whom=fn)
        return payments

    def payments_from_members(self):
        fn = food_network()
        payments = Payment.objects.all().filter(to_whom=fn)
        return payments

class EconomicEvent(models.Model):
    transaction_date = models.DateField(_('transaction date'))
    from_whom = models.ForeignKey(Party, 
        related_name="given_events", verbose_name=_('from whom'))
    to_whom = models.ForeignKey(Party, 
        related_name="taken_events", verbose_name=_('to whom'))
    amount = models.DecimalField(_('amount'), max_digits=8, decimal_places=2)
    notes = models.CharField(_('notes'), max_length=64, blank=True)
    content_type = models.ForeignKey(ContentType,editable=False,null=True)

    raw_objects = models.Manager()
    objects = EconomicEventManager()

    def as_leaf_class(self):
        if self.content_type:
            content_type = self.content_type
            model = content_type.model_class()
            if (model == EconomicEvent):
                return self
            return model.objects.get(id=self.id)
        else:
            return self
        
    def save(self, *args, **kwargs):
        if not self.content_type:
            self.content_type = ContentType.objects.get_for_model(self.__class__)
        self.save_base(*args, **kwargs)

    def payments(self):
        if isinstance(self.as_leaf_class(), Payment):
            return []
        answer = []
        for d in self.transaction_payments.all():
            answer.append(d.payment)
        return answer

    def paid_amount(self):
        answer = False
        paid = Decimal("0")
        for payment in self.transaction_payments.all():
             paid += payment.amount_paid
        return paid.quantize(Decimal('.01'), rounding=ROUND_UP)

    def due_to_member(self):
        return self.as_leaf_class().due_to_member()

    def is_paid(self):
        return self.paid_amount() >= self.due_to_member()

    def payment_string(self):
        ps = []
        for payment in self.payments():
            ps.append(payment.as_string())
        ps = list(set(ps))
        ps_string = ", ".join(ps)
        return ps_string

    def delete_payments(self):
        for tp in self.transaction_payments.all():
            tp.delete()

        
class Payment(EconomicEvent):
    reference = models.CharField(_('reference'), max_length=64, blank=True)

    def __unicode__(self):
        amount_string = '$' + str(self.amount)
        return ' '.join([
            self.transaction_date.strftime('%Y-%m-%d'),
            self.to_whom.short_name,
            amount_string])

    class Meta:
        ordering = ('transaction_date',)

    def as_string(self):
        return self.__unicode__()

    def paid_transactions(self):
        paid = []
        for d in self.paid_events.all():
            paid.append(d.paid_event.as_leaf_class())
        return paid

    def paid_inventory_transactions(self):
        paid = []
        for p in self.paid_transactions():
            if isinstance(p, InventoryTransaction):
                paid.append(p)
        return paid

    def paid_service_transactions(self):
        paid = []
        for p in self.paid_transactions():
            if isinstance(p, ServiceTransaction):
                paid.append(p)
        return paid

    def paid_transportation_transactions(self):
        paid = []
        for p in self.paid_transactions():
            if isinstance(p, TransportationTransaction):
                paid.append(p)
        return paid

    def orders_paid(self):
        paid = []
        for cp in self.paid_orders.all():
            paid.append(cp.paid_order)
        return paid


class TransactionPayment(models.Model):
    """ Payment to Producer or Service provider
        for an EconomicEvent.
        In REA terms, this is a Duality
        but always assuming money in payment.
    """
    paid_event = models.ForeignKey(EconomicEvent, 
        related_name="transaction_payments", verbose_name=_('paid event'))
    payment = models.ForeignKey(Payment, 
        related_name="paid_events", verbose_name=_('payment'))
    amount_paid = models.DecimalField(_('amount paid'), max_digits=8, decimal_places=2)


ORDER_STATES = (
    ('Unsubmitted', _('Unsubmitted')),
    ('Submitted', _('Submitted')),
    ('Filled', _('Filled')),
    ('Paid', _('Paid')),
    ('Paid-Filled', _('Paid and Filled')),
    ('Filled-Paid', _('Filled and Paid')),
)


class Order(models.Model):
    customer = models.ForeignKey(Customer, verbose_name=_('customer'))
    purchase_order = models.CharField(_('purchase order'), max_length=64, blank=True)
    order_date = models.DateField(_('order date'))
    delivery_date = models.DateField(_('delivery date'))
    distributor = models.ForeignKey(Party, blank=True, null=True, 
        related_name="orders", verbose_name=_('distributor'))
    #todo: obsolete, or leave in for no-customer-app situations?
    paid = models.BooleanField(default=False, verbose_name=_("Order paid"))
    state = models.CharField(_('state'), max_length=16, choices=ORDER_STATES, default='Submitted', blank=True)
    product_list = models.ForeignKey(MemberProductList, blank=True, null=True,
        related_name="orders", verbose_name=_('product list'),
        help_text=_("Optional: The product list this order was created from. Maintained by customer."))
    created_by = models.ForeignKey(User, verbose_name=_('created by'),
        related_name='orders_created', blank=True, null=True)
    changed_by = models.ForeignKey(User, verbose_name=_('changed by'),
        related_name='orders_changed', blank=True, null=True)

    class Meta:
        ordering = ('order_date', 'customer')

    def __unicode__(self):
        date = self.delivery_date if self.delivery_date else self.order_date
        return ' '.join([date.strftime('%Y-%m-%d'), self.customer.short_name])

    def save(self, *args, **kwargs):
        if self.paid:
            self.set_paid_state()
        self.save_base(*args, **kwargs)
    
    def delete(self):
        #todo: is this necessary?  shd be cascaded, no?
        deliveries = InventoryTransaction.objects.filter(order_item__order=self) 
        for delivery in deliveries:
            delivery.delete()
        super(Order, self).delete()

    def is_paid(self):
        #todo: what about partials?
        if self.paid:
            return True
        if self.state == "Paid" or self.state == "Paid-Filled" or self.state == "Filled-Paid":
            return True
        return False

    def is_changeable(self):
        answer = False
        if self.state == "Unsubmitted" or self.state == "Submitted":
            if self.delivery_date == self.customer.next_delivery_date():
                answer = True
        return answer
    
    def delete_payments(self):
        for cp in self.customer_payments.all():
            cp.delete()
        if self.state == "Paid-Filled" or self.state == "Filled-Paid":
            self.state = "Filled"
        else:
            self.state = "Submitted"
        self.save()

    def is_delivered(self):
        #todo: what about partials?
        if self.state == "Filled" or self.state == "Paid-Filled" or self.state == "Filled-Paid":
            return True
        return False

    def register_delivery(self):
        if self.state.find("Filled") < 0:
            #print "registering delivery for order", self
            if self.state == "Paid":
                self.state = "Paid-Filled"
            else:
                self.state = "Filled"
            self.save()

    def set_paid_state(self):
        """ This method is for internal use
            (by order.save() and order.register_customer_payment())
            and so does not include self.save().
        """

        if self.state.find("Paid") < 0:
            if self.state == "Filled":
                self.state = "Filled-Paid"
            else:
                self.state = "Paid"
            return True
        else:
            return False

    def register_customer_payment(self):
        if self.set_paid_state():
            self.save()

    def transportation_fee(self):
        try:
            transportation_tx = TransportationTransaction.objects.get(order=self)
            return transportation_tx.amount.quantize(Decimal('.01'), rounding=ROUND_UP)
        except TransportationTransaction.DoesNotExist:
            return self.customer.transportation_fee().quantize(Decimal('.01'), rounding=ROUND_UP)
    
    def total_price(self):
        items = self.orderitem_set.all()
        total = Decimal("0")
        for item in items:
            total += item.extended_price()
            total += item.service_cost()
        return total.quantize(Decimal('.01'), rounding=ROUND_UP)
    
    def coop_fee(self):
        total = self.total_price()
        # todo: shd consider customer_fee_override?
        fee = customer_fee()
        answer = total * fee
        return answer.quantize(Decimal('.01'), rounding=ROUND_UP)
    
    def grand_total(self):
        return self.transportation_fee() + self.total_price() + self.coop_fee()
    
    def payment_due_date(self):
        term_days = customer_terms()
        return self.delivery_date + datetime.timedelta(days=term_days)
    
    def display_transportation_fee(self):
        return self.transportation_fee().quantize(Decimal('.01'), rounding=ROUND_UP)
    
    def customer_fee_label(self):
        fee = int(customer_fee() * 100)
        return "".join([str(fee), "% Administration Fee"])

    def short_items(self):
        shorts = []
        for item in self.orderitem_set.all():
            if item.qty_short():
                shorts.append(item)
        return shorts


class CustomerPayment(models.Model):
    """ Payment from a Customer to FoodNetwork
        for a delivered Order.
        In REA terms, this is a Duality
        where the Order is a bundle of EconomicEvents
        and assuming money in payment.
    """
    paid_order = models.ForeignKey(Order, 
        related_name="customer_payments", verbose_name=_('paid order'))
    payment = models.ForeignKey(Payment, 
        related_name="paid_orders", verbose_name=_('payment'))
    amount_paid = models.DecimalField(_('amount paid'), max_digits=8, decimal_places=2)

    def __unicode__(self):
        amount_string = '$' + str(self.amount_paid)
        return ' '.join([
            "From:", self.payment.from_whom.short_name,
            "Order:", str(self.paid_order.id),
            "Paid:", self.payment.transaction_date.strftime('%Y-%m-%d'),
            amount_string])
        

class ShortOrderItems(object):
    def __init__(self, product, total_avail, total_ordered, quantity_short, order_items):
         self.product = product
         self.total_avail = total_avail
         self.total_ordered = total_ordered
         self.quantity_short = quantity_short
         self.order_items = order_items

#todo: check this out
# shorts shd use total_avail meaning all remaining, not reduced by ordered
# total_ordered shd mean unfilled within avail date range
def shorts_for_date(delivery_date):
    shorts = []
    maybes = {}
    ois = OrderItem.objects.filter(order__delivery_date=delivery_date).exclude(order__state="Unsubmitted")
    for oi in ois:
        if not oi.product in maybes:
            maybes[oi.product] = ShortOrderItems(oi.product, 
                oi.product.total_avail(delivery_date), Decimal("0"), Decimal("0"), [])
        maybes[oi.product].total_ordered += (oi.quantity -oi.delivered_quantity())    
        maybes[oi.product].order_items.append(oi)
    for maybe in maybes:
        qty_short = maybes[maybe].total_ordered - maybes[maybe].total_avail
        if qty_short > Decimal("0"):
            maybes[maybe].quantity_short = qty_short
            shorts.append(maybes[maybe])
    return shorts

#todo: check this out
#see above shorts_for_date
#plus, shorts for week shd probly be shorts_for_delivery_cycle
def shorts_for_week():
    cw = next_delivery_date()
    monday = cw - datetime.timedelta(days=datetime.date.weekday(cw))
    saturday = monday + datetime.timedelta(days=5)
    shorts = []
    maybes = {}
    ois = OrderItem.objects.filter(order__delivery_date__range=(cw, saturday)).exclude(order__state="Unsubmitted")
    for oi in ois:
        if not oi.product in maybes:
            maybes[oi.product] = ShortOrderItems(oi.product, 
                oi.product.total_avail(oi.order.delivery_date), Decimal("0"), Decimal("0"), [])
        maybes[oi.product].total_ordered += (oi.quantity -oi.delivered_quantity())    
        maybes[oi.product].order_items.append(oi)
    for maybe in maybes:
        qty_short = maybes[maybe].total_ordered - maybes[maybe].total_avail
        if qty_short > Decimal("0"):
            maybes[maybe].quantity_short = qty_short
            shorts.append(maybes[maybe])
    return shorts


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name=_('order'))
    product = models.ForeignKey(Product, verbose_name=_('product'))
    quantity = models.DecimalField(_('quantity'), max_digits=8, decimal_places=2)
    #orig_qty = models.DecimalField(_('orig qty'), max_digits=8, decimal_places=2, default=Decimal('0'))
    unit_price = models.DecimalField(_('unit price'), max_digits=8, decimal_places=2)
    fee = models.DecimalField(_('fee'), max_digits=3, decimal_places=2, default=Decimal('0'),
        help_text=_('Fee is a decimal fraction, not a percentage - for example, .05 instead of 5%'))
    notes = models.CharField(_('notes'), max_length=64, blank=True)

    def __unicode__(self):
        return ' '.join([
            str(self.order),
            self.product.short_name,
            str(self.quantity)])
    
    def delete(self):
        #todo: is this necessary? shd be cascaded, no?
        deliveries = self.inventorytransaction_set.all()
        for delivery in deliveries:
            delivery.delete()
        super(OrderItem, self).delete()

    #todo: check this out
    def total_avail(self):
        """
        means quantity available on delivery_date, not reduced by orders
        """
        return self.product.total_avail(self.order.delivery_date)

    #todo: check this out
    def total_ordered(self):
        return self.product.total_ordered(self.order.delivery_date)

    #todo: check this out
    # shorts shd use total_avail meaning all remaining, not reduced by ordered
    # total_ordered shd mean unfilled within avail date range
    #but where is this used?
    #does it mean qty_short per product, or for this orderItem?
    #(in order_confirmation, looks like it means for this orderItem)
    #if per product, shd not be here...
    #note: see short_adjusted_qty below
    def qty_short(self):
        avail = self.total_avail()
        ordered = self.total_ordered()
        if ordered > avail:
            return ordered - avail
        else:
            return Decimal("0")

    #todo: check this out
    #seems wrong, because qty_short looks like per product, not this orderItem
    #but maybe it's ok as used in order_confirmation?
    def short_adjusted_qty(self):
        return self.quantity - self.qty_short()

    def short_adjusted_extended_price(self):
        answer = self.short_adjusted_qty() * self.unit_price
        return answer.quantize(Decimal('.01'), rounding=ROUND_UP)

    def qty_before_staff_short_change(self):
        #todo: consider customer unforced changes after staff short change?
        staff_short_changes = self.order_item_changes.filter(
            reason=3)
        if staff_short_changes:
            return staff_short_changes[0].prev_qty
        else:
            return None

    def orig_qty(self):
        return self.qty_before_staff_short_change()

    def producers(self):
        txs = self.inventorytransaction_set.all()
        producers = []
        for tx in txs:
            producers.append(tx.inventory_item.producer.short_name)
        return ', '.join(list(set(producers)))
    
    def services(self):
        svs = []
        try:
            deliveries = self.inventorytransaction_set.all()
            for delivery in deliveries:
                svs.extend(delivery.services())
        except:
            pass
        return svs
    
    def service_cost(self):
        cost = Decimal(0)
        for delivery in self.inventorytransaction_set.all():
            cost += delivery.invoiced_service_cost()
        return cost.quantize(Decimal('.01'))
    
    def processors(self):
        procs = []
        for svc in self.services():
            procs.append(svc.from_whom.short_name)
        procs = list(set(procs))
        return ", ".join(procs)
    
    def distributor(self):
        delivery_date = self.order.delivery_date
        plans = ProductPlan.objects.filter(
            product = self.product,
            producer = self.producer,
            from_date__lte=delivery_date,
            to_date__gte=delivery_date)
        if plans:
            return plans[0].distributor
        else:
            return None
    
    def extended_price(self):
        answer = self.quantity * self.unit_price
        # todo: think about this, is it correct?
        #if self.processing():
        #    answer += self.processing().cost
        return answer.quantize(Decimal('.01'), rounding=ROUND_UP)
    
    def lot(self):
        #todo:
        # this is a hack
        # PBC's order_by_lot means one delivery InventoryTransaction
        # and thus one InventoryItem per OrderItem
        deliveries = self.inventorytransaction_set.all()
        if deliveries.count():
            delivery = deliveries[0]
            item = delivery.inventory_item
            return item
        else:
            return None
    
    def delivered_quantity(self):
        return sum(tx.amount for tx in self.inventorytransaction_set.all())

    def unfilled_quantity(self):
        return self.quantity - self.delivered_quantity()
        
    def producer_fee(self):
        return producer_fee()
    
    def extended_producer_fee(self):
        answer = self.quantity * self.unit_price * producer_fee()
        return answer.quantize(Decimal('.01'), rounding=ROUND_UP)
    
    def formatted_unit_price(self):
        return self.unit_price.quantize(Decimal('.01'), rounding=ROUND_UP)

    def customer_fee(self):
        return customer_fee()

    class Meta:
        ordering = ('order', 'product',)


ACTION_CHOICES = (
    (1, _('Add')),
    (2, _('Change')),
    (3, _('Delete')),
)

REASON_CHOICES = (
    (1, _('Customer unforced change')),
    (2, _('Customer short change')),
    (3, _('Staff short change')),
    (4, _('Customer order deletion')),
)

class OrderItemChange(models.Model):
    action = models.PositiveSmallIntegerField(_('action'), max_length="1",
        choices=ACTION_CHOICES)
    reason = models.PositiveSmallIntegerField(_('reason'), max_length="1",
        choices=REASON_CHOICES)
    when_changed = models.DateTimeField(_('when changed'), auto_now_add=True)
    changed_by = models.ForeignKey(User, verbose_name=_('changed by'),
        related_name='order_items_changed', blank=True, null=True)
    order = models.ForeignKey(Order, verbose_name=_('order'),
        related_name="order_changes", blank=True, null=True)
    customer = models.ForeignKey(Customer, verbose_name=_('customer'),
        related_name="order_changes")
    order_item = models.ForeignKey(OrderItem, verbose_name=_('order_item'),
        related_name="order_item_changes", blank=True, null=True)
    product = models.ForeignKey(Product, verbose_name=_('product'),
        related_name="order_item_changes")
    prev_qty = models.DecimalField(_('prev qty'), max_digits=8,
        decimal_places=2, default=Decimal('0'))
    new_qty = models.DecimalField(_('new qty'), max_digits=8, 
        decimal_places=2, default=Decimal('0'))
    prev_notes = models.CharField(_('prev notes'), max_length=64, blank=True)
    new_notes = models.CharField(_('new notes'), max_length=64, blank=True)


class ServiceType(models.Model):
    name = models.CharField(_('name'), max_length=64)
    invoiced_separately = models.BooleanField(_('invoiced separately'), default=False,
        help_text=_('If checked, the cost of services appear as separate line items on invoices. If not, they are included in the prices of resulting products.'))
    pay_provider_on_terms = models.BooleanField(_('pay provider on terms'), default=True,
        help_text=_('If checked, the Food Network pays the service provider on member terms. If not, the provider payment is based on customer order payment.'))

    def __unicode__(self):
        return self.name


class ProcessType(models.Model):
    name = models.CharField(_('name'), max_length=64)
    input_type = models.ForeignKey(Product, 
        related_name='input_types', verbose_name=_('input type'))
    use_existing_input_lot = models.BooleanField(_('use existing input lot'), default=True)
    number_of_processing_steps = models.IntegerField(_('number of processing steps'), default=1)
    output_type = models.ForeignKey(Product, 
        related_name='output_types', verbose_name=_('output type'))
    number_of_output_lots = models.IntegerField(_('number of output lots'), default=1)
    notes = models.TextField(_('notes'), blank=True)

    def __unicode__(self):
        return self.name


def previous_process_collector(process, collector):
    for proc in process.previous_processes():
        collector.append(proc)
        previous_process_collector(proc, collector)
    return collector


class Process(models.Model):
    process_type = models.ForeignKey(ProcessType)
    process_date = models.DateField()
    managed_by = models.ForeignKey(Party, related_name="managed_processes",
         verbose_name=_('managed by'), blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ('process_date',)
        verbose_name_plural = "Processes"

    def __unicode__(self):
        return " ".join([
            self.process_type.name,
            self.input_lot_id()
            #self.process_date.strftime('%Y-%m-%d')
            ])


    def inputs(self):
        return self.inventory_transactions.filter(transaction_type="Issue")

    def outputs(self):
        return self.inventory_transactions.filter(transaction_type="Production")

    def services(self):
        return self.service_transactions.all()

    def invoiced_services(self):
        return self.service_transactions.filter(service_type__invoiced_separately=True)

    def input_lot_id(self):
        inputs = self.inventory_transactions.filter(transaction_type="Issue")
        try:
            return inputs[0].inventory_item.lot_id()
        except:
            return ""

    def output_lot_ids(self):
        answer = ""
        outputs = self.inventory_transactions.filter(transaction_type="Production")
        lot_ids = []
        for output in outputs:
            lot_ids.append(output.inventory_item.lot_id())
        answer = ", ".join(lot_ids)
        return answer

    def next_processes(self):
        processes = []
        for output in self.outputs():
            lot = output.inventory_item
            for issue in lot.inventorytransaction_set.filter(transaction_type="Issue"):
                if issue.process:
                    processes.append(issue.process)
        return processes

    def previous_processes_recursive(self):
        processes = previous_process_collector(self, []) 
        return processes 

    def previous_processes(self):
        processes = []
        for inp in self.inputs():
            lot = inp.inventory_item
            for tx in lot.inventorytransaction_set.filter(transaction_type="Production"):
                if tx.process:
                    processes.append(tx.process)
        return processes 

    def previous_process(self):       
        # for PBC now, processes will have one or None previous_processes
        processes = self.previous_processes()
        if processes:
            return processes[0]
        else:
            return None

    def service_cost(self):
        cost = Decimal("0")
        for s in self.services():
            cost += s.amount
        return cost

    def invoiced_service_cost(self):
        cost = Decimal("0")
        for s in self.invoiced_services():
            cost += s.amount
        return cost

    def unit_service_cost(self):
        """ Allocating the same cost to each output unit 
        """
        cost = self.service_cost()
        output = sum(op.amount for op in self.outputs())
        return cost / output

    def cumulative_service_cost(self):
        cost = self.service_cost()
        for proc in self.previous_processes_recursive():
            cost += proc.service_cost()
        return cost

    def cumulative_unit_service_cost(self):
        """ Allocating the same cost to each output unit 
        """
        cost = self.cumulative_service_cost()
        output = sum(op.amount for op in self.outputs())
        return cost / output

    def cumulative_invoiced_service_cost(self):
        cost = self.invoiced_service_cost()
        for proc in self.previous_processes_recursive():
            cost += proc.invoiced_service_cost()
        return cost

    def cumulative_invoiced_unit_service_cost(self):
        """ Allocating the same cost to each output unit 
        """
        cost = self.cumulative_invoiced_service_cost()
        output = sum(op.amount for op in self.outputs())
        return cost / output

    def cumulative_services(self):
        svs = list(self.services())
        for proc in self.previous_processes_recursive():
            svs.extend(proc.services())
        return svs

    def is_deletable(self):
        answer = True
        for output in self.outputs():
            lot = output.inventory_item
            other_types = ["Issue", "Delivery", "Damage", "Reject", "Receipt", "Transfer"]
            if lot.inventorytransaction_set.filter(transaction_type__in=other_types).count() > 0:
                answer = False
        return answer


TX_TYPES = (
    ('Receipt', _('Receipt')),         # inventory was received from outside the system
    ('Delivery', _('Delivery')),       # inventory was delivered to a customer
    ('Transfer', _('Transfer')),       # combination delivery and receipt inside the system
    ('Issue', _('Issue')),             # a process consumed inventory
    ('Production', _('Production')),   # a process created inventory
    ('Damage', _('Damage')),           # inventory was damaged and must be paid for
    ('Reject', _('Reject')),           # inventory was rejected by a customer and does not need to be paid for
)

class InventoryTransaction(EconomicEvent):
    transaction_type = models.CharField(_('transaction type'), max_length=10, choices=TX_TYPES, default='Delivery')
    inventory_item = models.ForeignKey(InventoryItem, verbose_name=_('inventory item'))
    process = models.ForeignKey(Process, blank=True, null=True, 
        related_name='inventory_transactions', verbose_name=_('process'))
    order_item = models.ForeignKey(OrderItem, 
        blank=True, null=True, verbose_name=_('order item'))
    unit_price = models.DecimalField(_('unit price'), max_digits=8, decimal_places=2)

    def __unicode__(self):
        if self.order_item:
            label = ' '.join(['Order Item:', str(self.order_item)])
        else:
            label = ' '.join(['Type:', self.transaction_type])
        return " ".join([
            label, 
            'Inventory Item:', str(self.inventory_item), 
            'Qty:', str(self.amount)])
        
    def save(self, *args, **kwargs):
        initial_qty = Decimal("0")
        if self.pk:
            prev_state = InventoryTransaction.objects.get(pk=self.pk)
            initial_qty = prev_state.amount
        else:
            if self.order_item:
                self.unit_price = self.order_item.unit_price
            else:
                self.unit_price = self.inventory_item.product.price
        super(InventoryTransaction, self).save(*args, **kwargs)
        qty_delta = self.amount - initial_qty
        if self.transaction_type=="Receipt" or self.transaction_type=="Production":
            self.inventory_item.update_from_transaction(qty_delta)
        else:
            self.inventory_item.update_from_transaction(-qty_delta)
        if self.order_item:
            if self.transaction_type=="Delivery":
                self.order_item.order.register_delivery()
        
    def delete(self):
        #todo: admin deletes do not call this delete method
        # need a signal or something...
        if self.transaction_type=="Receipt" or self.transaction_type=="Production":
            self.inventory_item.update_from_transaction(-self.amount)
        else:
            self.inventory_item.update_from_transaction(self.amount)
        super(InventoryTransaction, self).delete()
        
    def order_customer(self):
        return self.order_item.order.customer
    
    def product(self):
        return self.inventory_item.product
    
    def producer(self):
        return self.inventory_item.producer
    
    def inventory_date(self):
        return self.inventory_item.inventory_date
    
    def due_to_member(self):
        if self.transaction_type=='Reject' or self.transaction_type=="Production" :
            return Decimal(0)
        if not self.inventory_item.product.pay_producer:
            return Decimal(0)
        
        fee = producer_fee()
        #unit_price = self.unit_price
        return (self.unit_price * self.amount * (1 - fee)).quantize(Decimal('.01'), rounding=ROUND_UP)

    def is_due(self):
        if not self.due_to_member():
            return False
        if self.inventory_item.product.pay_producer_on_terms:
            term_days = member_terms()
            due_date = self.transaction_date + datetime.timedelta(days=term_days)
            if datetime.date.today() >= due_date:
                return True
            else:
                return False
        else:
            if self.order_item:
                return self.order_item.order.is_paid()
            else:
                return False

    def should_be_paid(self):
        if self.is_paid():
            return False
        return self.is_due()

    def extended_producer_fee(self):
        # todo: this is wrong, but not sure why it was done this way
        # shd investigate more sometime, but for now, just fix
        #if self.order_item:
        #    return self.order_item.extended_producer_fee()
        #else:
        #    unit_price = self.unit_price
        #    answer = self.amount * unit_price * producer_fee()
        #    return answer.quantize(Decimal('.01'), rounding=ROUND_UP)
        price = self.unit_price
        if self.order_item:
            price = self.order_item.unit_price
        answer = self.amount * price * producer_fee()
        return answer.quantize(Decimal('.01'), rounding=ROUND_UP)
    
    def service_cost(self):
        cost = Decimal(0)
        item = self.inventory_item
        for tx in item.inventorytransaction_set.filter(transaction_type="Production"):
            cost += self.amount * tx.process.cumulative_unit_service_cost()
        return cost

    def invoiced_service_cost(self):
        cost = Decimal(0)
        item = self.inventory_item
        for tx in item.inventorytransaction_set.filter(transaction_type="Production"):
            cost += self.amount * tx.process.cumulative_invoiced_unit_service_cost()
        return cost

    def services(self):
        svs = []
        item = self.inventory_item
        for tx in item.inventorytransaction_set.filter(transaction_type="Production"):
            svs.extend(list(tx.process.cumulative_services()))
        return svs

    class Meta:
        ordering = ('-transaction_date',)


class ServiceTransaction(EconomicEvent):
    service_type = models.ForeignKey(ServiceType, verbose_name=_('service type'))
    process = models.ForeignKey(Process, 
        related_name='service_transactions', verbose_name=_('process'))


    def __unicode__(self):
        return " ".join([
            self.service_type.name,
            self.from_whom.long_name,
            ])

    def order_paid(self):
        # todo: shd be recursive for next processes?
        for output in self.process.outputs():
            for delivery in output.inventory_item.deliveries():
                if delivery.order_item.order.is_paid():
                    return True
        return False

    def is_due(self):
        if self.service_type.pay_provider_on_terms:
            term_days = member_terms()
            due_date = self.transaction_date + datetime.timedelta(days=term_days)
            if datetime.date.today() >= due_date:
                return True
            else:
                return False
        else:
            return self.order_paid()

    def should_be_paid(self):
        if self.is_paid():
            return False
        return self.is_due()


    def downstream_orders(self):
        # todo: shd be recursive for next processes
        orders = []
        for output in self.process.outputs():
            for delivery in output.inventory_item.deliveries():
                orders.append(delivery.order_item.order)
        return orders
        
    def order_string(self):
        os = []
        for order in self.downstream_orders():
            os.append("".join([" #", str(order.id), ":", order.customer.short_name]))
        os = list(set(os))
        os_string = ", ".join(os)
        return os_string

    def delivered_items(self):
        # todo: shd be recursive for next processes
        items = []
        for output in self.process.outputs():
            items.append(output.inventory_item)
        return items

    def product_string(self):
        ps = []
        for item in self.delivered_items():
            ps.append(item.product.short_name)
        ps = list(set(ps))
        ps_string = ", ".join(ps)
        return ps_string

    def due_to_member(self):
        return self.amount.quantize(Decimal('.01'), rounding=ROUND_UP)


class TransportationTransaction(EconomicEvent):
    service_type = models.ForeignKey(ServiceType, verbose_name=_('service type'))
    order = models.ForeignKey(Order, verbose_name=_('order'))

    def __unicode__(self):
        return " ".join([
            self.service_type.name,
            self.from_whom.long_name,
            "for",
            unicode(self.order),
            ])

    def save(self, *args, **kwargs):
        if not self.pk:
            tt, created = ServiceType.objects.get_or_create(name="Transportation")
            self.service_type = tt
        super(TransportationTransaction, self).save(*args, **kwargs)

    def should_be_paid(self):
        if self.is_paid():
            return False
        return self.order.is_paid()

    def is_due(self):
        return self.order.is_paid()

    def due_to_member(self):
        return self.amount.quantize(Decimal('.01'), rounding=ROUND_UP)


DAY_CHOICES =  ( 
    (1, _('Monday')),
    (2, _('Tuesday')),
    (3, _('Wednesday')),
    (4, _('Thursday')),
    (5, _('Friday')),
    (6, _('Saturday')),
    (7, _('Sunday')),
)

class DeliveryCycle(models.Model):
    delivery_day = models.PositiveSmallIntegerField(_('delivery day'), max_length="1", choices=DAY_CHOICES)
    route = models.CharField(_('route'), max_length=255)
    order_closing_day = models.PositiveSmallIntegerField(_('order closing day'), max_length="1", choices=DAY_CHOICES)
    order_closing_time = models.TimeField()
    customers = models.ManyToManyField(Customer,
        through="CustomerDeliveryCycle", verbose_name=_('customers'))

    class Meta:
        ordering = ('delivery_day',)

    def __unicode__(self):
        return " ".join([
            self.get_delivery_day_display(),
            self.route,
        ])

    def customer_list(self):
        return ", ".join(c.short_name for c in self.customers.all())

    def next_delivery_date(self, date=None):
        if not date:
            date = datetime.date.today()
        monday = date - datetime.timedelta(days=datetime.date.weekday(date))
        dd = monday + datetime.timedelta(days=(self.delivery_day - 1))
        if dd <= date:
            dd = dd + datetime.timedelta(days=7)
        return dd

    def next_delivery_date_using_closing(self, date_and_time=None):
        if not date_and_time:
            date_and_time = datetime.datetime.now()
        #import pdb; pdb.set_trace()
        dd = self.next_delivery_date(date_and_time.date())
        while date_and_time > self.order_closing(dd):
            dd = dd + datetime.timedelta(days=1)
            dd = self.next_delivery_date(dd)
        return dd

    def order_closing(self, delivery_date):
        dd = self.delivery_day
        ocd = self.order_closing_day
        if dd < ocd:
            dd = dd + 7
        offset = dd - ocd
        closing_date = delivery_date - datetime.timedelta(days=offset)
        return datetime.datetime.combine(closing_date, self.order_closing_time)


class CustomerDeliveryCycle(models.Model):
    customer = models.ForeignKey(Customer, related_name="delivery_cycles",
                                 verbose_name=_('customer'))
    delivery_cycle = models.ForeignKey(DeliveryCycle,
        related_name="delivery_customers", verbose_name=_('delivery cycle'))

    class Meta:
        unique_together = ("customer", "delivery_cycle")
        
