import datetime
import time
import csv
from operator import attrgetter

from django.db.models import Q
from django.http import Http404
from django.views.generic import list_detail
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.template import RequestContext
from django.http import HttpResponse
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.core.exceptions import MultipleObjectsReturned
from django.core.mail import send_mail
from django.utils import simplejson

from models import *
from forms import *
from view_helpers import *
from utils import DojoDataJSONResponse, serialize

try:
    from notification import models as notification
except ImportError:
    notification = None

# Several of the views here are based on
# http://collingrady.com/2008/02/18/editing-multiple-objects-in-django-with-newforms/
# Could now be switched to use formsets.

@login_required
def send_fresh_list(request):
    if request.method == "POST":
        if notification:
            try:
                fn = food_network()
                food_network_name = fn.long_name
            except FoodNetwork.DoesNotExist:
                return render_to_response('distribution/network_error.html')

            if fn:
                week_of = current_week()
                fresh_list = fn.fresh_list()
                users = list(Customer.objects.all())
                users.append(fn)
                nt = NoticeType.objects.get(label='distribution_fresh_list')
                intro = EmailIntro.objects.filter(notice_type=nt)[0]
                notification.send(users, "distribution_fresh_list", {
                    "intro": intro.message,
                    "fresh_list": fresh_list, 
                    "week_of": week_of,
                    "food_network_name": food_network_name,
                })
                request.user.message_set.create(message="Fresh List emails have been sent")
        return HttpResponseRedirect(request.POST["next"])
    
@login_required
def send_pickup_list(request):
    if request.method == "POST":
        if notification:
            try:
                fn = food_network()
                food_network_name = fn.long_name
            except FoodNetwork.DoesNotExist:
                return render_to_response('distribution/network_error.html')

            if fn:
                pickup_date = current_week()
                pickup_list = fn.pickup_list()
                for pickup in pickup_list:
                    dist = pickup_list[pickup]
                    item_list = dist.custodians.values()
                    item_list.sort(lambda x, y: cmp(x.custodian, y.custodian))   
                    users = [dist, fn]
                    notification.send(users, "distribution_pickup_list", {
                            "pickup_list": item_list, 
                            "pickup_date": pickup_date,
                            "distributor": dist.distributor})
                request.user.message_set.create(message="Pickup List emails have been sent")
        return HttpResponseRedirect(request.POST["next"])
    
@login_required
def send_delivery_list(request):
    if request.method == "POST":
        if notification:
            try:
                fn = food_network()
                food_network_name = fn.long_name
            except FoodNetwork.DoesNotExist:
                return render_to_response('distribution/network_error.html')

            if fn:
                delivery_date = current_week()
                delivery_list = fn.delivery_list()
                for distributor in delivery_list:
                    dist = delivery_list[distributor]
                    order_list = dist.customers.values()
                    order_list.sort(lambda x, y: cmp(x.customer, y.customer))
                    users = [dist, fn]
                    notification.send(users, "distribution_order_list", {
                            "order_list": order_list, 
                            "order_date": delivery_date,
                            "distributor": dist.distributor})
                request.user.message_set.create(message="Order List emails have been sent")
        return HttpResponseRedirect(request.POST["next"])

@login_required
def send_order_notices(request):
    if request.method == "POST":
        if notification:
            try:
                fn = food_network()
                food_network_name = fn.long_name
            except FoodNetwork.DoesNotExist:
                return render_to_response('distribution/network_error.html')

            if fn:
                thisdate = current_week()
                weekstart = thisdate - datetime.timedelta(days=datetime.date.weekday(thisdate))
                weekend = weekstart + datetime.timedelta(days=5)
                order_list = Order.objects.filter(delivery_date__range=(weekstart, weekend))
                for order in order_list:
                    users = [order.customer, fn]
                    notification.send(users, "distribution_order_notice", {
                            "order": order, 
                            "order_date": thisdate})
                request.user.message_set.create(message="Order Notice emails have been sent")
        return HttpResponseRedirect(request.POST["next"])


def json_customer_info(request, customer_id):
    # Note: serializer requires an iterable, not a single object. Thus filter rather than get.
    data = serializers.serialize("json", Party.objects.filter(pk=customer_id))
    return HttpResponse(data, mimetype="text/json-comment-filtered")


def json_producer_info(request, producer_id):
    data = serializers.serialize("json", Party.objects.filter(pk=producer_id))
    return HttpResponse(data, mimetype="text/json-comment-filtered")

#@login_required
def plan_selection(request):
    #import pdb; pdb.set_trace()
    from_date = datetime.date.today()
    # force from_date to Monday, to_date to Sunday
    from_date = from_date - datetime.timedelta(days=datetime.date.weekday(from_date))
    to_date = from_date + datetime.timedelta(weeks=16)
    to_date = to_date - datetime.timedelta(days=datetime.date.weekday(to_date)+1)
    to_date = to_date + datetime.timedelta(days=7)
    plan_init = {
        'plan_from_date': from_date,
        'plan_to_date': to_date,
        'list_type': 'M',
    }
    init = {
        'from_date': from_date,
        'to_date': to_date,
    }

    if request.method == "POST":
        if request.POST.get('submit-supply-demand'):
            sdform = DateRangeSelectionForm(prefix='sd', data=request.POST)  
            if sdform.is_valid():
                data = sdform.cleaned_data
                from_date = data['from_date'].strftime('%Y_%m_%d')
                to_date = data['to_date'].strftime('%Y_%m_%d')
                return HttpResponseRedirect('/%s/%s/%s/'
                    % ('distribution/dojosupplydemand', from_date, to_date))
            else:
                psform = PlanSelectionForm(initial=plan_init)
                income_form = DateRangeSelectionForm(prefix = 'inc', initial=init)

        elif request.POST.get('submit-income'):
            income_form = DateRangeSelectionForm(prefix='inc', data=request.POST)  
            if income_form.is_valid():
                data = income_form.cleaned_data
                from_date = data['from_date'].strftime('%Y_%m_%d')
                to_date = data['to_date'].strftime('%Y_%m_%d')
                return HttpResponseRedirect('/%s/%s/%s/'
                    % ('distribution/dojoincome', from_date, to_date))
            else:
                psform = PlanSelectionForm(initial=plan_init)
                sdform = DateRangeSelectionForm(prefix='sd', initial=init)
      
        else:
            psform = PlanSelectionForm(request.POST)  
            if psform.is_valid():
                psdata = psform.cleaned_data
                member_id = psdata['member']
                from_date = psdata['plan_from_date'].strftime('%Y_%m_%d')
                to_date = psdata['plan_to_date'].strftime('%Y_%m_%d')
                list_type = psdata['list_type']
                return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
                   % ('distribution/dojoplanningtable', member_id, list_type, from_date, to_date))
            else:
                sdform = DateRangeSelectionForm(prefix='sd', initial=init)
                income_form = DateRangeSelectionForm(prefix = 'inc', initial=init)

    else:
        psform = PlanSelectionForm(initial=plan_init)
        sdform = DateRangeSelectionForm(prefix='sd', initial=init)
        income_form = DateRangeSelectionForm(prefix = 'inc', initial=init)
    return render_to_response('distribution/plan_selection.html', 
            {'plan_form': psform,
             'sdform': sdform,
             'income_form': income_form,
            }, context_instance=RequestContext(request))

@login_required
def planning_table(request, member_id, list_type, from_date, to_date):
    try:
        member = Party.objects.get(pk=member_id)
    except Party.DoesNotExist:
        raise Http404
    role = "producer"
    plan_type = "Production"
    if member.is_customer():
        role = "consumer"
        plan_type = "Consumption"

    try:
        from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
        to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    # force from_date to Monday, to_date to Sunday
    from_date = from_date - datetime.timedelta(days=datetime.date.weekday(from_date))
    to_date = to_date - datetime.timedelta(days=datetime.date.weekday(to_date)+1)
    to_date = to_date + datetime.timedelta(days=7)
    products = None
    if list_type == "M":
        if role == "consumer":
            products = CustomerProduct.objects.filter(customer=member, planned=True)
        else:
            products = ProducerProduct.objects.filter(producer=member, planned=True)
    if not products:
        products = Product.objects.filter(plannable=True)
        list_type = "A"
    plan_table = plan_weeks(member, products, from_date, to_date)
    #import pdb; pdb.set_trace()
    forms = create_weekly_plan_forms(plan_table.rows, data=request.POST or None)
    if request.method == "POST":
        for row in forms:
            if row.formset.is_valid():
                for form in row.formset.forms:
                    data = form.cleaned_data
                    qty = data['quantity']
                    plan_id = data['plan_id']
                    from_dt = data['from_date']
                    to_dt = data['to_date']
                    product_id = data['product_id']
                    plan = None
                    if plan_id:
                        # what if plan was changed by prev cell?
                        plan = ProductPlan.objects.get(id=plan_id)
                        if plan.to_date < from_dt or plan.from_date > to_dt:
                            plan = None
                    if qty:
                        if plan:
                            if not qty == plan.quantity:
                                if plan.from_date >= from_dt and plan.to_date <= to_dt:
                                    plan.quantity = qty
                                    plan.save()
                                else:
                                    if plan.from_date < from_dt:
                                        new_to_dt = from_dt - datetime.timedelta(days=1)
                                        earlier_plan = ProductPlan(
                                            member=plan.member,
                                            product=plan.product,
                                            quantity=plan.quantity,
                                            from_date=plan.from_date,
                                            to_date=new_to_dt,
                                            role=plan.role,
                                            inventoried=plan.inventoried,
                                            distributor=plan.distributor,
                                        )
                                        earlier_plan.save()
                                    if plan.to_date > to_dt:
                                        new_plan = ProductPlan(
                                            member=plan.member,
                                            product=plan.product,
                                            quantity=qty,
                                            from_date=from_dt,
                                            to_date=to_dt,
                                            role=plan.role,
                                            inventoried=plan.inventoried,
                                            distributor=plan.distributor,
                                        )
                                        new_plan.save()
                                        plan.from_date = to_dt + datetime.timedelta(days=1)
                                        plan.save()
                                    else:
                                        plan.from_date=from_dt
                                        plan.quantity=qty
                                        plan.save()      
                        else:
                            product = Product.objects.get(id=product_id)
                            new_plan = ProductPlan(
                                member=member,
                                product=product,
                                quantity=qty,
                                from_date=from_dt,
                                to_date=to_dt,
                                role=role,
                            )
                            new_plan.save()
                            if role == "producer":
                                listed_product, created = ProducerProduct.objects.get_or_create(
                                    product=product, producer=member)
                            elif role == "consumer":
                                listed_product, created = CustomerProduct.objects.get_or_create(
                                    product=product, customer=member)

                    else:
                        if plan:
                            if plan.from_date >= from_dt and plan.to_date <= to_dt:
                                plan.delete()
                            else:
                                if plan.to_date > to_dt:
                                    early_from_dt = plan.from_date              
                                    if plan.from_date < from_dt:
                                        early_to_dt = from_dt - datetime.timedelta(days=1)
                                        earlier_plan = ProductPlan(
                                            member=plan.member,
                                            product=plan.product,
                                            quantity=plan.quantity,
                                            from_date=early_from_dt,
                                            to_date=early_to_dt,
                                            role=plan.role,
                                            inventoried=plan.inventoried,
                                            distributor=plan.distributor,
                                         )
                                        earlier_plan.save()
                                    plan.from_date = to_dt + datetime.timedelta(days=1)
                                    plan.save()
                                else:
                                    plan.to_date= from_dt - datetime.timedelta(days=1)
                                    plan.save()
        from_date = from_date.strftime('%Y_%m_%d')
        to_date = to_date.strftime('%Y_%m_%d')
        return HttpResponseRedirect('/%s/%s/%s/%s/'
                    % ('distribution/membersupplydemand', from_date, to_date, member_id))
    return render_to_response('distribution/planning_table.html', 
        {
            'from_date': from_date,
            'to_date': to_date,
            'plan_table': plan_table,
            'forms': forms,
            'plan_type': plan_type,
            'member': member,
            'list_type': list_type,
            'tabnav': "distribution/tabnav.html",
        }, context_instance=RequestContext(request))

# todo: needs 2 views, this one to present the page,
# the other to respond to the JsonRestStore
@login_required
def dojo_planning_table(request, member_id, list_type, from_date, to_date):
    try:
        member = Party.objects.get(pk=member_id)
    except Party.DoesNotExist:
        raise Http404
    role = "producer"
    plan_type = "Production"
    if member.is_customer():
        role = "consumer"
        plan_type = "Consumption"
    from_datestring = from_date
    to_datestring = to_date
    try:
        from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
        to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    # force from_date to Monday, to_date to Sunday
    from_date = from_date - datetime.timedelta(days=datetime.date.weekday(from_date))
    to_date = to_date - datetime.timedelta(days=datetime.date.weekday(to_date)+1)
    to_date = to_date + datetime.timedelta(days=7)
    products = None
    if list_type == "M":
        if role == "consumer":
            products = CustomerProduct.objects.filter(customer=member, planned=True)
        else:
            products = ProducerProduct.objects.filter(producer=member, planned=True)
    if not products:
        products = Product.objects.filter(plannable=True)
        list_type = "A"
    columns = plan_columns(from_date, to_date)
    return render_to_response('distribution/dojo_planning_table.html', 
        {
            'from_date': from_date,
            'to_date': to_date,
            'from_datestring': from_datestring,
            'to_datestring': to_datestring,
            'columns': columns,
            'column_count': len(columns),
            'plan_type': plan_type,
            'member': member,
            'list_type': list_type,
            'tabnav': "distribution/tabnav.html",
        }, context_instance=RequestContext(request))


def json_planning_table(request, member_id, list_type, from_date, to_date, row_id=None):
    #import pdb; pdb.set_trace()
    try:
        member = Party.objects.get(pk=member_id)
    except Party.DoesNotExist:
        raise Http404
    role = "producer"
    plan_type = "Production"
    if member.is_customer():
        role = "consumer"
        plan_type = "Consumption"

    #import pdb; pdb.set_trace()
    if row_id:
        if request.method == "GET":
            #import pdb; pdb.set_trace()
            response = HttpResponse(request.raw_post_data, mimetype="text/json-comment-filtered")
            response['Cache-Control'] = 'no-cache'
            return response
        elif request.method == "PUT":
            #import pdb; pdb.set_trace()
            product = Product.objects.get(id=row_id)
            data = simplejson.loads(request.raw_post_data)
            member = Party.objects.get(id=data['member_id'])
            fd = data["from_date"]
            td = data["to_date"]
            from_date = datetime.datetime(*time.strptime(fd, '%Y-%m-%d')[0:5]).date()
            to_date = datetime.datetime(*time.strptime(td, '%Y-%m-%d')[0:5]).date() 
            wkdate = from_date
            while wkdate <= to_date:
                key = wkdate.strftime('%Y-%m-%d')
                qty = data[key]
                if is_number(qty):
                    qty = Decimal(qty)
                    plan_id = data.get(":".join([key, "plan_id"]))
                    from_dt = wkdate
                    to_dt = from_dt + datetime.timedelta(days=6)
                    plan = None
                    if plan_id:
                        plan = ProductPlan.objects.get(id=plan_id)
                        if plan.to_date < from_dt or plan.from_date > to_dt:
                            plan = None
                    if qty:
                        if plan:
                            if not qty == plan.quantity:
                                if plan.from_date >= from_dt and plan.to_date <= to_dt:
                                    plan.quantity = qty
                                    plan.save()
                                else:
                                    if plan.from_date < from_dt:
                                        new_to_dt = from_dt - datetime.timedelta(days=1)
                                        earlier_plan = ProductPlan(
                                            member=plan.member,
                                            product=plan.product,
                                            quantity=plan.quantity,
                                            from_date=plan.from_date,
                                            to_date=new_to_dt,
                                            role=plan.role,
                                            inventoried=plan.inventoried,
                                            distributor=plan.distributor,
                                        )
                                        earlier_plan.save()
                                    if plan.to_date > to_dt:
                                        new_plan = ProductPlan(
                                            member=plan.member,
                                            product=plan.product,
                                            quantity=qty,
                                            from_date=from_dt,
                                            to_date=to_dt,
                                            role=plan.role,
                                            inventoried=plan.inventoried,
                                            distributor=plan.distributor,
                                        )
                                        new_plan.save()
                                        plan.from_date = to_dt + datetime.timedelta(days=1)
                                        plan.save()
                                    else:
                                        plan.from_date=from_dt
                                        plan.quantity=qty
                                        plan.save()      
                        else:
                            new_plan = ProductPlan(
                                member=member,
                                product=product,
                                quantity=qty,
                                from_date=from_dt,
                                to_date=to_dt,
                                role=role,
                            )
                            new_plan.save()
                            if role == "producer":
                                listed_product, created = ProducerProduct.objects.get_or_create(
                                    product=product, producer=member)
                            elif role == "consumer":
                                listed_product, created = CustomerProduct.objects.get_or_create(
                                    product=product, customer=member)

                    else:
                        if plan:
                            if plan.from_date >= from_dt and plan.to_date <= to_dt:
                                plan.delete()
                            else:
                                if plan.to_date > to_dt:
                                    early_from_dt = plan.from_date              
                                    if plan.from_date < from_dt:
                                        early_to_dt = from_dt - datetime.timedelta(days=1)
                                        earlier_plan = ProductPlan(
                                            member=plan.member,
                                            product=plan.product,
                                            quantity=plan.quantity,
                                            from_date=early_from_dt,
                                            to_date=early_to_dt,
                                            role=plan.role,
                                            inventoried=plan.inventoried,
                                            distributor=plan.distributor,
                                         )
                                        earlier_plan.save()
                                    plan.from_date = to_dt + datetime.timedelta(days=1)
                                    plan.save()
                                else:
                                    plan.to_date= from_dt - datetime.timedelta(days=1)
                                    plan.save()

                wkdate = wkdate + datetime.timedelta(days=7)

            response = HttpResponse(request.raw_post_data, mimetype="text/json-comment-filtered")
            response['Cache-Control'] = 'no-cache'
            return response
    else:
        try:
            from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
            to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
        except ValueError:
            raise Http404
        # force from_date to Monday, to_date to Sunday
        from_date = from_date - datetime.timedelta(days=datetime.date.weekday(from_date))
        to_date = to_date - datetime.timedelta(days=datetime.date.weekday(to_date)+1)
        to_date = to_date + datetime.timedelta(days=7)
        products = None
        if list_type == "M":
            if role == "consumer":
                products = CustomerProduct.objects.filter(customer=member, planned=True)
            else:
                products = ProducerProduct.objects.filter(producer=member, planned=True)
        if not products:
            products = Product.objects.filter(plannable=True)
            list_type = "A"
        #import pdb; pdb.set_trace()
        rows = plans_for_dojo(member, products, from_date, to_date)
        range = request.META["HTTP_RANGE"]
        range = range.split("=")[1]
        range = range.split("-")
        range_start = int(range[0])
        range_end = int(range[1])
        count = len(rows)
        if count < range_end:
            range_end = count
        rows = rows[range_start:range_end + 1]
        data = simplejson.dumps(rows)
        response = HttpResponse(data, mimetype="text/json-comment-filtered")
        response['Cache-Control'] = 'no-cache'
        response['Content-Range'] = "".join(["items ", str(range_start),
            "-", str(range_end), "/", str(count + 1)])
        return response

@login_required
def plan_update(request, prod_id):
    try:
        member = Party.objects.get(pk=prod_id)
    except Party.DoesNotExist:
        raise Http404
    if request.method == "POST":
        itemforms = create_plan_forms(member, request.POST)     
        if all([itemform.is_valid() for itemform in itemforms]):
            member_id = request.POST['member-id']
            member = Party.objects.get(pk=member_id)
            role = "producer"
            if member.is_customer():
                role = "consumer"
            for itemform in itemforms:
                data = itemform.cleaned_data
                prodname = data['prodname']
                item_id = data['item_id']
                from_date = data['from_date']
                to_date = data['to_date']
                quantity = data['quantity']
                if item_id:
                    item = ProductPlan.objects.get(pk=item_id)
                    item.from_date = from_date
                    item.to_date = to_date
                    item.quantity = quantity
                    item.save()
                else:
                    if quantity > 0:
                        prodname = data['prodname']
                        product = Product.objects.get(short_name__exact=prodname)
                        item = itemform.save(commit=False)
                        item.member = member
                        item.product = product
                        item.role = role
                        item.save()
            return HttpResponseRedirect('/%s/%s/'
               % ('distribution/producerplan', member_id))
        else:
            for itemform in itemforms:
                if not itemform.is_valid():
                    print '**invalid**', itemform
    else:
        itemforms = create_plan_forms(member)
    return render_to_response('distribution/plan_update.html', {'member': member, 'item_forms': itemforms})

@login_required
def inventory_selection(request):
    try:
        fn = food_network()
    except FoodNetwork.DoesNotExist:
        return render_to_response('distribution/network_error.html')
    this_week = current_week()
    init = {"avail_date": this_week,}
    available = fn.all_avail_items(this_week)
    if request.method == "POST":
        ihform = InventorySelectionForm(request.POST)  
        if ihform.is_valid():
            ihdata = ihform.cleaned_data
            producer_id = ihdata['producer']
            inv_date = ihdata['avail_date']
            #import pdb; pdb.set_trace()
            if int(producer_id):
                return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
                    % ('distribution/inventoryupdate', producer_id, inv_date.year, inv_date.month, inv_date.day))
            else:
                return HttpResponseRedirect('/%s/%s/%s/%s/'
                    % ('distribution/allinventoryupdate', inv_date.year, inv_date.month, inv_date.day))
    else:
        ihform = InventorySelectionForm(initial=init)
    return render_to_response('distribution/inventory_selection.html', {
        'header_form': ihform,
        'available': available,
    }, context_instance=RequestContext(request))

@login_required
def inventory_update(request, prod_id, year, month, day):
    availdate = datetime.date(int(year), int(month), int(day))
    try:
        producer = Party.objects.get(pk=prod_id)
    except Party.DoesNotExist:
        raise Http404
    monday = availdate - datetime.timedelta(days=datetime.date.weekday(availdate))
    saturday = monday + datetime.timedelta(days=5)
    #import pdb; pdb.set_trace()
    items = InventoryItem.objects.filter(
        producer=producer, 
        remaining__gt=0,
        inventory_date__range=(monday, saturday))
    plans = ProductPlan.objects.filter(
        member=producer, 
        from_date__lte=availdate, 
        to_date__gte=saturday)
    if plans:
        planned = True
    else:
        planned = False
        plans = producer.producer_products.all()
    itemforms = create_inventory_item_forms(
            producer, availdate, plans, items, data=request.POST or None)
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        if all([itemform.is_valid() for itemform in itemforms]):
            producer_id = request.POST['producer-id']
            producer = Producer.objects.get(pk=producer_id)
            inv_date = request.POST['avail-date']
            for itemform in itemforms:
                data = itemform.cleaned_data
                prod_id = data['prod_id']
                item_id = data['item_id']
                custodian = data['custodian']
                inventory_date = data['inventory_date']
                planned = data['planned']
                received = data['received']
                notes = data['notes']
                field_id = data['field_id']
                freeform_lot_id = data['freeform_lot_id']

                if item_id:
                    item = InventoryItem.objects.get(pk=item_id)
                    item.custodian = custodian
                    item.inventory_date = inventory_date
                    rem_change = planned - item.planned
                    item.planned = planned
                    item.remaining = item.remaining + rem_change
                    oh_change = received - item.received                 
                    item.received = received
                    item.onhand = item.onhand + oh_change
                    item.notes = notes
                    item.field_id = field_id
                    item.freeform_lot_id = freeform_lot_id
                    item.save()
                else:
                    if planned + received > 0:
                        prod_id = data['prod_id']
                        product = Product.objects.get(pk=prod_id)
                        item = itemform.save(commit=False)
                        item.producer = producer
                        #item.custodian = custodian
                        #item.inventory_date = inventory_date
                        item.product = product
                        item.remaining = planned
                        item.onhand = received
                        #item.notes = notes
                        item.save()
            return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
               % ('distribution/produceravail', producer_id, year, month, day))
    return render_to_response('distribution/inventory_update.html', {
        'avail_date': availdate, 
        'producer': producer,
        'planned': planned,
        'item_forms': itemforms}, context_instance=RequestContext(request))

@login_required
def all_inventory_update(request, year, month, day):
    availdate = datetime.date(int(year), int(month), int(day))
    monday = availdate - datetime.timedelta(days=datetime.date.weekday(availdate))
    saturday = monday + datetime.timedelta(days=5)
    #import pdb; pdb.set_trace()
    items = InventoryItem.objects.select_related(depth=1).filter(
        remaining__gt=0,
        inventory_date__range=(monday, saturday))
    plans = ProductPlan.objects.select_related(depth=1).filter(
        role="producer",
        from_date__lte=availdate, 
        to_date__gte=saturday)
    if plans:
        planned = True
    else:
        planned = False
        plans = ProducerProduct.objects.select_related(depth=1).all()
    itemforms = create_all_inventory_item_forms(
            availdate, plans, items, data=request.POST or None)
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        if all([itemform.is_valid() for itemform in itemforms]):
            inv_date = request.POST['avail-date']
            for itemform in itemforms:
                data = itemform.cleaned_data
                producer_id = int(data['producer_id'])
                producer = Producer.objects.get(pk=producer_id)
                prod_id = int(data['product_id'])
                item_id = int(data['item_id'])
                custodian = data['custodian']
                inventory_date = data['inventory_date']
                planned = data['planned']
                received = data['received']
                notes = data['notes']
                field_id = data['field_id']
                freeform_lot_id = data['freeform_lot_id']
                #import pdb; pdb.set_trace()
                if item_id:
                    item = InventoryItem.objects.get(pk=item_id)
                    item.custodian = custodian
                    item.inventory_date = inventory_date
                    rem_change = planned - item.planned
                    item.planned = planned
                    item.remaining = item.remaining + rem_change
                    oh_change = received - item.received                 
                    item.received = received
                    item.onhand = item.onhand + oh_change
                    item.notes = notes
                    item.field_id = field_id
                    item.freeform_lot_id = freeform_lot_id
                    item.save()
                else:
                    if planned + received > 0:
                        #prod_id = data['product_id']
                        product = Product.objects.get(pk=prod_id)
                        item = itemform.save(commit=False)
                        item.producer = producer
                        #item.custodian = custodian
                        #item.inventory_date = inventory_date
                        item.product = product
                        item.remaining = planned
                        item.onhand = received
                        #item.notes = notes
                        item.save()
            return HttpResponseRedirect('/%s/'
               % ('distribution/inventoryselection',))
    return render_to_response('distribution/all_inventory_update.html', {
        'avail_date': availdate, 
        'planned': planned,
        'item_forms': itemforms}, context_instance=RequestContext(request))


@login_required
def order_selection(request):
    unpaid_orders = Order.objects.exclude(state__contains="Paid").exclude(state="Unsubmitted")
    if request.method == "POST":
        ihform = OrderSelectionForm(request.POST)  
        if ihform.is_valid():
            ihdata = ihform.cleaned_data
            customer_id = ihdata['customer']
            ord_date = ihdata['delivery_date']
            if ordering_by_lot():
                return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
                   % ('distribution/orderbylot', customer_id, ord_date.year, ord_date.month, ord_date.day))
            else:
                return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
                   % ('distribution/orderupdate', customer_id, ord_date.year, ord_date.month, ord_date.day))
    else:
        ihform = OrderSelectionForm()
    return render_to_response(
        'distribution/order_selection.html', 
        {'header_form': ihform,
         'unpaid_orders': unpaid_orders}, context_instance=RequestContext(request))


    #init = {"delivery_date": current_week(),}
    #if request.method == "POST":
    #    ihform = OrderSelectionForm(request.POST)  
    #    if ihform.is_valid():
    #        ihdata = ihform.cleaned_data
    #        customer_id = ihdata['customer']
    #        ord_date = ihdata['delivery_date']
    #        if ordering_by_lot():
    #            return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
    #               % ('distribution/orderbylot', customer_id, ord_date.year, ord_date.month, ord_date.day))
    #        else:
    #            return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
    #               % ('distribution/orderupdate', customer_id, ord_date.year, ord_date.month, ord_date.day))
    #else:)
    #    ihform = OrderSelectionForm(initial=init)
    #return render_to_response('distribution/order_selection.html', {'header_form': ihform})

#todo: this whole view shd be changed a la PBC
# plus, it is a logical mess...
@login_required
def order_update(request, cust_id, year, month, day):
    delivery_date = datetime.date(int(year), int(month), int(day))
    availdate = delivery_date

    try:
        fn = food_network()
    except FoodNetwork.DoesNotExist:
        return render_to_response('distribution/network_error.html')

    cust_id = int(cust_id)
    try:
        customer = Customer.objects.get(pk=cust_id)
    except Customer.DoesNotExist:
        raise Http404

    try:
        order = Order.objects.get(customer=customer, delivery_date=delivery_date)
    except MultipleObjectsReturned:
        order = Order.objects.filter(customer=customer, delivery_date=delivery_date)[0]
    except Order.DoesNotExist:
        order = False

    if request.method == "POST":
        if order:
            ordform = OrderForm(order=order, data=request.POST, instance=order)
        else:
            ordform = OrderForm(data=request.POST, initial={
                'customer': customer,
                'order_date': datetime.date.today(),
                'delivery_date': delivery_date,
                'transportation_fee': fn.transportation_fee,
                })
        #import pdb; pdb.set_trace()
        itemforms = create_order_item_forms(order, availdate, delivery_date, request.POST)
        #import pdb; pdb.set_trace()
        if ordform.is_valid() and all([itemform.is_valid() for itemform in itemforms]):
            if order:
                the_order = ordform.save(commit=False)
                the_order.changed_by = request.user
                the_order.save()
            else:
                the_order = ordform.save(commit=False)
                the_order.created_by = request.user
                the_order.customer = customer
                #the_order.delivery_date = delivery_date
                the_order.save()

            order_data = ordform.cleaned_data
            transportation_fee = order_data["transportation_fee"]
            distributor = order_data["distributor"] or fn 
            #import pdb; pdb.set_trace()
            if transportation_fee:
                transportation_tx = None
                if order:
                    try:
                        transportation_tx = TransportationTransaction.objects.get(order=order)
                        if transportation_fee != transportation_tx.amount:
                            transportation_tx.amount = transportation_fee
                            transportation_tx.save()
                    except TransportationTransaction.DoesNotExist:
                        pass
                if not transportation_tx:
                    transportation_tx = TransportationTransaction(
                        from_whom=distributor,
                        to_whom=customer,
                        order=the_order, 
                        amount=transportation_fee,
                        transaction_date=delivery_date)
                    transportation_tx.save()

            for itemform in itemforms:
                data = itemform.cleaned_data
                qty = data['quantity'] 
                if itemform.instance.id:
                    if qty > 0:
                        itemform.save()
                    else:
                        itemform.instance.delete()
                else:                    
                    if qty > 0:
                        # these product gyrations wd not be needed if I cd make the product field readonly
                        # or display the product field value (instead of the input widget) in the template
                        prod_id = data['prod_id']
                        product = Product.objects.get(pk=prod_id)
                        oi = itemform.save(commit=False)
                        oi.order = the_order
                        oi.product = product
                        oi.save()
            return HttpResponseRedirect('/%s/%s/'
               % ('distribution/order', the_order.id))
    else:
        if order:
            ordform = OrderForm(order=order, instance=order)
        else:
            ordform = OrderForm(initial={
                'customer': customer,
                'order_date': datetime.date.today(),
                'delivery_date': delivery_date,
                'transportation_fee': fn.transportation_fee,
            })
        itemforms = create_order_item_forms(order, availdate, delivery_date)
    return render_to_response('distribution/order_update.html', 
        {'customer': customer, 
         'order': order, 
         'delivery_date': delivery_date, 
         'avail_date': availdate, 
         'order_form': ordform, 
         'item_forms': itemforms}, context_instance=RequestContext(request))

def create_order_by_lot_forms(order, delivery_date, data=None):    
    fn = food_network()
    
    items = fn.all_avail_items(delivery_date)

    initial_data = []
    
    product_dict = {}
    if order:
        for oi in order.orderitem_set.all():
            product_dict[oi.product] = True
            item = oi.lot()
            avail = oi.quantity
            if item:
                if item.remaining:
                    avail = item.remaining + oi.quantity
                if item.onhand:
                    avail = item.onhand + oi.quantity
                lot_label = item.lot_id()
                lot_id = item.id
            else:
                avail = Decimal("0")
                lot_label = "None"
                lot_id = 0
            dict ={
                'order_item_id': oi.id,
                'lot_id': lot_id,
                'product_id': oi.product.id,
                'avail': avail, 
                'lot_label': lot_label,
                'unit_price': oi.unit_price,
                'quantity': oi.quantity,
                'notes': oi.notes}
            initial_data.append(dict)

    for item in items:
        if not item.product in product_dict:
            # all_avail_items must have either remaining or onhand qty
            if item.remaining:
                avail = item.remaining
            else:
                avail = item.onhand 
            dict ={
                'order_item_id': None,
                'lot_id': item.id,
                'product_id': item.product.id,
                'avail': avail, 
                'lot_label': item.lot_id(),
                'unit_price': item.product.price,
                'quantity': Decimal(0),
                'notes': ""}
            initial_data.append(dict)
                       
    OrderByLotFormSet = formset_factory(OrderByLotForm, extra=0)
    formset = OrderByLotFormSet(initial=initial_data)
    #import pdb; pdb.set_trace()
    return formset

@login_required
def order_by_lot(request, cust_id, year, month, day):
    orderdate = datetime.date(int(year), int(month), int(day))
    
    try:
        fn = food_network()
    except FoodNetwork.DoesNotExist:
        return render_to_response('distribution/network_error.html')

    cust_id = int(cust_id)
    try:
        customer = Customer.objects.get(pk=cust_id)
    except Customer.DoesNotExist:
        raise Http404

    try:
        order = Order.objects.get(customer=customer, delivery_date=orderdate)
    except MultipleObjectsReturned:
        order = Order.objects.filter(customer=customer, delivery_date=orderdate)[0]
    except Order.DoesNotExist:
        order = False

    if request.method == "POST":
        if order:
            ordform = OrderForm(order=order, data=request.POST, instance=order)
        else:
            ordform = OrderForm(data=request.POST)
        OrderByLotFormSet = formset_factory(OrderByLotForm, extra=0)
        formset = OrderByLotFormSet(request.POST)
        if ordform.is_valid() and formset.is_valid():
            if order:
                the_order = ordform.save()
            else:
                the_order = ordform.save(commit=False)
                the_order.customer = customer
                the_order.delivery_date = orderdate
                the_order.save()
            order_data = ordform.cleaned_data
            transportation_fee = order_data["transportation_fee"]
            distributor = order_data["distributor"]
            #import pdb; pdb.set_trace()
            if transportation_fee:
                transportation_tx = None
                if order:
                    try:
                        transportation_tx = TransportationTransaction.objects.get(order=order)
                        if transportation_fee != transportation_tx.amount:
                            transportation_tx.amount = transportation_fee
                            transportation_tx.save()
                    except TransportationTransaction.DoesNotExist:
                        pass
                if not transportation_tx:
                    transportation_tx = TransportationTransaction(
                        from_whom=distributor,
                        to_whom=customer,
                        order=the_order, 
                        amount=transportation_fee,
                        transaction_date=orderdate)
                    transportation_tx.save()
                
            for form in formset.forms:
                data = form.cleaned_data
                qty = data["quantity"]
                oi_id = data["order_item_id"]
                product_id = data["product_id"]
                product = Product.objects.get(pk=product_id)                
                unit_price = data["unit_price"]
                notes = data["notes"]
                lot_id = data["lot_id"]
                lot = InventoryItem.objects.get(pk=lot_id)
                if oi_id:
                    oi = OrderItem.objects.get(pk=oi_id)
                    if oi.quantity != qty or oi.unit_price != unit_price:
                        delivery = oi.inventorytransaction_set.all()[0]
                        if qty > 0:
                            oi.quantity = qty
                            oi.unit_price = unit_price
                            oi.notes=notes
                            oi.save()
                            delivery.amount=qty
                            delivery.unit_price = unit_price
                            delivery.save()
                        else:
                            delivery.delete()
                            oi.delete()                      
                    elif oi.notes != notes:
                        oi.notes = notes
                        oi.save()         
                else:
                    if qty:
                        oi = OrderItem(
                            order=the_order,
                            product=product,
                            quantity=qty,
                            unit_price=unit_price,
                            notes=notes)
                        oi.save()
                        delivery = InventoryTransaction(
                            transaction_type="Delivery",
                            inventory_item=lot,
                            order_item=oi,
                            from_whom = lot.producer,
                            to_whom = customer,
                            amount=qty,
                            transaction_date=orderdate)
                        delivery.save()

            return HttpResponseRedirect('/%s/%s/'
               % ('distribution/order', the_order.id))
        #if invalid
        else:
            #print "ordform:", ordform
            #for form in formset.forms:
            #    print form.as_table()
            #todo: this is wrong, shd redisplay with errors
            if order:
                ordform = OrderForm(order=order, instance=order)
            else:
                ordform = OrderForm(initial={'customer': customer, 'delivery_date': orderdate, })
            formset = create_order_by_lot_forms(order, orderdate)                     
    else:
        if order:
            ordform = OrderForm(order=order, instance=order)
        else:
            ordform = OrderForm(initial={'customer': customer, 'delivery_date': orderdate, })
        formset = create_order_by_lot_forms(order, orderdate) 
        
    return render_to_response('distribution/order_by_lot.html', 
        {'customer': customer, 
         'order': order, 
         'delivery_date': orderdate, 
         'order_form': ordform, 
         'formset': formset}, context_instance=RequestContext(request))    

@login_required
def delivery_selection(request):
    init = {"delivery_date": current_week(),}
    if request.method == "POST":
        dsform = DeliverySelectionForm(request.POST)  
        if dsform.is_valid():
            dsdata = dsform.cleaned_data
            cust_id = dsdata['customer']
            ord_date = dsdata['delivery_date']
            return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
               % ('distribution/deliveryupdate', cust_id, ord_date.year, ord_date.month, ord_date.day))
    else:
        #dsform = DeliverySelectionForm(initial={'order_date': order_date, })
    #return render_to_response('distribution/delivery_selection.html', {'order_date': order_date, 'header_form': dsform})
        dsform = DeliverySelectionForm(initial=init)
    return render_to_response('distribution/delivery_selection.html', 
        {'header_form': dsform}, context_instance=RequestContext(request))

@login_required
def delivery_update(request, cust_id, year, month, day):
    thisdate = datetime.date(int(year), int(month), int(day))
    cust_id = int(cust_id)
    if cust_id:
        try:
            customer = Customer.objects.get(pk=cust_id)
        except Customer.DoesNotExist:
            raise Http404
    else:
        customer = ''
        
    try:
        fn = food_network()
    except FoodNetwork.DoesNotExist:
        return render_to_response('distribution/network_error.html')
    
    #todo: finish this thought
    lots = fn.all_avail_items(thisdate)
    lot_list = []
    for lot in lots:
        lot_list.append([lot.id, float(lot.avail_qty())])

    if request.method == "POST":
        itemforms = create_delivery_forms(thisdate, customer, request.POST)
        for itemform in itemforms:
            if itemform.is_valid():
                item_data = itemform.cleaned_data
                oi_id = item_data['order_item_id']
                order_item = OrderItem.objects.get(pk=oi_id)
                if not customer:
                    customer = order_item.order.customer
                #import pdb; pdb.set_trace()
                for delform in itemform.delivery_forms:
                    if delform.is_valid():
                        del_data = delform.cleaned_data
                        inv_item = del_data['inventory_item']
                        amt = del_data['amount']
                        if delform.instance.pk:
                            if amt > 0:
                                delform.save()
                            else:
                                delform.instance.delete()
                        else:
                            delivery = delform.save(commit=False) 
                            delivery.from_whom = inv_item.producer
                            delivery.to_whom = customer
                            delivery.order_item = order_item
                            delivery.unit_price = order_item.unit_price
                            delivery.transaction_date = order_item.order.delivery_date
                            delivery.transaction_type='Delivery'
                            delivery.save()
        return HttpResponseRedirect('/%s/%s/%s/%s/' 
                                    % ('distribution/orderdeliveries', year, month, day))
    else:
        itemforms = create_delivery_forms(thisdate, customer)
    return render_to_response('distribution/delivery_update.html', {
        'delivery_date': thisdate, 
        'customer': customer, 
        'item_forms': itemforms,
        'lot_list': lot_list,
        }, context_instance=RequestContext(request))


def order_headings_by_product(thisdate, links=True):
    orders = Order.objects.filter(delivery_date=thisdate).exclude(state='Unsubmitted')
    heading_list = []
    for order in orders:
        lines = []
        if links:
            lines.append("<a href='/distribution/order/" + str(order.id) + "/'>" + order.customer.short_name + "</a>")
        else:
            lines.append(order.customer.short_name)
        lines.append(order.customer.contact)
        lines.append(order.customer.phone)
        heading = " ".join(str(i) for i in lines)
        heading_list.append(heading)
    return heading_list


def order_item_rows_by_product(thisdate):
    orders = Order.objects.filter(delivery_date=thisdate).exclude(state='Unsubmitted')
    if not orders:
        return []
    #cust_list = []
    #for order in orders:
    #    cust_list.append(order.customer.short_name)
    #cust_count = len(cust_list)
    order_list = []
    for order in orders:
        order_list.append(order.id)
    order_count = len(order_list)
    prods = Product.objects.all()
    product_dict = {}
    for prod in prods:
        totavail = prod.total_avail(thisdate)
        totordered = prod.total_ordered(thisdate)
        if totordered > 0:
            producers = prod.avail_producers(thisdate)
            product_dict[prod.short_name] = [prod.parent_string(),
                prod.long_name, prod.growing_method, producers, totavail, totordered]
            for x in range(order_count):
                product_dict[prod.short_name].append(' ')
    items = OrderItem.objects.filter(order__delivery_date=thisdate)
    for item in items:
        prod_cell = order_list.index(item.order.id) + 6
        product_dict[item.product.short_name][prod_cell] = item.quantity
    item_list = product_dict.values()
    item_list.sort()
    return item_list

def order_item_rows(thisdate):
    orders = Order.objects.filter(delivery_date=thisdate).exclude(state='Unsubmitted')
    if not orders:
        return []
    cust_list = []
    for order in orders:
        cust_list.append(order.customer.id)
    cust_count = len(cust_list)
    prods = Product.objects.all()
    product_dict = {}
    for prod in prods:
        totavail = prod.total_avail(thisdate)
        totordered = prod.total_ordered(thisdate)
        if totordered > 0:
            producers = prod.avail_producers(thisdate)
            product_dict[prod.id] = [prod.parent_string(), prod.long_name, producers, totavail, totordered]
            for x in range(cust_count):
                product_dict[prod.id].append(' ')
    items = OrderItem.objects.filter(order__delivery_date=thisdate)
    for item in items:
        prod_cell = cust_list.index(item.order.customer.id) + 5
        product_dict[item.product.id][prod_cell] = item.quantity
    item_list = product_dict.values()
    item_list.sort()
    return item_list

@login_required
def order_table_selection(request):
    init = {"selected_date": current_week(),}
    if request.method == "POST":
        dsform = DateSelectionForm(request.POST)  
        if dsform.is_valid():
            dsdata = dsform.cleaned_data
            ord_date = dsdata['selected_date']
            if request.POST.get('submit-order-table'):
                if ordering_by_lot():
                    return HttpResponseRedirect('/%s/%s/%s/%s/'
                        % ('distribution/ordertable', ord_date.year, ord_date.month, ord_date.day))
                else:
                    return HttpResponseRedirect('/%s/%s/%s/%s/'
                        % ('distribution/ordertablebyproduct', ord_date.year, ord_date.month, ord_date.day))
            elif request.POST.get('submit-short-changes'):
                return HttpResponseRedirect('/%s/%s/%s/%s/'
                    % ('distribution/shortschanges', ord_date.year, ord_date.month, ord_date.day))
            else:
                return HttpResponseRedirect('/%s/%s/%s/%s/'
                    % ('distribution/shorts', ord_date.year, ord_date.month, ord_date.day))
    else:
        dsform = DateSelectionForm(initial=init)
    return render_to_response('distribution/order_table_selection.html', 
            {
                'dsform': dsform,
                'show_shorts': not ordering_by_lot(),
            }, context_instance=RequestContext(request))

ORDER_HEADINGS = ["Customer", "Order", "Lot", "Custodian", "Order Qty"]

@login_required
def order_table(request, year, month, day):
    thisdate = datetime.date(int(year), int(month), int(day))
    date_string = thisdate.strftime('%Y_%m_%d')
    heading_list = ORDER_HEADINGS
    orders = Order.objects.filter(delivery_date=thisdate)
    for order in orders:
        order.rows = order.orderitem_set.all().count()
    item_list = OrderItem.objects.filter(order__delivery_date=thisdate)
    return render_to_response('distribution/order_table.html', 
        {'date': thisdate, 
         'datestring': date_string,
         'heading_list': heading_list, 
         'item_list': item_list,
         'orders': orders,}, context_instance=RequestContext(request))

@login_required
def order_table_by_product(request, year, month, day):
    thisdate = datetime.date(int(year), int(month), int(day))
    date_string = thisdate.strftime('%Y_%m_%d')
    heading_list = order_headings_by_product(thisdate)
    item_list = order_item_rows_by_product(thisdate)
    return render_to_response('distribution/order_table_by_product.html', 
        {'date': thisdate, 
         'datestring': date_string,
         'heading_list': heading_list, 
         'item_list': item_list}, context_instance=RequestContext(request))


def order_csv(request, delivery_date):
    thisdate = datetime.datetime(*time.strptime(delivery_date, '%Y_%m_%d')[0:5]).date()
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=ordersheet.csv'
    #thisdate = current_week()
    writer = csv.writer(response)
    writer.writerow(ORDER_HEADINGS)
    for item in OrderItem.objects.filter(order__delivery_date=thisdate):
        lot = item.lot()
        if lot:
            custodian = lot.custodian
        else:
            custodian = ""            
        writer.writerow(
            [item.order.customer.long_name,
             "".join(["#", str(item.order.id), " ", item.order.delivery_date.strftime('%Y-%m-%d')]),
             lot,
             custodian,
             item.quantity]
             )
    return response


def order_csv_by_product(request, delivery_date):
    thisdate = datetime.datetime(*time.strptime(delivery_date, '%Y_%m_%d')[0:5]).date()
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=ordersheet.csv'
    product_heads = ['Category', 'Product', 'Producers', 'Avail', 'Ordered']
    order_heads = order_headings_by_product(thisdate, links=False)
    heading_list = product_heads + order_heads
    item_list = order_item_rows(thisdate)
    writer = csv.writer(response)
    writer.writerow(heading_list)
    for item in item_list:
        writer.writerow(item)
    return response

@login_required
def shorts(request, year, month, day):
    thisdate = datetime.date(int(year), int(month), int(day))
    date_string = thisdate.strftime('%Y_%m_%d')
    shorts_table = create_shorts_table(thisdate, data=request.POST or None)
    #print shorts_table.rows[0].item_forms[0].as_table()
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        changed_items = []
        for row in shorts_table.rows:
            for item_form in row.item_forms:
                if item_form.is_valid():
                    item_data = item_form.cleaned_data
                    qty = item_data["quantity"]
                    id = item_data["item_id"]
                    #print "qty:", qty, "id:", id
                    item = OrderItem.objects.get(pk=id)
                    if item.quantity != qty:
                        if not item.orig_qty:
                            item.orig_qty = item.quantity
                        item.quantity = qty
                        item.save()
                        changed_items.append(item)
        return HttpResponseRedirect('/%s/%s/%s/%s/'
            % ('distribution/shortschanges', thisdate.year, thisdate.month, thisdate.day))
    return render_to_response('distribution/shorts.html', 
        {'date': thisdate, 
         'shorts_table': shorts_table }, context_instance=RequestContext(request))

@login_required
def shorts_changes(request, year, month, day):
    thisdate = datetime.date(int(year), int(month), int(day))
    changed_items = OrderItem.objects.filter(
        order__delivery_date=thisdate,
        orig_qty__gt=Decimal("0")
    )
    return render_to_response('distribution/shorts_changes.html', 
        {'date': thisdate, 
         'changed_items': changed_items }, context_instance=RequestContext(request))

@login_required
def send_short_change_notices(request, year, month, day):
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        if notification:
            try:
                fn = food_network()
                food_network_name = fn.long_name
            except FoodNetwork.DoesNotExist:
                return render_to_response('distribution/network_error.html')

            if fn:
                thisdate = datetime.date(int(year), int(month), int(day))
                changed_items = OrderItem.objects.filter(
                    order__delivery_date=thisdate,
                    orig_qty__gt=Decimal("0")
                )
                orders = {}
                for item in changed_items:
                    if not item.order in orders:
                        orders[item.order] = []
                    orders[item.order].append(item)

                for order in orders:
                    users = [order.customer, fn]
                    if order.created_by:
                        if request.user.id == order.created_by.id:
                            parties = request.user.parties.all()
                            if parties:
                                user_party = parties[0]
                                if user_party.id == order.customer.id:
                                    if not user.email == order.customer.email:
                                        users.append(request.user)             
                    notification.send(users, "distribution_short_change_notice", {
                        "order": order, 
                        "items": orders[order],
                        "delivery_date": thisdate})
                request.user.message_set.create(message="Short Change emails have been sent")
        return HttpResponseRedirect(request.POST["next"])

@login_required
def order(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        raise Http404
    return render_to_response('distribution/order.html', 
        {'order': order}, context_instance=RequestContext(request))

@login_required
def order_with_lots(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        raise Http404
    return render_to_response('distribution/order_with_lots.html', 
        {'order': order}, context_instance=RequestContext(request))

@login_required
def producerplan(request, prod_id):
    try:
        member = Party.objects.get(pk=prod_id)
    except Party.DoesNotExist:
        raise Http404
    plans = list(ProductPlan.objects.filter(member=member))
    for plan in plans:
        plan.parents = plan.product.parent_string()
    plans.sort(lambda x, y: cmp(x.parents, y.parents))
        
    return render_to_response('distribution/producer_plan.html', 
        {'member': member, 
         'plans': plans }, context_instance=RequestContext(request))

@login_required
def supply_and_demand(request, from_date, to_date):
    try:
        from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
        to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    sdtable = supply_demand_table(from_date, to_date)
    return render_to_response('distribution/supply_demand.html', 
        {
            'from_date': from_date,
            'to_date': to_date,
            'sdtable': sdtable,
            'tabnav': "distribution/tabnav.html",
            'tabs': 'D',
        }, context_instance=RequestContext(request))

@login_required
def dojo_supply_and_demand(request, from_date, to_date):
    from_datestring = from_date
    to_datestring = to_date
    try:
        from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
        to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    columns = sd_columns(from_date, to_date)
    return render_to_response('distribution/dojo_supply_demand.html', 
        {
            'from_date': from_date,
            'to_date': to_date,
            'from_datestring': from_datestring,
            'to_datestring': to_datestring,
            'columns': columns,
            'column_count': len(columns),
            'tabnav': "distribution/tabnav.html",
            'tabs': 'D',
        }, context_instance=RequestContext(request))

@login_required
def json_supply_and_demand(request, from_date, to_date):
    try:
        from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
        to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    rows = supply_demand_rows(from_date, to_date)
    count = len(rows)
    try:
        range = request.META["HTTP_RANGE"]
        range = range.split("=")[1]
        range = range.split("-")
        range_start = int(range[0])
        range_end = int(range[1])
    except KeyError:
        range_start = 0
        range_end = count
    if count < range_end:
        range_end = count
    rows = rows[range_start:range_end + 1]
    data = simplejson.dumps(rows)
    response = HttpResponse(data, mimetype="text/json-comment-filtered")
    response['Cache-Control'] = 'no-cache'
    response['Content-Range'] = "".join(["items ", str(range_start),
        "-", str(range_end), "/", str(count + 1)])
    return response

@login_required
def dojo_income(request, from_date, to_date):
    from_datestring = from_date
    to_datestring = to_date
    try:
        from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
        to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    income_table = suppliable_demand(from_date, to_date)
    total_net =  sum(row[len(row)-1] for row in income_table.rows)
    total_gross =  sum(row[len(row)-2] for row in income_table.rows)
    columns = sd_columns(from_date, to_date)
    return render_to_response('distribution/dojo_income.html', 
        {
            'from_date': from_date,
            'to_date': to_date,
            'from_datestring': from_datestring,
            'to_datestring': to_datestring,
            'total_net': total_net,
            'total_gross': total_gross,
            'columns': columns,
            'column_count': len(columns) + 2,
            'tabnav': "distribution/tabnav.html",
            'tabs': 'D',
        }, context_instance=RequestContext(request))

@login_required
def json_income(request, from_date, to_date):
    try:
        from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
        to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    rows = json_income_rows(from_date, to_date)
    count = len(rows)
    try:
        range = request.META["HTTP_RANGE"]
        range = range.split("=")[1]
        range = range.split("-")
        range_start = int(range[0])
        range_end = int(range[1])
    except KeyError:
        range_start = 0
        range_end = count
    if count < range_end:
        range_end = count
    rows = rows[range_start:range_end + 1]
    data = simplejson.dumps(rows)
    response = HttpResponse(data, mimetype="text/json-comment-filtered")
    response['Cache-Control'] = 'no-cache'
    response['Content-Range'] = "".join(["items ", str(range_start),
        "-", str(range_end), "/", str(count + 1)])
    return response




@login_required
def income(request, from_date, to_date):
    try:
        from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
        to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    income_table = suppliable_demand(from_date, to_date)
    total_net =  sum(row[len(row)-1] for row in income_table.rows)
    total_gross =  sum(row[len(row)-2] for row in income_table.rows)
    return render_to_response('distribution/income.html', 
        {
            'from_date': from_date,
            'to_date': to_date,
            'total_net': total_net,
            'total_gross': total_gross,
            'income_table': income_table,
        }, context_instance=RequestContext(request))

@login_required
def member_supply_and_demand(request, from_date, to_date, member_id):
    try:
        member = Party.objects.get(pk=member_id)
    except Party.DoesNotExist:
        raise Http404
    try:
        from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
        to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    sdtable = supply_demand_table(from_date, to_date, member)
    plan_type = "Production"
    if member.is_customer():
        plan_type = "Consumption"
    #import pdb; pdb.set_trace()
    return render_to_response('distribution/member_plans.html', 
        {
            'from_date': from_date,
            'to_date': to_date,
            'sdtable': sdtable,
            'member': member,
            'plan_type': plan_type,
            'tabnav': "distribution/tabnav.html",
        }, context_instance=RequestContext(request))

@login_required
def dojo_member_plans(request, from_date, to_date, member_id):
    try:
        member = Party.objects.get(pk=member_id)
    except Party.DoesNotExist:
        raise Http404
    from_datestring = from_date
    to_datestring = to_date
    try:
        from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
        to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    #sdtable = supply_demand_table(from_date, to_date, member)
    if member.is_customer():
        plan_type = "Consumption"
        products = CustomerProduct.objects.filter(customer=member, planned=True)
    else:
        plan_type = "Production"
        products = ProducerProduct.objects.filter(producer=member, planned=True)
    columns = plan_columns(from_date, to_date)
    return render_to_response('distribution/dojo_member_plans.html', 
        {
            'from_date': from_date,
            'to_date': to_date,
            'columns': columns,
            'column_count': len(columns),
            'member': member,
            'from_datestring': from_datestring,
            'to_datestring': to_datestring,
            'plan_type': plan_type,
            'tabnav': "distribution/tabnav.html",
        }, context_instance=RequestContext(request))


@login_required
def json_member_plans(request, from_date, to_date, member_id):
    #import pdb; pdb.set_trace()
    try:
        member = Party.objects.get(pk=member_id)
    except Party.DoesNotExist:
        raise Http404
    try:
        from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
        to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    if member.is_customer():
        plan_type = "Consumption"
        products = CustomerProduct.objects.filter(customer=member, planned=True)
    else:
        plan_type = "Production"
        #products = ProducerProduct.objects.filter(producer=member, planned=True)
        products = [plan.product for plan in
                    ProductPlan.objects.filter(member=member)]
        products = list(set(products))

    rows = plans_for_dojo(member, products, from_date, to_date)
    count = len(rows)
    try:
        range = request.META["HTTP_RANGE"]
        range = range.split("=")[1]
        range = range.split("-")
        range_start = int(range[0])
        range_end = int(range[1])
    except KeyError:
        range_start = 0
        range_end = count
    if count < range_end:
        range_end = count
    rows = rows[range_start:range_end + 1]
    data = simplejson.dumps(rows)
    response = HttpResponse(data, mimetype="text/json-comment-filtered")
    response['Cache-Control'] = 'no-cache'
    response['Content-Range'] = "".join(["items ", str(range_start),
        "-", str(range_end), "/", str(count + 1)])
    return response

@login_required
def supply_and_demand_week(request, tabs, week_date):
    try:
        week_date = datetime.datetime(*time.strptime(week_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    sdtable = supply_demand_weekly_table(week_date)
    tabnav = "distribution/tabnav.html"
    if tabs == "P":
        tabnav = "producer/producer_tabnav.html"
    return render_to_response('distribution/supply_demand_week.html', 
        {
            'week_date': week_date,
            'sdtable': sdtable,
            'tabnav': tabnav,
        }, context_instance=RequestContext(request))

@login_required
def dojo_supply_and_demand_week(request, tabs, week_date):
    try:
        week_date = datetime.datetime(*time.strptime(week_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    sdtable = dojo_supply_demand_weekly_table(week_date)
    columns = sdtable.columns
    tabnav = "distribution/tabnav.html"
    if tabs == "P":
        tabnav = "producer/producer_tabnav.html"
    return render_to_response('distribution/dojo_supply_demand_week.html', 
        {
            'week_date': week_date,
            'columns': columns,
            'column_count': len(columns),
            'tabnav': tabnav,
        }, context_instance=RequestContext(request))

@login_required
def json_supply_and_demand_week(request, week_date):
    try:
        week_date = datetime.datetime(*time.strptime(week_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    tbl = dojo_supply_demand_weekly_table(week_date)
    rows = tbl.rows
    count = len(rows)
    try:
        range = request.META["HTTP_RANGE"]
        range = range.split("=")[1]
        range = range.split("-")
        range_start = int(range[0])
        range_end = int(range[1])
    except KeyError:
        range_start = 0
        range_end = count
    if count < range_end:
        range_end = count
    rows = rows[range_start:range_end + 1]
    data = simplejson.dumps(rows)
    response = HttpResponse(data, mimetype="text/json-comment-filtered")
    response['Cache-Control'] = 'no-cache'
    response['Content-Range'] = "".join(["items ", str(range_start),
        "-", str(range_end), "/", str(count + 1)])
    return response




@login_required
def produceravail(request, prod_id, year, month, day):
    availdate = datetime.date(int(year), int(month), int(day))
    availdate = availdate - datetime.timedelta(days=datetime.date.weekday(availdate)) + datetime.timedelta(days=2)
    weekstart = availdate - datetime.timedelta(days=datetime.date.weekday(availdate))
    try:
        producer = Party.objects.get(pk=prod_id)
        inventory = InventoryItem.objects.filter(
            Q(producer=producer) &
            (Q(onhand__gt=0) | Q(inventory_date__range=(weekstart, availdate))))
    except Party.DoesNotExist:
        raise Http404
    return render_to_response('distribution/producer_avail.html', 
        {'producer': producer, 
         'avail_date': weekstart, 
         'inventory': inventory }, context_instance=RequestContext(request))

@login_required
def meatavail(request, prod_id, year, month, day):
    availdate = datetime.date(int(year), int(month), int(day))
    availdate = availdate - datetime.timedelta(days=datetime.date.weekday(availdate)) + datetime.timedelta(days=5)
    weekstart = availdate - datetime.timedelta(days=datetime.date.weekday(availdate))
    try:
        producer = Party.objects.get(pk=prod_id)
        inventory = InventoryItem.objects.filter(
            Q(producer=producer) &
            (Q(onhand__gt=0) | Q(inventory_date__range=(weekstart, availdate))))
    except Party.DoesNotExist:
        raise Http404
    return render_to_response('distribution/meat_avail.html', 
        {'producer': producer, 
         'avail_date': weekstart, 
         'inventory': inventory }, context_instance=RequestContext(request))


@login_required
def all_avail(request):

    return list_detail.object_list(
        request,
        queryset = AvailItem.objects.select_related().order_by(
            'distribution_availproducer.avail_date', 'distribution_product.short_name', 'distribution_producer.short_name'),
        template_name = "distribution/avail_list.html",
    )


#def welcome(request):
#    return render_to_response('welcome.html')

#changed help to flatpage
#def help(request):
#    return render_to_response('distribution/help.html')


class ProductActivity():
    def __init__(self, category, product, avail, ordered, delivered, lots):
        self.category = category
        self.product = product
        self.avail = avail
        self.ordered = ordered
        self.delivered = delivered
        self.lots = lots

@login_required
def dashboard(request):
    try:
        fn = food_network()
        food_network_name = fn.long_name
    except FoodNetwork.DoesNotExist:
        fn = None
        food_network_name = ""
    
    thisdate = ""
    week_form = ""
    plans = []
    shorts = []
    orders = []
    if fn:
        thisdate = current_week()
        monday = thisdate - datetime.timedelta(days=datetime.date.weekday(thisdate))
        saturday = monday + datetime.timedelta(days=5)
        week_form = CurrentWeekForm(initial={"current_week": thisdate})
        plans = weekly_production_plans(thisdate)
        shorts = shorts_for_week()
        orders = Order.objects.filter(
            delivery_date__range=(thisdate, saturday)).exclude(state="Unsubmitted")

    return render_to_response('distribution/dashboard.html', 
        {'plans': plans,
         'shorts': shorts,
         'orders': orders,
         'delivery_date': thisdate,
         'week_form': week_form,
         'food_network_name': food_network_name, 
         }, context_instance=RequestContext(request))

@login_required
def reset_week(request):
    if request.method == "POST":
        try:
            fn = food_network()
            food_network_name = fn.long_name
            form = CurrentWeekForm(request.POST)
            if form.is_valid():
                current_week = form.cleaned_data['current_week']
                fn.current_week = current_week
                fn.save()
                #todo: nips shd be rethought with delivery skeds
                #import pdb; pdb.set_trace()
                nips = ProducerProduct.objects.filter(
                    inventoried=False, 
                    default_avail_qty__gt=0, 
                    product__sellable=True)
                for nip in nips:
                    item, created = InventoryItem.objects.get_or_create(
                        product=nip.product,
                        producer=nip.producer,
                        inventory_date=current_week,
                        planned=nip.default_avail_qty)
                    if created:
                        item.remaining = nip.default_avail_qty
                        item.save()
                        
        except FoodNetwork.DoesNotExist:
            pass
    return HttpResponseRedirect("/distribution/dashboard/")   

@login_required
def all_orders(request):
    return list_detail.object_list(
        request,
        queryset = OrderItem.objects.all(),
        template_name = "distribution/order_list.html",
    )

@login_required
def all_deliveries(request):
    return list_detail.object_list(
        request,
        queryset = InventoryTransaction.objects.filter(transaction_type='Delivery'),
        template_name = "distribution/delivery_list.html",
    )

@login_required
def orders_with_deliveries(request, year, month, day):
    thisdate = datetime.date(int(year), int(month), int(day))
    orderitem_list = OrderItem.objects.select_related().filter(order__delivery_date=thisdate).order_by('order', 'distribution_product.short_name')
    return render_to_response('distribution/order_delivery_list.html', 
        {'delivery_date': thisdate, 
         'orderitem_list': orderitem_list}, context_instance=RequestContext(request))

@login_required
def payment_selection(request):
    thisdate = current_week()
    init = {
        'from_date': thisdate - datetime.timedelta(days=7),
        'to_date': thisdate + datetime.timedelta(days=5),
    }
    if request.method == "POST":
        ihform = PaymentSelectionForm(request.POST)  
        if ihform.is_valid():
            ihdata = ihform.cleaned_data
            producer_id = ihdata['producer']
            from_date = ihdata['from_date'].strftime('%Y_%m_%d')
            to_date = ihdata['to_date'].strftime('%Y_%m_%d')
            due = 1 if ihdata['due'] else 0
            paid_member = ihdata['paid_member']
            return HttpResponseRedirect('/%s/%s/%s/%s/%s/%s/'
               % ('distribution/producerpayments', producer_id, from_date, to_date, due, paid_member))
    else:
        #ihform = PaymentSelectionForm(initial={'from_date': thisdate, 'to_date': thisdate })
    #return render_to_response('distribution/payment_selection.html', {'avail_date': thisdate, 'header_form': ihform})
        ihform = PaymentSelectionForm(initial=init)
    return render_to_response('distribution/payment_selection.html', 
        {'header_form': ihform}, context_instance=RequestContext(request))

@login_required
def statement_selection(request):
    if request.method == "POST":
        hdrform = StatementSelectionForm(request.POST)  
        if hdrform.is_valid():
            hdrdata = hdrform.cleaned_data
            from_date = hdrdata['from_date'].strftime('%Y_%m_%d')
            to_date = hdrdata['to_date'].strftime('%Y_%m_%d')
            return HttpResponseRedirect('/%s/%s/%s/'
               % ('distribution/statements', from_date, to_date))
    else:
        hdrform = StatementSelectionForm()
    return render_to_response('distribution/statement_selection.html', 
        {'header_form': hdrform}, context_instance=RequestContext(request))

@login_required
def statements(request, from_date, to_date):
    try:
        from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
        to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
        
    try:
        network = food_network()
    except FoodNetwork.DoesNotExist:
        return render_to_response('distribution/network_error.html')
    
    payments = Payment.objects.filter(
        transaction_date__gte=from_date, 
        transaction_date__lte=to_date).exclude(to_whom=network)
    return render_to_response('distribution/statements.html', 
        {'payments': payments, 
         'network': network, }, context_instance=RequestContext(request))   

@login_required
def producer_payments(request, prod_id, from_date, to_date, due, paid_member):
    try:
        from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
        to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
        due = int(due)
    except ValueError:
            raise Http404
    show_payments = True
    if paid_member == 'unpaid':
        show_payments=False
    prod_id = int(prod_id)
    if prod_id:
        try:
            producer = Party.objects.get(pk=prod_id)
        except Party.DoesNotExist:
            raise Http404
        producer = one_producer_payments(producer, from_date, to_date, due, paid_member)
        return render_to_response('distribution/one_producer_payments.html', 
              {'from_date': from_date, 
               'to_date': to_date, 
               'producer': producer, 
               'show_payments': show_payments }, context_instance=RequestContext(request))
    else:
        producer_list = all_producer_payments(from_date, to_date, due, paid_member)
        return render_to_response('distribution/producer_payments.html', 
            {'from_date': from_date, 
             'to_date': to_date, 
             'producers': producer_list, 
             'show_payments': show_payments }, context_instance=RequestContext(request))

def one_producer_payments(producer, from_date, to_date, due, paid_member):  

    # Collect the transactions

    deliveries = []
    processings = []
    transportations = []

    tx_types = ["Delivery", "Issue"]

    # filter by date and producer

    dels = InventoryTransaction.objects.filter(
        inventory_item__producer=producer,
        transaction_date__range=(from_date, to_date),
        transaction_type__in=tx_types).order_by('order_item')

    procs = ServiceTransaction.objects.filter(
        from_whom=producer,
        transaction_date__range=(from_date, to_date))

    trans = TransportationTransaction.objects.filter(
        from_whom=producer,
        transaction_date__range=(from_date, to_date))

    # filter by payment status

    if due and paid_member == 'paid':

        for tx in dels:
            if tx.is_due():
                if tx.is_paid():
                    deliveries.append(tx)

        for proc in procs:
            if proc.is_due():
                if proc.is_paid():
                    processings.append(proc)
 
        for tx in trans:
            if tx.is_due():
                if tx.is_paid():
                    transportations.append(tx)

    elif due and paid_member == 'unpaid':

        for tx in dels:
            if tx.is_due():
                if not tx.is_paid():
                    deliveries.append(tx)

        for proc in procs:
            if proc.is_due():
                if not proc.is_paid():
                    processings.append(proc)
 
        for tx in trans:
            if tx.is_due():
                if not tx.is_paid():
                    transportations.append(tx)

    elif due:

        for tx in dels:
            if tx.is_due():
                deliveries.append(tx)

        for proc in procs:
            if proc.is_due():
                processings.append(proc)
 
        for tx in trans:
            if tx.is_due():
                transportations.append(tx)


    elif paid_member == 'paid':

        for tx in dels:
            if tx.due_to_member():
                if tx.is_paid():
                    deliveries.append(tx)
           
        for proc in procs:
            if proc.is_paid():
                processings.append(proc)
            
        for tx in trans:
            if tx.is_paid():
                transportations.append(tx)

    elif paid_member == 'unpaid':

        for tx in dels:
            if tx.due_to_member():
                if not tx.is_paid():
                    deliveries.append(tx)

        for tx in trans:
            if not tx.is_paid():
                transportations.append(tx)

        for proc in procs:
            if not proc.is_paid():
                processings.append(proc)

    else:
        for tx in dels:
            if tx.due_to_member():
                deliveries.append(tx)
        transportations = trans
        processings = procs

    damaged = []                
    if paid_member == 'paid':
        txs = InventoryTransaction.objects.filter(
            inventory_item__producer=producer,
            transaction_date__range=(from_date, to_date), 
            transaction_type='Damage').order_by('inventory_item')
        for tx in txs:
            if tx.is_paid():
                damaged.append(tx)       
    elif paid_member == 'unpaid':
        txs = InventoryTransaction.objects.filter(
            inventory_item__producer=producer,
            transaction_date__range=(from_date, to_date),
            transaction_type='Damage').order_by('inventory_item')
        for tx in txs:
            if not tx.is_paid():
                damaged.append(tx) 
    else:   
        damaged = InventoryTransaction.objects.filter(
            inventory_item__producer=producer,
            transaction_date__range=(from_date, to_date), 
            transaction_type='Damage').order_by('inventory_item')
    
    rejected = InventoryTransaction.objects.filter(
        transaction_date__range=(from_date, to_date), 
        transaction_type='Reject').order_by('inventory_item')       
                
        
    rejected = InventoryTransaction.objects.filter(
        transaction_date__range=(from_date, to_date),
        transaction_type='Reject', 
        inventory_item__producer=producer).order_by('inventory_item')

    # Total    
    total_due = 0
    producer.deliveries = deliveries
    producer.damaged = damaged
    producer.rejected = rejected
    producer.processes = processings
    producer.transportations = transportations

    for delivery in deliveries:
        total_due += delivery.due_to_member()
    for damage in damaged:
        total_due += damage.due_to_member()

    for proc in processings:
        total_due += proc.due_to_member()
    for tx in transportations:
        total_due += tx.due_to_member()
    producer.total_due = total_due
    return producer

def all_producer_payments(from_date, to_date, due, paid_member):
    try:
        network = food_network()
    except FoodNetwork.DoesNotExist:
        return render_to_response('distribution/network_error.html')

    delivery_producers = {}
    processors = {}
    transporters = {}
    damage_producers = {}
    reject_producers = {}
    
    # Logic summary:
    # 1. Collect and filter the transactions (deliveries, damages, rejects, processing and transportation)
    # 2. Organize and total the transactions by party
    
    # Collect the transactions

    deliveries = []
    processings = []
    transportations = []

    tx_types = ["Delivery", "Issue"]

    # filter by date

    dels = InventoryTransaction.objects.filter(
        transaction_date__range=(from_date, to_date),
        transaction_type__in=tx_types).order_by('order_item')

    procs = ServiceTransaction.objects.filter(
        transaction_date__range=(from_date, to_date))

    trans = TransportationTransaction.objects.filter(
        transaction_date__range=(from_date, to_date)).exclude(from_whom=network)

    # filter by payment status

    if due and paid_member == 'paid':

        for tx in dels:
            if tx.is_due():
                if tx.is_paid():
                    deliveries.append(tx)

        for proc in procs:
            if proc.is_due():
                if proc.is_paid():
                    processings.append(proc)
 
        for tx in trans:
            if tx.is_due():
                if tx.is_paid():
                    transportations.append(tx)

    elif due and paid_member == 'unpaid':

        for tx in dels:
            if tx.is_due():
                if not tx.is_paid():
                    deliveries.append(tx)

        for proc in procs:
            if proc.is_due():
                if not proc.is_paid():
                    processings.append(proc)
 
        for tx in trans:
            if tx.is_due():
                if not tx.is_paid():
                    transportations.append(tx)

    elif due:

        for tx in dels:
            if tx.is_due():
                deliveries.append(tx)

        for proc in procs:
            if proc.is_due():
                processings.append(proc)
 
        for tx in trans:
            if tx.is_due():
                transportations.append(tx)


    elif paid_member == 'paid':

        for tx in dels:
            if tx.due_to_member():
                if tx.is_paid():
                    deliveries.append(tx)
           
        for proc in procs:
            if proc.is_paid():
                processings.append(proc)
            
        for tx in trans:
            if tx.is_paid():
                transportations.append(tx)

    elif paid_member == 'unpaid':

        for tx in dels:
            if tx.due_to_member():
                if not tx.is_paid():
                    deliveries.append(tx)

        for tx in trans:
            if not tx.is_paid():
                transportations.append(tx)

        for proc in procs:
            if not proc.is_paid():
                processings.append(proc)

    else:
        for tx in dels:
            if tx.due_to_member():
                deliveries.append(tx)
        transportations = trans
        processings = procs

    damaged = []                
    if paid_member == 'paid':
        txs = InventoryTransaction.objects.filter(
            transaction_date__range=(from_date, to_date), 
            transaction_type='Damage').order_by('inventory_item')
        for tx in txs:
            if tx.is_paid():
                damaged.append(tx)       
    elif paid_member == 'unpaid':
        txs = InventoryTransaction.objects.filter(
            transaction_date__range=(from_date, to_date),
            transaction_type='Damage').order_by('inventory_item')
        for tx in txs:
            if not tx.is_paid():
                damaged.append(tx) 
    else:   
        damaged = InventoryTransaction.objects.filter(
            transaction_date__range=(from_date, to_date), 
            transaction_type='Damage').order_by('inventory_item')
    
    rejected = InventoryTransaction.objects.filter(
        transaction_date__range=(from_date, to_date), 
        transaction_type='Reject').order_by('inventory_item')
        
    # Organize and total the transactions by party
    
    # Organize
    for delivery in deliveries:
        prod = delivery.inventory_item.producer
        delivery_producers.setdefault(prod, []).append(delivery)

    for proc in processings:
        processor = proc.from_whom
        processors.setdefault(processor, []).append(proc)
    for tx in transportations:
        dist = tx.from_whom
        transporters.setdefault(dist, []).append(tx)

    for damage in damaged:
        prod = damage.inventory_item.producer
        damage_producers.setdefault(prod, []).append(damage)
    for reject in rejected:
        prod = reject.inventory_item.producer
        reject_producers.setdefault(prod, []).append(reject)
    producer_list = []
    
    # Total
    for prod in delivery_producers:
        prod_deliveries = delivery_producers[prod]
        delivery_total_due = Decimal("0")
        delivery_total_paid = Decimal("0")
        grand_total_due = Decimal("0")
        grand_total_paid = Decimal("0")
        for delivery in prod_deliveries:
            due_to_member = delivery.due_to_member()
            delivery_total_due += due_to_member
            grand_total_due += due_to_member
            delivery_total_paid += delivery.paid_amount()
            grand_total_paid += delivery.paid_amount()
        if grand_total_due > 0:
            producer = prod
            producer.delivery_total_due = delivery_total_due
            producer.delivery_total_paid = delivery_total_paid
            producer.grand_total_due = grand_total_due
            producer.grand_total_paid = grand_total_paid
            producer.deliveries = prod_deliveries
            producer_list.append(producer)
    for prod in processors:
        prod_processes = processors[prod]
        process_total_due = Decimal("0")
        process_total_paid = Decimal("0")
        for process in prod_processes:
            process_total_due += process.due_to_member()
            process_total_paid += process.paid_amount()
        if process_total_due > 0:
            producer = prod
            producer.process_total_due = process_total_due
            producer.process_total_paid = process_total_paid
            try:
                grand_total_due = producer.grand_total_due
                grand_total_paid = producer.grand_total_paid
            except:
                grand_total_due = Decimal("0")
                grand_total_paid = Decimal("0")
            grand_total_due += process_total_due
            grand_total_paid += process_total_paid
            producer.grand_total_due = grand_total_due
            producer.grand_total_paid = grand_total_paid
            producer.processes = prod_processes
            producer_list.append(producer)
    for dist in transporters:
        trans_tx = transporters[dist]
        transportation_total_due = Decimal("0")
        transportation_total_paid = Decimal("0")
        for tx in trans_tx:
            due_to_member = tx.due_to_member()
            transportation_total_due += due_to_member
            transportation_total_paid += tx.paid_amount()
        if transportation_total_due > 0:
            producer = dist
            producer.transportation_total_due = transportation_total_due
            producer.transportation_total_paid = transportation_total_paid
            try:
                grand_total_due = producer.grand_total_due
                grand_total_paid = producer.grand_total_paid
            except:
                grand_total_due = Decimal("0")
                grand_total_paid = Decimal("0")
            grand_total_due += transportation_total_due
            grand_total_paid += transportation_total_paid
            producer.grand_total_due = grand_total_due
            producer.grand_total_paid = grand_total_paid
            producer.transportations = trans_tx
            producer_list.append(producer)
    for prod in damage_producers:
        prod_damages = damage_producers[prod]
        damage_total_due = Decimal("0")
        damage_total_paid = Decimal("0")
        for damage in prod_damages:
            due_to_member = damage.due_to_member()
            damage_total_due += due_to_member
            damage_total_paid += tx.paid_amount()
        if damage_total_due > 0:
            producer = prod # correct?
            if producer in producer_list:
                producer = producer_list[producer_list.index(producer)]
            else:
                producer_list.append(producer)
            producer.damage_total_due = damage_total_due
            producer.damage_total_paid = damage_total_paid
            grand_total_due = producer.grand_total_due if producer.grand_total_due else 0
            grand_total_paid = producer.grand_total_paid if producer.grand_total_paid else 0
            grand_total_due += damage_total_due
            grand_total_paid += damage_total_paid
            producer.grand_total_due = grand_total_due
            producer.grand_total_paid = grand_total_paid
            producer.damaged = prod_damages
    for prod in reject_producers:
        producer = prod
        if producer in producer_list:
            producer = producer_list[producer_list.index(producer)]
        else:
            producer_list.append(producer)
        producer.rejected = reject_producers[prod]
        
    producer_list.sort(lambda x, y: cmp(x.short_name, y.short_name))
    return producer_list

@login_required
def payment(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)
    return render_to_response('distribution/payment.html', 
        {'payment': payment}, context_instance=RequestContext(request))

@login_required
def customer_payment(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)
    return render_to_response('distribution/customer_payment.html', 
        {'payment': payment}, context_instance=RequestContext(request))

@login_required
def payment_update_selection(request):
    try:
        food_net = food_network()
    except FoodNetwork.DoesNotExist:
        return render_to_response('distribution/network_error.html')
    msform = PaymentUpdateSelectionForm(data=request.POST or None)
    csform = CustomerPaymentSelectionForm(data=request.POST or None)
    if request.method == "POST":
        if request.POST.get('submit-member-payments'):
            if msform.is_valid():
                msdata = msform.cleaned_data
                producer = msdata['producer'] if msdata['producer'] else 0
                payment = msdata['payment'] if msdata['payment'] else 0
                return HttpResponseRedirect('/%s/%s/%s/'
                   % ('distribution/paymentupdate', producer, payment))
    if request.method == "POST":
        if request.POST.get('submit-customer-payments'):
            if csform.is_valid():
                csdata = csform.cleaned_data
                customer = csdata['customer'] if csdata['customer'] else 0
                payment = csdata['payment'] if csdata['payment'] else 0
                return HttpResponseRedirect('/%s/%s/%s/'
                   % ('distribution/customerpaymentupdate', customer, payment))
    return render_to_response('distribution/payment_update_selection.html', {
        'member_selection_form': msform,
        'customer_selection_form': csform,
    }, context_instance=RequestContext(request))

@login_required
def payment_update(request, producer_id, payment_id):

    try:
        food_net = food_network()
    except FoodNetwork.DoesNotExist:
        return render_to_response('distribution/network_error.html')

    producer_id = int(producer_id)
    if producer_id:
        producer = get_object_or_404(Party, pk=producer_id)
    else:
        producer = ''

    payment_id = int(payment_id)
    if payment_id:
        payment = get_object_or_404(Payment, pk=payment_id)
        producer = payment.to_whom
    else:
        payment = ''

    if request.method == "POST":
        if payment:
            paymentform = PaymentForm(request.POST, instance=payment)
        else:
            paymentform = PaymentForm(request.POST)
        itemforms = create_payment_transaction_forms(producer, payment, request.POST)     
        if paymentform.is_valid() and all([itemform.is_valid() for itemform in itemforms]):
            the_payment = paymentform.save(commit=False)
            the_payment.from_whom = food_net
            the_payment.save()
            for itemform in itemforms:
                data = itemform.cleaned_data
                paid = data['paid']
                tx_id = data['transaction_id']
                tx_type = data['transaction_type']
                #import pdb; pdb.set_trace()
                if tx_type == 'Transportation':
                    tx = TransportationTransaction.objects.get(pk=tx_id)
                elif tx_type == 'Service':
                    tx = ServiceTransaction.objects.get(pk=tx_id)
                else:
                    tx = InventoryTransaction.objects.get(pk=tx_id)
                if paid:
                    # todo: assuming here that payments always pay the full tx.due_to_member
                    if not tx.is_paid():
                        tp = TransactionPayment(
                            paid_event = tx,
                            payment = the_payment,
                            amount_paid = tx.due_to_member())
                        tp.save()
                else:
                    tx.delete_payments()
            return HttpResponseRedirect('/%s/%s/'
               % ('distribution/payment', the_payment.id))
        #else:
        #    import pdb; pdb.set_trace()
    else:
        if payment:
            paymentform = PaymentForm(instance=payment)
        else:
            paymentform = PaymentForm(initial={'transaction_date': datetime.date.today(),})
        paymentform.fields['to_whom'].choices = [(producer.id, producer.short_name)]
        itemforms = create_payment_transaction_forms(producer, payment)
    return render_to_response('distribution/payment_update.html', 
        {'payment': payment, 
         'payment_form': paymentform, 
         'item_forms': itemforms}, context_instance=RequestContext(request))

@login_required
def customer_payment_update(request, customer_id, payment_id):

    try:
        food_net = food_network()
    except FoodNetwork.DoesNotExist:
        return render_to_response('distribution/network_error.html')

    customer_id = int(customer_id)
    if customer_id:
        customer = get_object_or_404(Party, pk=customer_id)
    else:
        customer = ''

    payment_id = int(payment_id)
    if payment_id:
        payment = get_object_or_404(Payment, pk=payment_id)
        #import pdb; pdb.set_trace()
        customer = payment.from_whom
    else:
        payment = ''

    if payment:
        paymentform = CustomerPaymentForm(data=request.POST or None, instance=payment)
    else:
        paymentform = CustomerPaymentForm(data=request.POST or None,
            initial={"transaction_date": datetime.date.today()})

    itemforms = create_customer_payment_transaction_forms(
        customer=customer, payment=payment, data=request.POST or None)

    if request.method == "POST":
        if paymentform.is_valid() and all([itemform.is_valid() for itemform in itemforms]):
            the_payment = paymentform.save(commit=False)
            the_payment.from_whom = customer
            the_payment.to_whom = food_net
            the_payment.save()
            for itemform in itemforms:
                data = itemform.cleaned_data
                paid = data['paid']
                order_id = data['order_id']
                order = Order.objects.get(pk=order_id)
                if paid:
                    # todo: assuming here that payments always pay the full tx.due_to_member
                    # todo: register_payment shd work like delete_payments
                    if not order.is_paid():
                        cp = CustomerPayment(
                            paid_order = order,
                            payment = the_payment,
                            amount_paid = order.grand_total())
                        cp.save()
                        order.register_customer_payment()
                else:
                    order.delete_payments()
            return HttpResponseRedirect('/%s/%s/'
               % ('distribution/customerpayment', the_payment.id))
        #else:
            #import pdb; pdb.set_trace()
        
    return render_to_response('distribution/customer_payment_update.html', 
        {'payment': payment,
         'customer': customer,
         'payment_form': paymentform, 
         'item_forms': itemforms}, context_instance=RequestContext(request))


def json_payments(request, producer_id):
    # todo: shd limit to a few most recent payments
    data = serializers.serialize("json", EconomicEvent.objects.payments_to_party(producer_id))
    return HttpResponse(data, mimetype="text/json-comment-filtered")

def json_products(request, product_id=None):
    #import pdb; pdb.set_trace()
    if product_id:
        if request.method == "GET":
            return DojoDataJSONResponse(Product.objects.get(id=product_id), exclude_fields=("parent",))
        elif request.method == "PUT":
            #import pdb; pdb.set_trace()
            product = Product.objects.get(id=product_id)
            data = simplejson.loads(request.raw_post_data)
            price = data["price"]
            if is_number(price):
                product.price=Decimal(price)
                product.save()
            return DojoDataJSONResponse(Product.objects.get(id=product_id), exclude_fields=("parent",))
    else:
        return DojoDataJSONResponse(Product.objects.all(), exclude_fields=("parent",))


@login_required
def dojo_products(request):

    return render_to_response('distribution/dojo_products.html', context_instance=RequestContext(request))


@login_required
def invoice_selection(request):
    init = {"delivery_date": current_week(),}
    unpaid_invoices = Order.objects.filter(
        state="Delivered")
    if request.method == "POST":
        dsform = DeliverySelectionForm(request.POST)  
        if dsform.is_valid():
            dsdata = dsform.cleaned_data
            cust_id = dsdata['customer']
            ord_date = dsdata['delivery_date']
            return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
               % ('distribution/invoices', cust_id, ord_date.year, ord_date.month, ord_date.day))
    else:
        dsform = DeliverySelectionForm(initial=init)
    return render_to_response('distribution/invoice_selection.html', 
        {'header_form': dsform,
         'unpaid_invoices': unpaid_invoices,
        }, context_instance=RequestContext(request))

@login_required
def invoices(request, cust_id, year, month, day):
    try:
        fn = food_network()
    except FoodNetwork.DoesNotExist:
        return render_to_response('distribution/network_error.html')
    thisdate = datetime.date(int(year), int(month), int(day))
    cust_id = int(cust_id)
    if cust_id:
        try:
            customer = Customer.objects.get(pk=cust_id)
        except Customer.DoesNotExist:
            raise Http404
    else:
        customer = ''
    #todo: shd include only unpaid but delivered orders?
    if customer:
        orders = Order.objects.filter(
            customer=customer, 
            delivery_date=thisdate,
            state__contains="Delivered"
        )
    else:
        orders = Order.objects.filter(
            delivery_date=thisdate,
            state__contains="Delivered"
        )
    return render_to_response('distribution/invoices.html', {
        'orders': orders, 
        'network': fn,
        'cust_id': cust_id,
        'year': year,
        'month': month,
        'day': day,
        'emails': True,
        'tabnav': "distribution/tabnav.html",
    }, context_instance=RequestContext(request))


@login_required
def send_invoices(request, cust_id, year, month, day):
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        if notification:
            try:
                fn = food_network()
            except FoodNetwork.DoesNotExist:
                return render_to_response('distribution/network_error.html')
        thisdate = datetime.date(int(year), int(month), int(day))
        cust_id = int(cust_id)
        if cust_id:
            try:
                customer = Customer.objects.get(pk=cust_id)
            except Customer.DoesNotExist:
                raise Http404
        else:
            customer = ''
        if customer:
            orders = Order.objects.filter(
                customer=customer, 
                delivery_date=thisdate,
                state__contains="Delivered"
            )
        else:
            orders = Order.objects.filter(
                delivery_date=thisdate,
                state__contains="Delivered"
            )
        #import pdb; pdb.set_trace()
        for order in orders:
            users = [order.customer, fn]
            if order.created_by:
                if request.user.id == order.created_by.id:
                    parties = request.user.parties.all()
                    if parties:
                        user_party = parties[0]
                        if user_party.id == order.customer.id:
                            if not user.email == order.customer.email:
                                users.append(request.user)             
            notification.send(users, "distribution_invoice", {
                "order": order,
                "network": fn,
            })
            request.user.message_set.create(message="Invoice emails have been sent")
        return HttpResponseRedirect(request.POST["next"])

@login_required
def send_order_emails(request, cust_id, year, month, day):
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        next = request.POST.get("next")
        if not next:
            next = "/distribution/dashboard/"
        if notification:
            try:
                fn = food_network()
            except FoodNetwork.DoesNotExist:
                return render_to_response('distribution/network_error.html')
        thisdate = datetime.date(int(year), int(month), int(day))
        cust_id = int(cust_id)
        if cust_id:
            try:
                customer = Customer.objects.get(pk=cust_id)
            except Customer.DoesNotExist:
                raise Http404
        else:
            customer = ''
        if customer:
            orders = Order.objects.filter(
                customer=customer, 
                delivery_date=thisdate,
            )
        else:
            orders = Order.objects.filter(
                delivery_date=thisdate,
            )
        #import pdb; pdb.set_trace()
        for order in orders:
            users = [order.customer, fn]
            if order.created_by:
                if request.user.id == order.created_by.id:
                    parties = request.user.parties.all()
                    if parties:
                        user_party = parties[0]
                        if user_party.id == order.customer.id:
                            if not user.email == order.customer.email:
                                users.append(request.user)             
            notification.send(users, "distribution_order", {
                "order": order,
                "network": fn,
            })
            request.user.message_set.create(message="Order emails have been sent")
        return HttpResponseRedirect(next)

# todo: replace with new Processes
def create_meat_item_forms(producer, avail_date, data=None):
    monday = avail_date - datetime.timedelta(days=datetime.date.weekday(avail_date))
    saturday = monday + datetime.timedelta(days=5)
    items = InventoryItem.objects.filter(
        producer=producer, 
        product__meat=True,
        inventory_date__range=(monday, saturday))
    
    initial_data = []
        
    item_dict = {}
    for item in items:
        item_dict[item.product.id] = item
        processor_id = ""
        cost = 0
        try:
            processor_id = item.processing.processor.id
            cost = item.processing.cost
        except Processing.DoesNotExist:
            pass
        custodian_id = ""
        if item.custodian:
            custodian_id = item.custodian.id
        dict ={
            'item_id': item.id,
            'product': item.product.id, 
            'description': item.product.long_name,
            'custodian': custodian_id,
            'inventory_date': item.inventory_date,
            'planned': item.planned,
            'received': item.received,
            'notes': item.notes,
            'processor': processor_id,
            'cost': cost }
        initial_data.append(dict)
        
    plans = ProductPlan.objects.filter(
        producer=producer, 
        product__meat=True,
        from_date__lte=avail_date, 
        to_date__gte=saturday)
    product_list = []
    for plan in plans:
        product_list.append(plan.product)
        
    form_list = []

    for plan in plans:
        try:
            item = item_dict[plan.product.id]
        except KeyError:
            item = False
        if not item:
            dict = {
                'product': plan.product.id, 
                'description': plan.product.long_name,
                'inventory_date': avail_date,
                'planned': 0,
                'received': 0,
                'cost': 0,
                'notes': ''}
            initial_data.append(dict)
        
    for i in range(1, 6):
        dict={'inventory_date': avail_date,
            'planned': 0,
            'received': 0,
            'cost': 0}
        initial_data.append(dict)
        
    MeatItemFormSet = formset_factory(MeatItemForm, extra=0)
    formset = MeatItemFormSet(initial=initial_data)
    product_choices = [(prod.id, prod.long_name) for prod in product_list]
    for form in formset.forms:
        form.fields['product'].choices = product_choices
    return formset


# todo: replace with new Processes
@login_required
def meat_update(request, prod_id, year, month, day):
    avail_date = datetime.date(int(year), int(month), int(day))
    try:
        producer = Party.objects.get(pk=prod_id)
    except Party.DoesNotExist:
        raise Http404
    
    if request.method == "POST":
        MeatItemFormSet = formset_factory(MeatItemForm, extra=0)
        formset = MeatItemFormSet(request.POST)
        if formset.is_valid():
            producer_id = request.POST['producer-id']
            producer = Producer.objects.get(pk=producer_id)
            inv_date = request.POST['avail-date']
            for form in formset.forms:
                data = form.cleaned_data
                product = data['product']
                item_id = data['item_id']
                custodian = data['custodian']
                inventory_date = data['inventory_date']
                planned = data['planned']
                received = data['received']
                notes = data['notes']
                processor_id = data['processor']
                cost = data['cost']
                if item_id:
                    item = InventoryItem.objects.get(pk=item_id)
                    item.custodian = custodian
                    item.inventory_date = inventory_date
                    rem_change = planned - item.planned
                    item.planned = planned
                    item.remaining = item.remaining + rem_change
                    oh_change = received - item.received                 
                    item.received = received
                    item.onhand = item.onhand + oh_change
                    item.notes = notes
                    item.save()
                    item_processing = None
                    try:
                        item_processing = item.processing
                    except Processing.DoesNotExist:
                        pass
                    if processor_id:
                        processor = Processor.objects.get(id=processor_id)
                        if item_processing:
                            item_processing.processor = processor
                            item_processing.cost = cost
                            item_processing.save()
                        else:
                            processing = Processing(
                                inventory_item = item,
                                processor=processor,
                                cost=cost).save()
                else:
                    if planned + received > 0:
                        #prodname = data['prodname']
                        #product = Product.objects.get(short_name__exact=prodname)
                        item = form.save(commit=False)
                        item.producer = producer
                        item.custodian = custodian
                        item.inventory_date = inventory_date
                        item.product = product
                        item.remaining = planned
                        item.onhand = received
                        item.notes = notes
                        item.save()
                        if processor_id:
                            processor = Processor.objects.get(id=processor_id)
                            processing = Processing(
                                inventory_item = item,
                                processor=processor,
                                cost=cost).save()
            return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
               % ('distribution/meatavail', producer_id, year, month, day))
                
    else:
        formset = create_meat_item_forms(producer, avail_date, data=None)
        
    return render_to_response('distribution/meat_update.html', {
        'avail_date': avail_date, 
        'producer': producer,
        'formset': formset}, context_instance=RequestContext(request))

@login_required
def process_selection(request):
    process_date = current_week()
    monday = process_date - datetime.timedelta(days=datetime.date.weekday(process_date))
    saturday = monday + datetime.timedelta(days=5)
    #initial_data = {"process_date": process_date}
    processes = Process.objects.filter(process_date__range=(monday, saturday))
    #psform = ProcessSelectionForm(data=request.POST or None, initial=initial_data)
    psform = ProcessSelectionForm(data=request.POST or None)
    if request.method == "POST":
        if psform.is_valid():
            data = psform.cleaned_data
            process_type_id = data['process_type']
            return HttpResponseRedirect('/%s/%s/'
               % ('distribution/newprocess', process_type_id))
    return render_to_response('distribution/process_selection.html', {
        'process_date': process_date,
        'header_form': psform,
        'processes': processes,}, context_instance=RequestContext(request))

@login_required
def new_process(request, process_type_id):
    try:
        foodnet = food_network()
    except FoodNetwork.DoesNotExist:
        return render_to_response('distribution/network_error.html')

    weekstart = current_week()
    weekend = weekstart + datetime.timedelta(days=5)
    expired_date = weekstart + datetime.timedelta(days=5)
    pt = get_object_or_404(ProcessType, id=process_type_id)

    input_types = pt.input_type.stockable_children()
    input_select_form = None
    input_create_form = None
    input_lot_qties = []
    if pt.use_existing_input_lot:
        input_lots = InventoryItem.objects.filter(
            product__in=input_types, 
            inventory_date__lte=weekend,
            expiration_date__gte=expired_date,
            remaining__gt=Decimal("0"))
        initial_data = {"quantity": Decimal("0")}

        for lot in input_lots:
            input_lot_qties.append([lot.id, float(lot.avail_qty())])
        if input_lots:
            initial_data = {"quantity": input_lots[0].remaining,}
        input_select_form = InputLotSelectionForm(input_lots, data=request.POST or None, prefix="inputselection", initial=initial_data)
    else:
        input_create_form = InputLotCreationForm(input_types, data=request.POST or None, prefix="inputcreation")

    service_label = "Processing Service"
    service_formset = None
    steps = pt.number_of_processing_steps
    if steps > 1:
        service_label = "Processing Services"
    ServiceFormSet = formset_factory(ProcessServiceForm, extra=steps)
    service_formset = ServiceFormSet(data=request.POST or None, prefix="service")

    output_types = pt.output_type.stockable_children()

    output_label = "Output Lot"
    output_formset = None
    outputs = pt.number_of_output_lots
    if outputs > 1:
        output_label = "Output Lots"
    OutputFormSet = formset_factory(OutputLotCreationFormsetForm, extra=outputs)
    output_formset = OutputFormSet(data=request.POST or None, prefix="output")
    for form in output_formset.forms:
        form.fields['product'].choices = [(prod.id, prod.long_name) for prod in output_types]

    process = None

    if request.method == "POST":
        #import pdb; pdb.set_trace()
        if input_create_form:
            if input_create_form.is_valid():
                data = input_create_form.cleaned_data
                lot = input_create_form.save(commit=False)
                producer = data["producer"]
                qty = data["planned"]
                process = Process(
                    process_type = pt,
                    process_date = weekstart,
                    managed_by = foodnet,
                )
                process.save()
                lot.inventory_date = weekstart
                lot.remaining = qty
                lot.save()
                issue = InventoryTransaction(
                    transaction_type = "Issue",
                    process = process,
                    # todo: is to_whom correct in all these process tx?
                    from_whom = producer, 
                    to_whom = producer, 
                    inventory_item = lot,
                    transaction_date = weekstart,
                    amount = qty)
                issue.save()

        elif input_select_form:
            if input_select_form.is_valid():
                data = input_select_form.cleaned_data
                lot_id = data['lot']
                lot = InventoryItem.objects.get(id=lot_id)
                producer = lot.producer
                qty = data["quantity"]
                process = Process(
                    process_type = pt,
                    process_date = weekstart)
                process.save()
                issue = InventoryTransaction(
                    transaction_type = "Issue",
                    process = process,
                    from_whom = producer, 
                    to_whom = producer, 
                    inventory_item = lot,
                    transaction_date = weekstart,
                    amount = qty)
                issue.save()

        if process:
            if service_formset:
                 # todo: shd be selective, or not?
                if service_formset.is_valid():
                    for service_form in service_formset.forms:
                        tx = service_form.save(commit=False)
                        tx.to_whom = foodnet
                        tx.process = process
                        tx.transaction_date = weekstart
                        tx.save()
            #import pdb; pdb.set_trace()
            if output_formset:
                for form in output_formset.forms:
                    if form.is_valid():
                        data = form.cleaned_data
                        qty = data["planned"]
                        if qty:
                            lot = form.save(commit=False)
                            producer = data["producer"]
                            lot.inventory_date = weekstart
                            lot.save()
                            tx = InventoryTransaction(
                                transaction_type = "Production",
                                process = process,
                                from_whom = producer, 
                                to_whom = producer, 
                                inventory_item = lot,
                                transaction_date = weekstart,
                                amount = qty)
                            tx.save()

            return HttpResponseRedirect('/%s/%s/'
               % ('distribution/process', process.id))

    return render_to_response('distribution/new_process.html', {
        'input_lot_qties': input_lot_qties,
        'input_select_form': input_select_form,
        'input_create_form': input_create_form,
        'service_formset': service_formset,
        'service_label': service_label,
        'output_formset': output_formset,
        'output_label': output_label,
        'tabnav': "distribution/tabnav.html",
        }, context_instance=RequestContext(request))  

@login_required
def edit_process(request, process_id):
    process = get_object_or_404(Process, id=process_id)
    inputs = process.inputs()

    # todo: wip: how to edit a process?


@login_required
def process(request, process_id):
    process = get_object_or_404(Process, id=process_id)
    return render_to_response('distribution/process.html', 
        {"process": process,}, context_instance=RequestContext(request))

@login_required
def delete_process_confirmation(request, process_id):
    if request.method == "POST":
        process = get_object_or_404(Process, id=process_id)
        outputs = []
        outputs_with_lot = []
        for output in process.outputs():
            lot = output.inventory_item
            qty = output.amount
            if lot.planned == qty:
                outputs_with_lot.append(output)
            else:
                outputs.append(output)
        inputs = []
        inputs_with_lot = []
        for inp in process.inputs():
            lot = inp.inventory_item
            qty = inp.amount
            if lot.planned == qty:
                inputs_with_lot.append(inp)
            else:
                inputs.append(inp)
        return render_to_response('distribution/process_delete_confirmation.html', {
            "process": process,
            "outputs": outputs,
            "inputs": inputs,
            "outputs_with_lot": outputs_with_lot,
            "inputs_with_lot": inputs_with_lot,
            }, context_instance=RequestContext(request))

@login_required
def delete_process(request, process_id):
    if request.method == "POST":
        process = get_object_or_404(Process, id=process_id)
        for output in process.outputs():
            lot = output.inventory_item
            qty = output.amount
            output.delete()
            if lot.planned == qty:
                lot.delete()
        for inp in process.inputs():
            lot = inp.inventory_item
            qty = inp.amount
            inp.delete()
            if lot.planned == qty:
                lot.delete()
        for service in process.services():
            service.delete() 
        process.delete()
        #todo: retest, this might not work! 
        return HttpResponseRedirect(reverse("process_selection"))

