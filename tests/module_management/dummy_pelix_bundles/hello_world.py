#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Basic "Hello Worl" services
"""
from pelix.ipopo.decorators import ComponentFactory, Provides, Instantiate, Property


# Define the component factory, with a given name
@ComponentFactory("hello-world-factory")
# Defines the service to provide when the component is active
@Provides("hello.world")
@Property("Prop1", None, 1)
@Property("Prop2", None, "Says.Hello")
@Property("Instantiated", None, True)
# A component must be instantiated as soon as the bundle is active
@Instantiate("provider")
class Greetings1(object):
    def hello(self, name="World"):
        return "Hello, {0}!".format(name)


# Another instance for the same service
@ComponentFactory("hello-world-factory2")
@Provides("hello.world")
@Property("Prop1", None, 2)
@Property("Prop2", None, "Says.Hi")
@Property("Instantiated", None, True)
@Instantiate("provider2")
class Greetings2(object):
    def hello(self, name="World"):
        return "Hi, {0}!".format(name)


@ComponentFactory("another-hello-world-factory")
@Provides("hello.world.no.instance")
@Property("Prop1", None, 3)
@Property("Prop2", None, "Says.Hello")
@Property("Instantiated", None, False)
# Not instantiating this one for testing the case
class OtherGreetings(object):
    def hello(self, name="World"):
        return "Hello again, {0}!".format(name)
