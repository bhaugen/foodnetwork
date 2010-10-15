import datetime
from decimal import *

from django.db import models
from django.utils.translation import ugettext_lazy as _

from distribution.models import Order, Payment

class PayPalSettings(models.Model):
    business = models.CharField(_('business'), max_length=128,
        help_text=_('can be email address for PayPal business account or Secure Merchant ID'))
    email = models.EmailField(_('email'), 
        help_text=_('primary email address for PayPal business account, all lower case'))
    use_sandbox = models.BooleanField(_('use PayPal Sandbox'), default=False,
        help_text=_('Sandbox is PayPal testing service'))
    
    class Meta:
        verbose_name = "PayPal Settings"
        verbose_name_plural = "PayPal Settings"

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super(PayPalSettings, self).save(*args, **kwargs)

from paypal.standard.ipn.signals import payment_was_successful
        
def register_payment(sender, **kwargs):
    ipn_obj = sender
    ipn_obj.custom = "received IPN"
    ipn_obj.save()
    if ipn_obj.txn_type == "web_accept":
        if len(ipn_obj.invoice) > 0:
            try:
                order = Order.objects.get(pk=int(ipn_obj.invoice))
                fn = FoodNetwork.objects.get(pk=1)
                amount = Decimal(ipn_obj.mc_gross)
                payment = Payment(
                    from_whom = order.customer,
                    to_whom = fn,
                    transaction_date = datetime.date.today(),
                    amount = amount,
                    reference = " ".join(["PayPal Payment", str(ipn_obj.txn_id)]),
                )
                payment.save()
                cp = CustomerPayment(
                    paid_order = order,
                    payment = payment,
                    amount_paid = amount)
                cp.save()
                order.register_customer_payment()
            except:
                pass
            

payment_was_successful.connect(register_payment)

