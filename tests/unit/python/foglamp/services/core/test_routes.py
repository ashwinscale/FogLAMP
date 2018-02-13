# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END


import pytest
from aiohttp import web
from aiohttp.web_urldispatcher import PlainResource, DynamicResource
from foglamp.services.core import routes


__author__ = "Ashish Jabble"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


@pytest.allure.feature("unit")
@pytest.allure.story("core", "routes")
class TestRoutes:
    """ Core Routes"""

    # TODO: only common and configuration route info tests added
    @pytest.fixture
    async def app(self):
        app = web.Application()
        return app

    def test_routes_count(self, app):
        routes.setup(app)
        actual_route_count = 41
        # total no. of routes
        assert actual_route_count == len(app.router.resources())
        # with enable cors
        assert actual_route_count * 2 == len(app.router.routes())

    def test_routes_info(self, app):
        routes.setup(app)

        for index, route in enumerate(app.router.routes()):
            res_info = route.resource.get_info()
            if index == 0:
                assert "GET" == route.method
                assert type(route.resource) is PlainResource
                assert "/foglamp/ping" == res_info["path"]
                assert str(route.handler).startswith("<function ping")
            elif index == 2:
                assert "PUT" == route.method
                assert type(route.resource) is PlainResource
                assert "/foglamp/shutdown" == res_info["path"]
                assert str(route.handler).startswith("<function shutdown")
            elif index == 4:
                assert "GET" == route.method
                assert type(route.resource) is PlainResource
                assert "/foglamp/category" == res_info["path"]
                assert str(route.handler).startswith("<function get_categories")
            elif index == 6:
                assert "POST" == route.method
                assert type(route.resource) is PlainResource
                assert "/foglamp/category" == res_info["path"]
                assert str(route.handler).startswith("<function create_category")
            elif index == 8:
                assert "GET" == route.method
                assert type(route.resource) is DynamicResource
                assert "/foglamp/category/{category_name}" == res_info["formatter"]
                assert str(route.handler).startswith("<function get_category")
            elif index == 10:
                assert "GET" == route.method
                assert type(route.resource) is DynamicResource
                assert "/foglamp/category/{category_name}/{config_item}" == res_info["formatter"]
                assert str(route.handler).startswith("<function get_category_item")
            elif index == 12:
                assert "PUT" == route.method
                assert type(route.resource) is DynamicResource
                assert "/foglamp/category/{category_name}/{config_item}" == res_info["formatter"]
                assert str(route.handler).startswith("<function set_configuration_item")
            elif index == 14:
                assert "DELETE" == route.method
                assert type(route.resource) is DynamicResource
                assert "/foglamp/category/{category_name}/{config_item}/value" == res_info["formatter"]
                assert str(route.handler).startswith("<function delete_configuration_item_value")
