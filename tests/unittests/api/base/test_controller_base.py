"""Unit tests for ``pdip.api.base.controller_base.Controller``.

``Controller`` discovers flask_restx namespaces, decorates resource
methods, and installs routes. The ``basic_app*`` suites exercise the
happy path end-to-end; these tests pin down the branches they do not
reach: an explicit ``namespace`` object, an explicit ``namespace_name``,
and the ``find_namespace`` matching branch that returns an existing
namespace rather than creating a new one.
"""

import sys
from unittest import TestCase
from unittest.mock import MagicMock

from flask import Flask
from flask_restx import Api

from pdip.api.base.controller_base import Controller
from pdip.api.base.resource_base import ResourceBase
from pdip.configuration.models.application import ApplicationConfig


def _application_config():
    return ApplicationConfig(
        root_directory="/tmp",
        name="test-app",
        environment="test",
        hostname=None,
        secret_key=None,
    )


def _make_resource():
    # Generate a fresh subclass each call so ResourceBase.__subclasses__
    # stays hygienic across tests and the controller's decoration does
    # not bleed state between cases.
    class _Widget(ResourceBase):
        def get(self):
            return {"value": 1}

    _Widget.__module__ = __name__
    return _Widget


class ControllerCreateRouteUsesExplicitNamespace(TestCase):
    def test_explicit_namespace_object_sets_namespace_and_name(self):
        # Arrange — hit the `self.namespace is not None` branch so
        # controller_namespace_name is pulled from namespace.name.
        app = Flask(__name__)
        api = Api(app)
        namespace = api.namespace("custom", description="custom")

        controller = Controller(
            cls=_make_resource(),
            api=api,
            application_config=_application_config(),
            namespace=namespace,
        )

        # Act
        controller.create_route()

        # Assert — the custom namespace still owns the new resource
        # (flask_restx records it in ``resources``).
        self.assertTrue(namespace.resources)


class ControllerCreateRouteUsesNamespaceName(TestCase):
    def test_namespace_name_triggers_find_namespace_lookup(self):
        # Arrange — non-empty namespace_name forces the `elif` branch
        # which calls ``find_namespace(name=self.namespace_name)``.
        app = Flask(__name__)
        api = Api(app)

        controller = Controller(
            cls=_make_resource(),
            api=api,
            application_config=_application_config(),
            namespace_name="widgets",
        )

        # Act
        controller.create_route()

        # Assert — a namespace named 'widgets' now exists on the api.
        names = [ns.name for ns in api.namespaces]
        self.assertIn("widgets", names)


class ControllerFindNamespaceReturnsExistingWhenMatch(TestCase):
    def test_find_namespace_returns_existing_match(self):
        # Arrange — preinstall a namespace; find_namespace must return
        # the same object (the loop's ``break`` branch, lines 59-60).
        app = Flask(__name__)
        api = Api(app)
        existing = api.namespace("reuseme", description="existing")

        controller = Controller(
            cls=_make_resource(),
            api=api,
            application_config=_application_config(),
            namespace_name="reuseme",
        )

        # Act
        found, name = controller.find_namespace(name="reuseme")

        # Assert
        self.assertIs(found, existing)
        self.assertEqual(name, "reuseme")


class ControllerFindNamespaceUsesExplicitNameBranch(TestCase):
    def test_find_namespace_with_explicit_name_uses_name_arg(self):
        # Directly exercise the ``if name is not None`` branch (line 53)
        # so the implicit ``get_namespace_name()`` path is not hit.
        app = Flask(__name__)
        api = Api(app)

        controller = Controller(
            cls=_make_resource(),
            api=api,
            application_config=_application_config(),
        )

        found, name = controller.find_namespace(name="provided")

        self.assertEqual(name, "provided")
        self.assertIsNotNone(found)


class ControllerCreateRouteSkipsAlreadyDecorated(TestCase):
    def test_already_decorated_handler_is_not_rewrapped(self):
        # The `decorated` fast-path (line 46) is skipped by name even
        # if the callable matches. Assert the attribute survives.
        app = Flask(__name__)
        api = Api(app)

        class _Predecorated(ResourceBase):
            pass

        def get(self):
            return {"ok": True}

        get.decorated = True
        _Predecorated.get = get
        _Predecorated.__module__ = __name__

        controller = Controller(
            cls=_Predecorated,
            api=api,
            application_config=_application_config(),
            namespace_name="preexist",
        )
        controller.create_route()

        # Assert — the very same function object is still assigned.
        self.assertIs(_Predecorated.get, get)
        self.assertTrue(_Predecorated.get.decorated)


class ControllerGetNamespaceNameDerivesFromModule(TestCase):
    def test_single_segment_module_falls_back_to_class_name(self):
        # When there's only one path segment, the class-name fallback
        # (``name = self.cls.__name__.replace('Controller'...)``) runs.
        app = Flask(__name__)
        api = Api(app)

        class WidgetController(ResourceBase):
            pass

        # Point module to a file that collapses to one segment after
        # the root_directory prefix is stripped.
        module_name = WidgetController.__module__
        fake_module = MagicMock()
        fake_module.__file__ = "/tmp/widget.py"
        sys.modules[module_name] = fake_module
        try:
            controller = Controller(
                cls=WidgetController,
                api=api,
                application_config=_application_config(),
            )
            name = controller.get_namespace_name()
        finally:
            # leave the module cache clean for other tests.
            del sys.modules[module_name]

        self.assertEqual(name, "Widget")

    def test_multisegment_module_uses_folder_name_and_drops_controllers(self):
        # More than one path segment + a ``controllers`` folder exercises
        # the excluded-folder removal (line 76) and the
        # ``split_namespace[-2].title()`` path (line 78).
        api = Api(Flask(__name__))

        class OrdersController(ResourceBase):
            pass

        module_name = OrdersController.__module__
        fake_module = MagicMock()
        fake_module.__file__ = "/tmp/app/orders/controllers/orders_controller.py"
        sys.modules[module_name] = fake_module
        try:
            controller = Controller(
                cls=OrdersController,
                api=api,
                application_config=ApplicationConfig(
                    root_directory="/tmp/app",
                    name="app",
                    environment="test",
                    hostname=None,
                    secret_key=None,
                ),
            )
            name = controller.get_namespace_name()
        finally:
            del sys.modules[module_name]

        # Folder chain after stripping root + 'controllers' is
        # ['orders', 'orders_controller.py']; index -2 .title() -> 'Orders'.
        self.assertEqual(name, "Orders")


class ControllerCreateRouteFallsBackToImplicitNamespace(TestCase):
    def test_no_namespace_arg_triggers_find_namespace_with_none(self):
        # Neither ``namespace`` nor ``namespace_name`` provided — the
        # ``else`` branch (line 36) runs and get_namespace_name derives
        # the name from the class name.
        api = Api(Flask(__name__))

        class GadgetResource(ResourceBase):
            pass

        module_name = GadgetResource.__module__
        fake_module = MagicMock()
        fake_module.__file__ = "/tmp/gadget.py"
        sys.modules[module_name] = fake_module
        try:
            controller = Controller(
                cls=GadgetResource,
                api=api,
                application_config=_application_config(),
            )
            controller.create_route()
        finally:
            del sys.modules[module_name]

        names = [ns.name for ns in api.namespaces]
        self.assertIn("Gadget", names)


class ControllerFindRouteFormsPath(TestCase):
    def test_find_route_strips_namespace_from_class_name(self):
        class WidgetResource(ResourceBase):
            pass

        controller = Controller(
            cls=WidgetResource,
            api=None,
            application_config=_application_config(),
        )

        route = controller.find_route("Widget")

        # WidgetResource -> strip 'Resource' -> 'Widget'; then strip
        # 'Widget' namespace prefix -> '' -> route is empty.
        self.assertEqual(route, "")

    def test_find_route_returns_leading_slash_when_remainder(self):
        class WidgetGetResource(ResourceBase):
            pass

        controller = Controller(
            cls=WidgetGetResource,
            api=None,
            application_config=_application_config(),
        )

        route = controller.find_route("Widget")

        self.assertEqual(route, "/Get")
