"""
Test module for bundle_loader.py
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
#  FAST is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import os.path as pth

import pelix
from pelix.framework import FrameworkFactory

from fastoad.module_management import BundleLoader

_LOGGER = logging.getLogger(__name__)
"""Logger for this module"""

logging.basicConfig(level=logging.DEBUG)


def test_init_bundle_loader_from_scratch():
    """
    Tests that creating a Loader instance will start a correctly configured
    Pelix framework
    """

    if FrameworkFactory.is_framework_running():
        FrameworkFactory.get_framework().delete(True)

    assert not FrameworkFactory.is_framework_running()

    loader = BundleLoader()
    _ = loader.framework  # a first call for initiating the framework
    framework = FrameworkFactory.get_framework()
    assert FrameworkFactory.is_framework_running()
    assert framework is loader.framework
    assert framework.get_bundle_by_name("pelix.ipopo.core") is not None

    # Framework outlives the Loader
    del loader
    assert FrameworkFactory.is_framework_running()

    # Another instance gets back the framework
    loader = BundleLoader()
    assert framework is loader.framework

    # Framework has to be deleted for next tests to run smoothly
    framework.delete(True)


def test_init_bundle_loader_with_running_framework():
    """
    Tests that creating a Loader instance with an already running Pelix
    framework will work and enforce a correct configuration of the framework.
    """

    if FrameworkFactory.is_framework_running():
        FrameworkFactory.get_framework().delete(True)

    framework = pelix.framework.create_framework(())
    assert framework.get_bundle_by_name("pelix.ipopo.core") is None
    assert FrameworkFactory.is_framework_running()

    # Creating a loader instance where existing framework misses
    # pelix.ipopo.core bundle.
    # This bundle is expected to be added to the framework at Loader
    # initialization
    loader = BundleLoader()
    assert framework is loader.framework
    assert loader.framework.get_bundle_by_name("pelix.ipopo.core") is not None
    del loader

    # Same as above, but now, existing framework HAS pelix.ipopo.core bundle
    loader = BundleLoader()
    assert framework is loader.framework
    assert loader.framework.get_bundle_by_name("pelix.ipopo.core") is not None
    del loader

    # Framework outlives the Loader
    assert FrameworkFactory.is_framework_running()

    # Framework has to be deleted for next tests to run smoothly
    framework.delete(True)


def test_install_packages():
    """
    Tests installation of bundles in a folder
    """
    loader = BundleLoader()

    loader.install_packages(
        pth.join(pth.dirname(__file__), "dummy_pelix_bundles"))
    assert loader.framework.get_bundle_by_name(
        "dummy_pelix_bundles.hello_world") is not None

    # Pelix framework has to be deleted for next tests to run smoothly
    loader.framework.delete(True)


def test_get_service_references():
    """
    Tests the method for retrieving service references according to properties
    """
    loader = BundleLoader()
    loader.install_packages(
        pth.join(pth.dirname(__file__), "dummy_pelix_bundles"))

    # Missing service
    service_refs = loader.get_service_references("does.not.exists")
    assert service_refs is None

    # Existing service, but not instantiated
    service_refs = loader.get_service_references("hello.world.no.instance")
    assert service_refs is None

    # Existing services, no property provided
    service_refs = loader.get_service_references("hello.world")
    assert len(service_refs) == 2

    # Existing services, 1 property provided
    service_refs = loader.get_service_references("hello.world",
                                                 {"Instantiated": True})
    assert len(service_refs) == 2
    service_refs = loader.get_service_references("hello.world", {"Prop1": 1})
    assert len(service_refs) == 1

    # Existing service, 2 properties, case insensitivity

    service_refs = loader.get_service_references("hello.world"
                                                 , {"Prop1": 1
                                                     , "Prop 2": "says.hello"})
    assert len(service_refs) == 1
    greet_service = loader.context.get_service(service_refs[0])
    assert greet_service.hello("Dolly") == "Hello, Dolly!"

    # Existing service, case insensitivity
    service_refs = loader.get_service_references("hello.world",
                                                 {"Prop 2": "SAYS.HI"})
    assert len(service_refs) == 1
    greet_service = loader.context.get_service(service_refs[0])
    assert greet_service.hello() == "Hi, World!"

    # Existing service, case sensitivity
    service_refs = loader.get_service_references("hello.world",
                                                 {"Prop 2": "SAYS.HELLO"}, True)
    assert service_refs is None
    service_refs = loader.get_service_references("hello.world",
                                                 {"Prop 2": "Says.Hello"}, True)
    assert len(service_refs) == 1
    river = loader.context.get_service(service_refs[0])
    assert river.hello("Sweetie") == "Hello, Sweetie!"

    # Pelix framework has to be deleted for next tests to run smoothly
    loader.framework.delete(True)


def test_get_services():
    """
    Tests the method for retrieving services according to properties
    """
    loader = BundleLoader()
    loader.install_packages(
        pth.join(pth.dirname(__file__), "dummy_pelix_bundles"))

    # Missing service
    services = loader.get_services("does.not.exists")
    assert services is None

    # Existing service, but not instantiated
    services = loader.get_services("hello.world.no.instance")
    assert services is None

    # Existing services, no property provided
    services = loader.get_services("hello.world")
    assert len(services) == 2

    # Existing services, 1 property provided
    services = loader.get_services("hello.world", {"Instantiated": True})
    assert len(services) == 2
    services = loader.get_services("hello.world", {"Prop1": 1})
    assert len(services) == 1

    # Existing service, 2 properties, case insensitivity
    services = loader.get_services("hello.world", {"Prop1": 1, "Prop 2": "says.hello"})
    assert len(services) == 1
    greet_service = services[0]
    assert greet_service.hello("Dolly") == "Hello, Dolly!"

    # Existing service, case insensitivity
    services = loader.get_services("hello.world", {"Prop 2": "SAYS.HI"})
    assert len(services) == 1
    greet_service = services[0]
    assert greet_service.hello() == "Hi, World!"

    # Existing service, case sensitivity
    services = loader.get_services("hello.world", {"Prop 2": "SAYS.HELLO"}, True)
    assert services is None
    services = loader.get_services("hello.world", {"Prop 2": "Says.Hello"}, True)
    assert len(services) == 1
    river = services[0]
    assert river.hello("Sweetie") == "Hello, Sweetie!"

    # Pelix framework has to be deleted for next tests to run smoothly
    loader.framework.delete(True)


def test_instantiate_component():
    """
    Tests the method for instantiating a component from factory name
    """
    loader = BundleLoader()
    loader.install_packages(
        pth.join(pth.dirname(__file__), "dummy_pelix_bundles"))

    # 2 services should already be instantiated
    services = loader.get_services("hello.world")
    assert len(services) == 2

    song = loader.instantiate_component("another-hello-world-factory")
    assert song.hello("Sweetie") == "Hello again, Sweetie!"
    assert song.Prop1 == 3
    assert song.Prop_2 == "Says.Hello"

    # now one more service is instantiated
    services = loader.get_services("hello.world")
    assert len(services) == 3

    # Pelix framework has to be deleted for next tests to run smoothly
    loader.framework.delete(True)


def test_get_factory_names():
    """
    Tests the method for retrieving factories according to properties
    """
    loader = BundleLoader()
    loader.install_packages(
        pth.join(pth.dirname(__file__), "dummy_pelix_bundles"))

    # Missing service
    factory_names = loader.get_factory_names("does.not.exists")
    assert not factory_names

    # Get all factories
    factory_names = loader.get_factory_names()
    assert len(factory_names) == 4

    # Existing services, no property provided
    factory_names = loader.get_factory_names("hello.world")
    assert len(factory_names) == 3

    # No service provided, but properties
    factory_names = loader.get_factory_names(properties={"Instantiated": False})
    assert len(factory_names) == 2

    # Existing services, property provided does not apply
    factory_names = loader.get_factory_names("hello.world", {"Not A Property": 1})
    assert len(factory_names) == 0

    # Existing services, 1 property provided
    factory_names = loader.get_factory_names("hello.world", {"Instantiated": True})
    assert len(factory_names) == 2
    factory_names = loader.get_factory_names("hello.world", {"Prop1": 1})
    assert len(factory_names) == 1

    # Existing service, 2 properties, case insensitivity
    factory_names = loader.get_factory_names("hello.world", {"Prop1": 1, "Prop 2": "says.hello"})
    assert len(factory_names) == 1
    greet_service = loader.instantiate_component(factory_names[0])
    assert greet_service.hello("Dolly") == "Hello, Dolly!"

    # Existing service, case insensitivity
    factory_names = loader.get_factory_names("hello.world", {"Prop 2": "SAYS.HI"})
    assert len(factory_names) == 1
    greet_service = loader.instantiate_component(factory_names[0])
    assert greet_service.hello() == "Hi, World!"

    # Existing service, case sensitivity
    factory_names = loader.get_factory_names("hello.world", {"Prop 2": "SAYS.HELLO"}, True)
    assert not factory_names
    factory_names = loader.get_factory_names("hello.world", {"Prop 2": "Says.Hello"}, True)
    assert len(factory_names) == 2

    # Pelix framework has to be deleted for next tests to run smoothly
    loader.framework.delete(True)
