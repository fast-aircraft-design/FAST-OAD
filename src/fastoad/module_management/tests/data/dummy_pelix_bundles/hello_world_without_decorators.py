"""
Basic "Hello World" services without using iPOPO decorators
"""

# Define the component factory, with a given name
from fastoad.module_management._bundle_loader import BundleLoader


# Register factories without instantiating with our wrapping of iPOPO
class OtherGreetings:
    def hello(self, name="World"):
        return "Hello again, {0}!".format(name)


BundleLoader().register_factory(
    OtherGreetings,
    factory_name="another-hello-world-factory",
    service_names=["hello.world", "hello.world.no.instance"],
    properties={"Prop1": 3, "Prop 2": "Says.Hello", "Instantiated": False},
)


class OtherGreetings2:
    def hello(self, name="Universe"):
        return "Hello again, {0}!".format(name)


# This one provides a different service and tests registering without properties
BundleLoader().register_factory(
    OtherGreetings2, factory_name="hello-universe-factory", service_names=["hello.universe"]
)
