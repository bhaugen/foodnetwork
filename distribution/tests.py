"""

>>> from distribution.models import *
>>> from datetime import date
>>> from decimal import *

>>> test_date = date(2009,8,10)

>>> steer = Product(
...     short_name="Steer",
...     long_name="Steer, live",
...     price=Decimal("1000"))
>>> steer.save()

>>> beef = Product(
...     short_name="Beef",
...     long_name="Beef per lb",
...     price=Decimal("10"))
>>> beef.save()

>>> ptype = ProcessType(
...     name="Butcher",
...     input_type=steer,
...     output_type=beef)
>>> ptype.save()

>>> producer = Producer(
...     short_name="Farmer",
...     long_name="Farmer John")
>>> producer.save()

>>> processor = Processor(
...     short_name="Fatty",
...     long_name="Fatty Meats")
>>> producer.save()

>>> process = Process(
...     process_type=ptype,
...     process_date=test_date)
>>> process.save()

>>> input_lot = InventoryItem(
...     producer=producer,
...     product=steer,
...     planned=Decimal("1"),
...     remaining=Decimal("1"),
...     inventory_date=test_date)
>>> input_lot.save()
>>> input_lot.remaining
Decimal("1")

>>> output_lot = InventoryItem(
...     producer=producer,
...     product=beef,
...     planned=Decimal("0"),
...     remaining=Decimal("0"),
...     inventory_date=test_date)
>>> output_lot.save()
>>> output_lot.remaining
Decimal("0")

>>> goods_input = InventoryTransaction(
...     inventory_item=input_lot,
...     process=process,
...     from_whom=producer,
...     to_whom=producer,
...     transaction_type="Issue",
...     amount=Decimal("1"),
...     transaction_date=test_date)
>>> goods_input.save()

>>> goods_output = InventoryTransaction(
...     inventory_item=output_lot,
...     process=process,
...     from_whom=producer,
...     to_whom=producer,
...     transaction_type="Production",
...     amount=Decimal("400"),
...     transaction_date=test_date)
>>> goods_output.save()

>>> process
<Process: Butcher  Farmer Steer, live 2009-08-10>

>>> input_lot.remaining
Decimal("0")

>>> output_lot.remaining
Decimal("400")

>>> goods_output.amount = Decimal("200")
>>> goods_output.save()
>>> output_lot.remaining
Decimal("200")

"""
