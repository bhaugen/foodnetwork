from django.template import Library, Node

from distribution.models import FoodNetwork

class FoodNet(Node):
    def render(self, context):
        try:
            answer = FoodNetwork.objects.get(pk=1)
        except FoodNetwork.DoesNotExist:
            answer = None
        context['food_network'] = answer
        return ''
        
def do_get_food_network(parser, token):

    return FoodNet()

register = Library()     
register.tag('food_network', do_get_food_network)




