# -*- coding: utf-8 -*-

import pytest
import time
from unittest.mock import patch
from aiohttp import web
import asyncio
from foglamp.common.storage_client.storage_client import ReadingsStorageClient, StorageClient
from foglamp.common.process import FoglampProcess, SilentArgParse, ArgumentParserError
from foglamp.services.common.microservice import FoglampMicroservice, _logger
from foglamp.common.microservice_management_client.microservice_management_client import MicroserviceManagementClient


__author__ = "Ashwin Gopalakrishnan"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

# test abstract methods
# test FoglampProcess class things it needs
# test that it registers with core
# test the microservice management api

@pytest.allure.feature("unit")
@pytest.allure.story("common", "foglamp-microservice")
class TestFoglampMicroservice:

    def test_constructor_abstract_method_missing(self):
        with pytest.raises(TypeError):
            fm = FoglampMicroservice()
        with pytest.raises(TypeError):
            class FoglampMicroserviceImp(FoglampMicroservice):
                pass
            fm = FoglampMicroserviceImp()
        with pytest.raises(TypeError):
            class FoglampMicroserviceImp(FoglampMicroservice):
                async def change(self):
                    pass
                async def shutdown(self):
                    pass
            fm = FoglampMicroserviceImp()
        with pytest.raises(TypeError):
            class FoglampMicroserviceImp(FoglampMicroservice):
                def run(self):
                    pass
                async def shutdown(self):
                    pass
            fm = FoglampMicroserviceImp()
        with pytest.raises(TypeError):
            class FoglampMicroserviceImp(FoglampMicroservice):
                def run(self):
                    pass
                async def change(self):
                    pass
            fm = FoglampMicroserviceImp()

    def test_constructor_good(self, loop):
        class FoglampMicroserviceImp(FoglampMicroservice):
            def run(self):
                pass
            async def change(self):
                pass
            async def shutdown(self):
                pass
        
        with patch.object(asyncio, 'get_event_loop', return_value=loop):
            with patch.object(SilentArgParse, 'silent_arg_parse', side_effect=['corehost', 0, 'sname']):
                with patch.object(MicroserviceManagementClient, '__init__', return_value=None) as mmc_patch:
                    with patch.object(ReadingsStorageClient, '__init__', return_value=None) as rsc_patch:
                        with patch.object(StorageClient, '__init__', return_value=None) as sc_patch:
                            with patch.object(FoglampMicroservice, '_make_microservice_management_app', return_value=None) as make_patch:
                                 with patch.object(FoglampMicroservice, '_run_microservice_management_app', side_effect=None) as run_patch:
                                     with patch.object(FoglampProcess, 'register_service_with_core', return_value={'id':'bla'}) as reg_patch:
                                         with patch.object(FoglampMicroservice, '_get_service_registration_payload', return_value=None) as payload_patch:
                                             fm = FoglampMicroserviceImp()
        # from FoglampProcess
        assert fm._core_management_host is 'corehost'
        assert fm._core_management_port is 0
        assert fm._name is 'sname'
        assert hasattr(fm, '_core_microservice_management_client')
        assert hasattr(fm, '_readings_storage')
        assert hasattr(fm, '_storage')
        assert hasattr(fm, '_start_time')
        # from FoglampMicroservice
        assert hasattr(fm, '_microservice_management_app')
        assert hasattr(fm, '_microservice_management_handler')
        assert hasattr(fm, '_microservice_management_server')
        assert hasattr(fm, '_microservice_management_host')
        assert hasattr(fm, '_microservice_management_port')
        assert hasattr(fm, '_microservice_id')
        assert hasattr(fm, '_type')
        assert hasattr(fm, '_protocol')

    def test_constructor_exception(self, loop):
        class FoglampMicroserviceImp(FoglampMicroservice):
            def run(self):
                pass
            async def change(self):
                pass
            async def shutdown(self):
                pass
        with patch.object(asyncio, 'get_event_loop', return_value=loop):
            with patch.object(SilentArgParse, 'silent_arg_parse', side_effect=['corehost', 0, 'sname']):
                with patch.object(MicroserviceManagementClient, '__init__', return_value=None) as mmc_patch:
                    with patch.object(ReadingsStorageClient, '__init__', return_value=None) as rsc_patch:
                        with patch.object(StorageClient, '__init__', return_value=None) as sc_patch:
                            with patch.object(FoglampMicroservice, '_make_microservice_management_app', side_effect=Exception()) as make_patch:
                                with patch.object(_logger, 'exception') as logger_patch:
                                    with pytest.raises(Exception) as excinfo:
                                        fm = FoglampMicroserviceImp()
        logger_patch.assert_called_once_with('Unable to intialize FoglampMicroservice due to exception %s', '')

    @pytest.mark.asyncio
    async def test_ping(self, loop):
        class FoglampMicroserviceImp(FoglampMicroservice):
            def run(self):
                pass
            async def change(self):
                pass
            async def shutdown(self):
                pass
        with patch.object(asyncio, 'get_event_loop', return_value=loop):
            with patch.object(SilentArgParse, 'silent_arg_parse', side_effect=['corehost', 0, 'sname']):
                with patch.object(MicroserviceManagementClient, '__init__', return_value=None) as mmc_patch:
                    with patch.object(ReadingsStorageClient, '__init__', return_value=None) as rsc_patch:
                        with patch.object(StorageClient, '__init__', return_value=None) as sc_patch:
                            with patch.object(FoglampMicroservice, '_make_microservice_management_app', return_value=None) as make_patch:
                                 with patch.object(FoglampMicroservice, '_run_microservice_management_app', side_effect=None) as run_patch:
                                     with patch.object(FoglampProcess, 'register_service_with_core', return_value={'id':'bla'}) as reg_patch:
                                         with patch.object(FoglampMicroservice, '_get_service_registration_payload', return_value=None) as payload_patch:
                                             with patch.object(web, 'json_response', return_value=None) as response_patch:
                                                 # called once on FoglampProcess init for _start_time, once for ping
                                                 with patch.object(time, 'time', return_value=1) as time_patch:
                                                     fm = FoglampMicroserviceImp()
                                                     await fm.ping(None)
        response_patch.assert_called_once_with({'uptime': 0})

    @pytest.mark.asyncio
    async def test_core_only_ms_api(self, loop):
        class FoglampMicroserviceImp(FoglampMicroservice):
            def run(self):
                pass
            async def change(self):
                pass
            async def shutdown(self):
                pass
        with patch.object(asyncio, 'get_event_loop', return_value=loop):
            with patch.object(SilentArgParse, 'silent_arg_parse', side_effect=['corehost', 0, 'sname']):
                with patch.object(MicroserviceManagementClient, '__init__', return_value=None) as mmc_patch:
                    with patch.object(ReadingsStorageClient, '__init__', return_value=None) as rsc_patch:
                        with patch.object(StorageClient, '__init__', return_value=None) as sc_patch:
                            with patch.object(FoglampMicroservice, '_make_microservice_management_app', return_value=None) as make_patch:
                                 with patch.object(FoglampMicroservice, '_run_microservice_management_app', side_effect=None) as run_patch:
                                     with patch.object(FoglampProcess, 'register_service_with_core', return_value={'id':'bla'}) as reg_patch:
                                         with patch.object(FoglampMicroservice, '_get_service_registration_payload', return_value=None) as payload_patch:
                                             with pytest.raises(web.HTTPBadRequest) as excinfo:
                                                 fm = FoglampMicroserviceImp()
                                                 await fm.register(None)
                                                 assert 'Service registration requests are handled by core microservice, not by sname microservice' in str(excinfo.value)
                                                 await fm.unregister(None)
                                                 assert 'Service registration requests are handled by core microservice, not by sname microservice' in str(excinfo.value)
                                                 await fm.get_service(None)
                                                 assert 'Service registration requests are handled by core microservice, not by sname microservice' in str(excinfo.value)
                                                 await fm.register_interest(None)
                                                 assert 'Service registration requests are handled by core microservice, not by sname microservice' in str(excinfo.value)
                                                 await fm.unregister_interest(None)
                                                 assert 'Service registration requests are handled by core microservice, not by sname microservice' in str(excinfo.value)
                                                 await fm.get_interest(None)
                                                 assert 'Service registration requests are handled by core microservice, not by sname microservice' in str(excinfo.value)
