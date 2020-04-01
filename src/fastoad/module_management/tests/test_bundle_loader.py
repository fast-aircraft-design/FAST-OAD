"""
Test module for bundle_loader.py
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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
import pytest
from pelix.framework import FrameworkFactory

from .. import BundleLoader
from ..exceptions import FastDuplicateFactoryError

_LOGGER = logging.getLogger(__name__)
"""Logger for this module"""

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture()
def delete_framework():
    """ Ensures framework is deleted before and after running tests"""
    if FrameworkFactory.is_framework_running():
        FrameworkFactory.get_framework().delete(True)

    yield

    if FrameworkFactory.is_framework_running():
        FrameworkFactory.get_framework().delete(True)


def test_init_bundle_loader_from_scratch(delete_framework):
    """
    Tests that creating a Loader instance will start a correctly configured
    Pelix framework
    """
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


def test_init_bundle_loader_with_running_framework(delete_framework):
    """
    Tests that creating a Loader instance with an already running Pelix
    framework will work and enforce a correct configuration of the framework.
    """

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


def test_install_packages(delete_framework):
    """
    Tests installation of bundles in a folder
    """
    loader = BundleLoader()

    loader.install_packages(pth.join(pth.dirname(__file__), "dummy_pelix_bundles"))
    assert (
        loader.framework.get_bundle_by_name("dummy_pelix_bundles.hello_world_with_decorators")
        is not None
    )


def test_install_packages_on_faulty_install(delete_framework):
    """
    Related to Issue #81
    """
    # TODO: this test was done for testing the workaround about iPOPO crashing
    #       when a module has None as __path__ attribute. As iPOPO is fixed, the
    #       workaround has been removed, and this test now just tests iPOPO, so
    #       it may be removed later.
    loader = BundleLoader()

    # Create the buggy numpy install
    import sys

    sys.modules["numpy.random.mtrand"].__path__ = None

    # Install packages
    loader.install_packages(pth.join(pth.dirname(__file__), "dummy_pelix_bundles"))
    assert (
        loader.framework.get_bundle_by_name("dummy_pelix_bundles.hello_world_with_decorators")
        is not None
    )


def test_register_factory(delete_framework):
    """
    Tests that register_factory raises correctly an error when finding
    duplicate names
    (Real tests are done when trying to get components registered in
    hello_world_without_decorators.py)
    """

    loader = BundleLoader()
    loader.install_packages(pth.join(pth.dirname(__file__), "dummy_pelix_bundles"))

    class Greetings1:
        def hello(self, name="World"):
            return "Hello, {0}!".format(name)

    with pytest.raises(FastDuplicateFactoryError) as exc_info:
        loader.register_factory(Greetings1, "hello-universe-factory", "hello.world")
    assert exc_info.value.factory_name == "hello-universe-factory"


def test_get_services(delete_framework):
    """
    Tests the method for retrieving services according to properties
    """
    loader = BundleLoader()
    loader.install_packages(pth.join(pth.dirname(__file__), "dummy_pelix_bundles"))

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


def test_instantiate_component(delete_framework):
    """
    Tests the method for instantiating a component from factory name
    """
    loader = BundleLoader()
    loader.install_packages(pth.join(pth.dirname(__file__), "dummy_pelix_bundles"))

    # 2 services should already be instantiated
    services = loader.get_services("hello.world")
    assert len(services) == 2

    song = loader.instantiate_component("another-hello-world-factory")
    assert song.hello("Sweetie") == "Hello again, Sweetie!"
    assert song._Prop1 == 3
    assert song._Prop_2 == "Says.Hello"

    # now one more service is instantiated
    services = loader.get_services("hello.world")
    assert len(services) == 3


def test_get_factory_names(delete_framework):
    """
    Tests the method for retrieving factories according to properties
    """
    loader = BundleLoader()
    loader.install_packages(pth.join(pth.dirname(__file__), "dummy_pelix_bundles"))

    # Missing service
    factory_names = loader.get_factory_names("does.not.exists")
    assert not factory_names

    # Get all factories
    factory_names = loader.get_factory_names()
    assert len(factory_names) >= 4  # the four test factories + factories in FAST

    # Existing services, no property provided
    factory_names = loader.get_factory_names("hello.world")
    assert len(factory_names) == 3
    factory_names = loader.get_factory_names("hello.universe")
    assert len(factory_names) == 1

    # No service provided, but properties
    factory_names = loader.get_factory_names(properties={"Instantiated": False})
    assert len(factory_names) == 1

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
