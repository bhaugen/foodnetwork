import datetime
from django.db.models import Model
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.utils import simplejson

def _json_safe_model_dict(model_instance, fields=(), exclude_fields=(),
    add_model_info=False):
    """
    Returns a dict of JSON safe formatted model fields. Related model objects
    are represented by their primary keys.
    
    Arguments:
        fields = A tuple of field names to use. An empty tuple includes all.
        exclude_fields = A tuple of field names that are excluded.
        add_model_info = A boolean indicating if _app_label and _model_name
            should be added to dictionary
    
    Two additional key-value-pairs are set to have a generic identifier and
    label for each item:
        _pk: The primary key of a model
        _unicode: The string representation of a model
    """
    data = {
        '_pk': model_instance.pk,
        '_unicode': unicode(model_instance),
    }
    if add_model_info:
        data.update({
            '_app_label': model_instance._meta.app_label,
            '_model_name': model_instance._meta.module_name,
        })
    # Standard fields
    for field in model_instance._meta.fields:
        if fields and field.name not in fields:
            continue
        if exclude_fields and field.name in exclude_fields:
            continue
        attr = getattr(model_instance, field.name)
        if isinstance(attr, datetime.datetime):
            attr = str(attr).replace(' ', 'T')
        elif isinstance(attr, datetime.date):
            attr = str(attr)
        elif isinstance(attr, Model):
            attr = attr.id
        elif attr is None:
            attr = None
        elif isinstance(attr, (str, unicode, int, long, float, bool,)):
            attr = attr
        else:
            attr = str(attr)
        data.update({ field.name: attr })
    # Many to many fields
    for field in model_instance._meta.many_to_many:
        if fields and field.name not in fields:
            continue
        if exclude_fields and field.name in exclude_fields:
            continue
        attr = getattr(model_instance, field.name)
        data.update({ field.name: list(attr.values_list('pk', flat=True)) })
    return data

def serialize(model_instances, fields=(), exclude_fields=(),
    add_model_info=False):
    """
    Serializes a model instance, a collection of model instances or a queryset
    to a dojo data compatible JSON string. To prevent JSON hijacking, the
    string gets prefixed, see http://tinyurl.com/sitepensiajax for details.
    
    Two additional key-value-pairs are set to have a generic identifier and
    label for each item:
        _pk: The primary key of a model
        _unicode: The string representation of a model
    
    Arguments:
        model_instances = One or more model instances or a queryset
        fields = A tuple of field names to use. An empty tuple includes all.
        exclude_fields = A tuple of field names that are excluded.
        add_model_info = A boolean indicating if _app_label and _model_name
            should be added to dictionary
    """
    if isinstance(model_instances, QuerySet):
        model_instances = list(model_instances)
    if not isinstance(model_instances, list):
        model_instances = [ model_instances ]
    items = [_json_safe_model_dict(i, fields, exclude_fields) for i in \
        model_instances if isinstance(i, Model)]
    dojo_data_dict = {
        'identifier': '_pk',
        'label': '_unicode',
        'numRows': len(items),
        'items': items,
    }
    dojo_data_json = simplejson.dumps(dojo_data_dict, ensure_ascii=False)
    #return ''.join(['{}&&\n', dojo_data_json])
    return simplejson.dumps(items, ensure_ascii=False)
    
def DojoDataJSONResponse(model_instances, fields=(), exclude_fields=(),
    add_model_info=False, status=200):
    """
    Serializes a model instance, a collection of model instances or a queryset
    to a dojo data compatible HTTP Response. To prevent JSON hijacking, it
    gets prefixed, see http://tinyurl.com/sitepensiajax for details.
    The HTTP Headers are set to ensure the response does not get cached.
    
    Two additional key-value-pairs are set to have a generic identifier and
    label for each item:
        _pk: The primary key of a model
        _unicode: The string representation of a model
    
    Arguments:
        model_instances = One or more model instances or a queryset
        fields = A tuple of field names to use. An empty tuple includes all.
        exclude_fields = A tuple of field names that are excluded.
        add_model_info = A boolean indicating if _app_label and _model_name
            should be added to dictionary
    """
    dojo_data_json = serialize(model_instances, fields, exclude_fields,
        add_model_info)
    response = HttpResponse(content=dojo_data_json, 
        mimetype='application/json', status=status)
    response['Cache-Control'] = 'no-cache, no-store, max-age=0, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = 'Mon, 01 Jan 1990 00:00:00 GMT'
    response['Last-Modified'] = datetime.datetime.strftime(
        datetime.datetime.utcnow(), "%a, %d %b %Y %H:%M:%S GMT")
    return response
