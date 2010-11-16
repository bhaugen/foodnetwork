import datetime
import time
from decimal import *

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
from django.forms.models import inlineformset_factory
from django.db.models import Q
from django.contrib.sites.models import Site

from distribution.models import *
from producer.forms import *
from producer.view_helpers import *
from distribution.forms import DateRangeSelectionForm, CurrentWeekForm
from distribution.view_helpers import plan_weeks, create_weekly_plan_forms, SupplyDemandTable

try:
    from notification import models as notification
except ImportError:
    notification = None


def producer_dashboard(request):
    food_network = FoodNetwork.objects.get(pk=1)
    #todo: all uses of the next statement shd be changed
    producer = request.user.parties.all()[0].party
    return render_to_response('producer/producer_dashboard.html', 
        {'producer': producer,
         'food_network': food_network,
         }, context_instance=RequestContext(request))

@login_required
def inventory_selection(request):
    init = {"current_week": current_week(),}
    producer = request.user.parties.all()[0].party
    form = CurrentWeekForm(data=request.POST or None, initial=init)
    if request.method == "POST":
        if form.is_valid():
            data = form.cleaned_data
            inv_date = data['current_week']
            return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
               % ('producer/inventoryupdate', producer.id, inv_date.year, inv_date.month, inv_date.day))
    return render_to_response('producer/inventory_selection.html', {
        'form': form}, context_instance=RequestContext(request))

@login_required
def inventory_update(request, prod_id, year, month, day):
    availdate = datetime.date(int(year), int(month), int(day))
    try:
        producer = Party.objects.get(pk=prod_id)
    except Party.DoesNotExist:
        raise Http404
    if request.method == "POST":
        itemforms = create_inventory_item_forms(producer, availdate, request.POST)
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
                        #item.notes = notes
                        item.save()
            return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
               % ('producer/produceravail', producer_id, year, month, day))
    else:
        itemforms = create_inventory_item_forms(producer, availdate)
    return render_to_response('producer/inventory_update.html', {
        'avail_date': availdate, 
        'producer': producer, 
        'item_forms': itemforms}, context_instance=RequestContext(request))

@login_required
def process_selection(request):
    process_date = current_week()
    monday = process_date - datetime.timedelta(days=datetime.date.weekday(process_date))
    saturday = monday + datetime.timedelta(days=5)
    initial_data = {"process_date": process_date}
    processes = Process.objects.filter(process_date__range=(monday, saturday))
    psform = ProcessSelectionForm(data=request.POST or None, initial=initial_data)
    if request.method == "POST":
        if psform.is_valid():
            data = psform.cleaned_data
            process_date = data['process_date']
            process_type_id = data['process_type']
            return HttpResponseRedirect('/%s/%s/'
               % ('producer/newprocess', process_type_id))
    return render_to_response('producer/process_selection.html', {
        'process_date': process_date,
        'header_form': psform,
        'processes': processes,}, context_instance=RequestContext(request))

from distribution.forms import InputLotSelectionForm, InputLotCreationForm, ProcessServiceForm, OutputLotCreationFormsetForm

@login_required
def new_process(request, process_type_id):
    try:
        foodnet = FoodNetwork.objects.get(pk=1)
    except FoodNetwork.DoesNotExist:
        return render_to_response('distribution/network_error.html')
    producer = request.user.parties.all()[0].party

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

    # todo: default service provider to producer?
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
                    managed_by = producer,
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
        'tabnav': "producer/producer_tabnav.html",
        }, context_instance=RequestContext(request))  

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
    member = request.user.parties.all()[0].party
    member_has_plans = False
    plans = ProductPlan.objects.filter(member=member)
    if plans.count():
        member_has_plans = True

    if request.method == "POST":
        if request.POST.get('submit-supply-demand'):
            sdform = DateRangeSelectionForm(prefix='sd', data=request.POST)  
            if sdform.is_valid():
                data = sdform.cleaned_data
                from_date = data['from_date'].strftime('%Y_%m_%d')
                to_date = data['to_date'].strftime('%Y_%m_%d')
                return HttpResponseRedirect('/%s/%s/%s/'
                    % ('producer/supplydemand', from_date, to_date))
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
                    % ('producer/income', from_date, to_date))
            else:
                psform = PlanSelectionForm(initial=plan_init)
                sdform = DateRangeSelectionForm(prefix='sd', initial=init)
      
        else:
            psform = PlanSelectionForm(request.POST)  
            if psform.is_valid():
                psdata = psform.cleaned_data
                from_date = psdata['plan_from_date'].strftime('%Y_%m_%d')
                to_date = psdata['plan_to_date'].strftime('%Y_%m_%d')
                list_type = psdata['list_type']
                return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
                   % ('producer/planningtable', member.id, list_type, from_date, to_date))
            else:
                sdform = DateRangeSelectionForm(prefix='sd', initial=init)
                income_form = DateRangeSelectionForm(prefix = 'inc', initial=init)

    else:
        psform = PlanSelectionForm(initial=plan_init)
        sdform = DateRangeSelectionForm(prefix='sd', initial=init)
        income_form = DateRangeSelectionForm(prefix = 'inc', initial=init)
    return render_to_response('producer/plan_selection.html', 
            {'plan_form': psform,
             'sdform': sdform,
             'income_form': income_form,
             'member_has_plans': member_has_plans,
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
    forms = create_weekly_plan_forms(plan_table.rows, data=request.POST or None)
    if request.method == "POST":
        #import pdb; pdb.set_trace()
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
                            #import pdb; pdb.set_trace()
                            if not qty == plan.quantity:
                                #import pdb; pdb.set_trace()
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
                                #inventoried=True,
                                #distributor,
                            )
                            new_plan.save()
                            #import pdb; pdb.set_trace()
                            if role == "producer":
                                listed_product, created = ProducerProduct.objects.get_or_create(
                                    product=product, producer=member)
                            elif role == "consumer":
                                #todo: shd these be auto-created at all?
                                # and if so, what MemberProductList?
                                listed_product, created = CustomerProduct.objects.get_or_create(
                                    product=product, customer=member)

                    else:
                        if plan:
                            if plan.from_date >= from_dt and plan.to_date <= to_dt:
                                #pass
                                plan.delete()
                            else:
                                #import pdb; pdb.set_trace()
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
            'tabnav': "producer/producer_tabnav.html",
        }, context_instance=RequestContext(request))


@login_required
def supply_and_demand(request, from_date, to_date):
    try:
        from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
        to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    member = request.user.parties.all()[0].party
    sdtable = supply_demand_table(from_date, to_date, member)
    return render_to_response('distribution/supply_demand.html', 
        {
            'from_date': from_date,
            'to_date': to_date,
            'sdtable': sdtable,
            'tabnav': "producer/producer_tabnav.html",
            'tabs': 'P',
        }, context_instance=RequestContext(request))

@login_required
def income(request, from_date, to_date):
    try:
        from_date = datetime.datetime(*time.strptime(from_date, '%Y_%m_%d')[0:5]).date()
        to_date = datetime.datetime(*time.strptime(to_date, '%Y_%m_%d')[0:5]).date()
    except ValueError:
            raise Http404
    member = request.user.parties.all()[0].party
    income_table = producer_suppliable_demand(from_date, to_date, member)
    total_income =  sum(row[len(row)-1] for row in income_table.rows)
    return render_to_response('producer/producer_income.html', 
        {
            'from_date': from_date,
            'to_date': to_date,
            'total_income': total_income,
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
        plan_type = "Production"
    #import pdb; pdb.set_trace()
    return render_to_response('distribution/member_plans.html', 
        {
            'from_date': from_date,
            'to_date': to_date,
            'sdtable': sdtable,
            'member': member,
            #'member_long_name': member.long_name,
            'plan_type': plan_type,
        }, context_instance=RequestContext(request))


