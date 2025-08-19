"""
Basic "Hello World" services using iPOPO decorators
"""

from pelix.ipopo.decorators import ComponentFactory, Instantiate, Property, Provides


@ComponentFactory("hello-world-factory")
@Provides("hello.world")
@Property("_Prop1", "Prop1", 1)
@Property("_Prop_2", "Prop 2", "Says.Hello")
@Property("Instantiated", None, True)
@Instantiate("provider")
class Greetings1:
    def hello(self, name="World"):
        return "Hello, {0}!".format(name)


@ComponentFactory("hello-world-factory2")
@Provides("hello.world")
@Property("_Prop1", "Prop1", 2)
@Property("_Prop_2", "Prop 2", "Says.Hi")
@Property("Instantiated", None, True)
@Instantiate("provider2")
class Greetings2:
    def hello(self, name="World"):
        return "Hi, {0}!".format(name)
