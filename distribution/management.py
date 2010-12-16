from django.db.models import signals

from django.utils.translation import ugettext_noop as _

try:
    from notification import models as notification
    
    def create_notice_types(app, created_models, verbosity, **kwargs):        
        notification.create_notice_type("distribution_fresh_list", _("Fresh List notice"), _("Here are the fresh foods available this week"), default=2)
        notification.create_notice_type("distribution_pickup_list", _("Pickup List notice"), _("Here are the items to be picked up today"), default=2) 
        notification.create_notice_type("distribution_order_list", _("Order List notice"), _("Here are the orders to be delivered today"), default=2)  
        notification.create_notice_type("distribution_order_notice", _("Order Notice"), 
            _("Here are the items ordered by this customer today"), default=2)
        notification.create_notice_type("distribution_short_change_notice",
            _("Short Change Notice"), _("Here are the short changes for this order"), default=2)
        notification.create_notice_type("distribution_invoice",
            _("Invoice Email"), _("Sending emails of selected invoices"), default=2)
        notification.create_notice_type("distribution_order",
            _("Order Email"), _("Sending emails of selected orders"), default=2)
        
    signals.post_syncdb.connect(create_notice_types, sender=notification)
except ImportError:
    print "Skipping creation of NoticeTypes as notification app not found"
