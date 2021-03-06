# -*- coding: utf-8 -*-
""" Unit tests for the omf plugin """

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

__author__ = "Stefano Simonelli"
__copyright__ = "Copyright (c) 2018 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

import pytest
import json
import time
import sys
import requests

from unittest.mock import patch, MagicMock

from foglamp.tasks.north.sending_process import SendingProcess
from foglamp.plugins.north.omf import omf
import foglamp.tasks.north.sending_process as module_sp

from foglamp.common.storage_client.storage_client import StorageClient


# noinspection PyPep8Naming
class to_dev_null(object):
    """ Used to ignore messages sent to the stderr """

    def write(self, _data):
        """" """
        pass


# noinspection PyUnresolvedReferences
@pytest.allure.feature("unit")
@pytest.allure.story("plugin", "north", "omf")
class TestOMF:
    """Unit tests related to the public methods of the omf plugin """

    def test_plugin_info(self):

        assert omf.plugin_info() == {
            'name': "OMF North",
            'version': "1.0.0",
            'type': "north",
            'interface': "1.0",
            'config': omf._CONFIG_DEFAULT_OMF
        }

    def test_plugin_init_good(self):
        """Tests plugin_init using a good set of values"""

        omf._logger = MagicMock()

        # Used to check the conversions
        data = {
                "stream_id": {"value": 1},

                "_CONFIG_CATEGORY_NAME":  module_sp.SendingProcess._CONFIG_CATEGORY_NAME,
                "URL": {"value": "test_URL"},
                "producerToken": {"value": "test_producerToken"},
                "OMFMaxRetry": {"value": "100"},
                "OMFRetrySleepTime": {"value": "100"},
                "OMFHttpTimeout": {"value": "100"},
                "StaticData": {
                    "value": json.dumps(
                        {
                            "Location": "Palo Alto",
                            "Company": "Dianomic"
                        }
                    )
                },

                'sending_process_instance': MagicMock(spec=SendingProcess)
            }

        config_default_omf_types = omf.CONFIG_DEFAULT_OMF_TYPES
        config_default_omf_types["type-id"]["value"] = "0001"

        with patch.object(data['sending_process_instance'], '_fetch_configuration',
                          return_value=config_default_omf_types):
            config = omf.plugin_init(data)

        assert config['_CONFIG_CATEGORY_NAME'] == module_sp.SendingProcess._CONFIG_CATEGORY_NAME
        assert config['URL'] == "test_URL"
        assert config['producerToken'] == "test_producerToken"
        assert config['OMFMaxRetry'] == 100
        assert config['OMFRetrySleepTime'] == 100
        assert config['OMFHttpTimeout'] == 100

        # Check conversion from String to Dict
        assert isinstance(config['StaticData'], dict)

    @pytest.mark.parametrize("data", [

            # Bad case 1 - StaticData is a python dict instead of a string containing a dict
            {
                "stream_id": {"value": 1},

                "_CONFIG_CATEGORY_NAME":  module_sp.SendingProcess._CONFIG_CATEGORY_NAME,
                "URL": {"value": "test_URL"},
                "producerToken": {"value": "test_producerToken"},
                "OMFMaxRetry": {"value": "100"},
                "OMFRetrySleepTime": {"value": "100"},
                "OMFHttpTimeout": {"value": "100"},
                "StaticData": {
                    "value":
                        {
                            "Location": "Palo Alto",
                            "Company": "Dianomic"
                        }
                },

                'sending_process_instance': MagicMock()
            },

            # Bad case 2 - OMFMaxRetry, bad value expected an int it is a string
            {
                "stream_id": {"value": 1},

                "_CONFIG_CATEGORY_NAME": module_sp.SendingProcess._CONFIG_CATEGORY_NAME,
                "URL": {"value": "test_URL"},
                "producerToken": {"value": "test_producerToken"},
                "OMFMaxRetry": {"value": "xxx"},
                "OMFRetrySleepTime": {"value": "100"},
                "OMFHttpTimeout": {"value": "100"},
                "StaticData": {
                    "value": json.dumps(
                        {
                            "Location": "Palo Alto",
                            "Company": "Dianomic"
                        }
                    )
                },

                'sending_process_instance': MagicMock()
            }

    ])
    def test_plugin_init_bad(self, data):
        """Tests plugin_init using an invalid set of values"""

        omf._logger = MagicMock()

        with pytest.raises(Exception):
            omf.plugin_init(data)

    def test_plugin_send_ok(self):
        """Tests plugin _plugin_send function, case everything went fine """

        def dummy_ok():
            """" """
            return True, 1, 1

        def data_send_ok():
            """" """
            return True

        def omf_types_create():
            """" """
            return True

        omf._logger = MagicMock()
        omf._config_omf_types = {"type-id": {"value": "0001"}}
        data = MagicMock()

        raw_data = []
        stream_id = 1

        # Test good case
        with patch.object(omf.OmfNorthPlugin, 'transform_in_memory_data', return_value=dummy_ok()):
            with patch.object(omf.OmfNorthPlugin, 'create_omf_objects', return_value=dummy_ok()):
                with patch.object(omf.OmfNorthPlugin, 'send_in_memory_data_to_picromf', return_value=data_send_ok()):
                    with patch.object(omf.OmfNorthPlugin, 'deleted_omf_types_already_created',
                                      return_value=omf_types_create()) as mocked_deleted_omf_types_already_created:
                        omf.plugin_send(data, raw_data, stream_id)

        assert not mocked_deleted_omf_types_already_created.called

    def test_plugin_send_bad(self):
        """Tests plugin _plugin_send function,
           it tests especially if the omf objects are created again in case of a communication error
           NOTE : the test will print a message to the stderr containing 'mocked object generated an exception'
                  the message could/should be ignored.
        """

        def dummy_ok():
            """" """
            return True, 1, 1

        def omf_types_create():
            """" """
            return True

        omf._logger = MagicMock()
        omf._config_omf_types = {"type-id": {"value": "0001"}}
        data = MagicMock()

        raw_data = []
        stream_id = 1

        # Test bad case - send operation raise an exception
        with patch.object(omf.OmfNorthPlugin, 'transform_in_memory_data', return_value=dummy_ok()):
            with patch.object(omf.OmfNorthPlugin, 'create_omf_objects', return_value=dummy_ok()):
                with patch.object(omf.OmfNorthPlugin, 'send_in_memory_data_to_picromf',
                                  side_effect=KeyError('mocked object generated an exception')):
                    with patch.object(omf.OmfNorthPlugin, 'deleted_omf_types_already_created',
                                      return_value=omf_types_create()) as mocked_deleted_omf_types_already_created:

                        with pytest.raises(Exception):
                            # To ignore messages sent to the stderr
                            sys.stderr = to_dev_null()

                            omf.plugin_send(data, raw_data, stream_id)

                        assert mocked_deleted_omf_types_already_created.called

    def test_plugin_shutdown(self):

        omf._logger = MagicMock()
        data = []
        omf.plugin_shutdown([data])

    def test_plugin_reconfigure(self):

        omf._logger = MagicMock()
        omf.plugin_reconfigure()


class TestOmfNorthPlugin:
    """Unit tests related to OmfNorthPlugin, methods used internally to the plugin"""

    @pytest.mark.parametrize(
        "p_data_origin, "
        "type_id, "
        "expected_data_to_send, "
        "expected_is_data_available, "
        "expected_new_position, "
        "expected_num_sent", [
                                # Case 1
                                (
                                    # Origin
                                    [
                                        {
                                            "id": 10,
                                            "asset_code": "test_asset_code",
                                            "read_key": "ef6e1368-4182-11e8-842f-0ed5f89f718b",
                                            "reading": {"humidity": 11, "temperature": 38},
                                            "user_ts": '2018-04-20 09:38:50.163164+00'
                                        }
                                    ],
                                    "0001",
                                    # Transformed
                                    [
                                        {
                                            "containerid": "0001measurement_test_asset_code",
                                            "values": [
                                                {
                                                    "Time": "2018-04-20T09:38:50.163164Z",
                                                    "humidity": 11,
                                                    "temperature": 38
                                                }
                                            ]
                                        }
                                    ],
                                    True, 10, 1
                                ),
                                # Case 2
                                (
                                        # Origin
                                        [
                                            {
                                                "id": 11,
                                                "asset_code": "test_asset_code",
                                                "read_key": "ef6e1368-4182-11e8-842f-0ed5f89f718b",
                                                "reading": {"tick": "tock"},
                                                "user_ts": '2018-04-20 09:38:50.163164+00'
                                            }
                                        ],
                                        "0001",
                                        # Transformed
                                        [
                                            {
                                                "containerid": "0001measurement_test_asset_code",
                                                "values": [
                                                    {
                                                        "Time": "2018-04-20T09:38:50.163164Z",
                                                        "tick": "tock"
                                                    }
                                                ]
                                            }
                                        ],
                                        True, 11, 1
                                ),

                                # Case 3 - 2 rows
                                (
                                        # Origin
                                        [
                                            {
                                                "id": 12,
                                                "asset_code": "test_asset_code",
                                                "read_key": "ef6e1368-4182-11e8-842f-0ed5f89f718b",
                                                "reading": {"pressure": 957.2},
                                                "user_ts": '2018-04-20 09:38:50.163164+00'
                                            },
                                            {
                                                "id": 20,
                                                "asset_code": "test_asset_code",
                                                "read_key": "ef6e1368-4182-11e8-842f-0ed5f89f718b",
                                                "reading": {"y": 34, "z": 114, "x": -174},
                                                "user_ts": '2018-04-20 09:38:50.163164+00'
                                            }
                                        ],
                                        "0001",
                                        # Transformed
                                        [
                                            {
                                                "containerid": "0001measurement_test_asset_code",
                                                "values": [
                                                    {
                                                        "Time": "2018-04-20T09:38:50.163164Z",
                                                        "pressure": 957.2
                                                    }
                                                ]
                                            },
                                            {
                                                "containerid": "0001measurement_test_asset_code",
                                                "values": [
                                                    {
                                                        "Time": "2018-04-20T09:38:50.163164Z",
                                                        "y": 34,
                                                        "z": 114,
                                                        "x": -174,
                                                    }
                                                ]
                                            },
                                        ],
                                        True, 20, 2
                                )

        ])
    def test_plugin_transform_in_memory_data(self,
                                             p_data_origin,
                                             type_id,
                                             expected_data_to_send,
                                             expected_is_data_available,
                                             expected_new_position,
                                             expected_num_sent):
        """Tests the plugin in memory transformations """

        sending_process_instance = []
        config = []
        config_omf_types = []
        logger = MagicMock()
        generated_data_to_send = []

        omf_north = omf.OmfNorthPlugin(sending_process_instance, config, config_omf_types, logger)

        omf_north._config_omf_types = {"type-id": {"value": type_id}}

        is_data_available, new_position, num_sent = omf_north.transform_in_memory_data(generated_data_to_send,
                                                                                       p_data_origin)

        assert generated_data_to_send == expected_data_to_send

        assert is_data_available == expected_is_data_available
        assert new_position == expected_new_position
        assert num_sent == expected_num_sent

    @pytest.mark.parametrize(
        "p_data_origin, "
        "p_stream_id, "
        "expected_data_to_send, ",
        [
                # Case 1 - Two integer values
                (
                    # Origin
                    {
                        "id": 10,
                        "asset_code": "test_asset_code_1",
                        "read_key": "ef6e1368-4182-11e8-842f-0ed5f89f718b",
                        "reading": {"humidity": 11, "temperature": 38},
                        "user_ts": '2018-04-20 09:38:50.163164+00'
                    },

                    # p_stream_id
                    "0001measurement_""test_asset_code_1",

                    # Expected transformation
                    [
                        {
                            "containerid": "0001measurement_""test_asset_code_1",
                            "values": [
                                {
                                    "Time": "2018-04-20T09:38:50.163164Z",
                                    "humidity": 11,
                                    "temperature": 38
                                }
                            ]
                        }
                    ]
                ),
                # Case 2 - String
                (
                    # Origin
                    {
                        "id": 11,
                        "asset_code": "test_asset_code_2",
                        "read_key": "ef6e1368-4182-11e8-842f-0ed5f89f718b",
                        "reading": {"tick": "tock"},
                        "user_ts": '2018-04-20 09:38:50.163164+00'
                    },

                    # p_stream_id
                    "0001measurement_""test_asset_code_2",

                    # Expected transformation
                    [
                        {
                            "containerid": "0001measurement_""test_asset_code_2",
                            "values": [
                                {
                                    "Time": "2018-04-20T09:38:50.163164Z",
                                    "tick": "tock"
                                }
                            ]
                        }
                    ]
                ),

                # Case 3 - Number 957.2
                (
                    # Origin
                    {
                        "id": 12,
                        "asset_code": "test_asset_code_3",
                        "read_key": "ef6e1368-4182-11e8-842f-0ed5f89f718b",
                        "reading": {"pressure": 957.2},
                        "user_ts": '2018-04-20 09:38:50.163164+00'
                    },

                    # p_stream_id
                    "0001measurement_""test_asset_code_3",

                    # Expected transformation
                    [

                        {
                            "containerid": "0001measurement_""test_asset_code_3",
                            "values": [
                                {
                                    "Time": "2018-04-20T09:38:50.163164Z",
                                    "pressure": 957.2
                                }
                            ]
                        }
                    ]
                )

        ]
    )
    def test_transform_in_memory_row(
                                        self,
                                        p_data_origin,
                                        p_stream_id,
                                        expected_data_to_send
    ):
        """Tests the in memory transformations of a single row - _transform_in_memory_row"""

        sending_process_instance = []
        config = []
        config_omf_types = []
        logger = MagicMock()
        generated_data_to_send = []

        omf_north = omf.OmfNorthPlugin(sending_process_instance, config, config_omf_types, logger)

        omf_north._transform_in_memory_row(generated_data_to_send, p_data_origin, p_stream_id)

        assert generated_data_to_send == expected_data_to_send

    @pytest.mark.parametrize(
        "p_creation_type, "
        "p_data_origin, "
        "p_asset_codes_already_created, "
        "p_omf_objects_configuration_based ",
        [
            # Case 1 - automatic
            (
                # p_creation_type
                "automatic",

                # Origin
                [
                    {
                        "id": 10,
                        "asset_code": "test_asset_code",
                        "read_key": "ef6e1368-4182-11e8-842f-0ed5f89f718b",
                        "reading": {"humidity": 10, "temperature": 20},
                        "user_ts": '2018-04-20 09:38:50.163164+00'
                    }
                ],

                # asset_codes_already_created
                [
                    "test_none"
                ],

                # omf_objects_configuration_based
                {"none": "none"}
            ),
            # Case 2 - configuration
            (
                    # p_creation_type
                    "configuration",

                    # Origin
                    [
                        {
                            "id": 10,
                            "asset_code": "test_asset_code",
                            "read_key": "ef6e1368-4182-11e8-842f-0ed5f89f718b",
                            "reading": {"humidity": 10, "temperature": 20},
                            "user_ts": '2018-04-20 09:38:50.163164+00'
                        }
                    ],

                    # asset_codes_already_created
                    [
                        "test_none"
                    ],

                    # omf_objects_configuration_based
                    {"test_asset_code": {"value": "test_asset_code"}}
            )

        ]
    )
    def test_create_omf_objects_test_creation(self,
                                              p_creation_type,
                                              p_data_origin,
                                              p_asset_codes_already_created,
                                              p_omf_objects_configuration_based
                                              ):
        """ Tests the evaluation of the 2 ways of creating OMF objects: automatic or configuration based """

        sending_process_instance = []
        config = []
        config_omf_types = []
        logger = MagicMock()

        config_category_name = "SEND_PR"
        type_id = "0001"

        omf_north = omf.OmfNorthPlugin(sending_process_instance, config, config_omf_types, logger)

        omf_north._config_omf_types = {"type-id": {"value": type_id}}
        omf_north._config_omf_types = p_omf_objects_configuration_based

        with patch.object(omf_north, '_retrieve_omf_types_already_created', return_value=p_asset_codes_already_created):

            with patch.object(omf_north, '_create_omf_objects_configuration_based') \
                    as patched_create_omf_objects_configuration_based:

                with patch.object(omf_north, '_create_omf_objects_automatic') \
                        as patched_create_omf_objects_automatic:

                    with patch.object(omf_north, '_flag_created_omf_type') \
                            as patched_flag_created_omf_type:

                        omf_north.create_omf_objects(p_data_origin, config_category_name, type_id)

        if p_creation_type == "automatic":

            assert not patched_create_omf_objects_configuration_based.called
            assert patched_create_omf_objects_automatic.called
            assert patched_flag_created_omf_type.called

        elif p_creation_type == "configuration":

            assert patched_create_omf_objects_configuration_based.called
            assert not patched_create_omf_objects_automatic.called
            assert patched_flag_created_omf_type.called

        else:
            raise Exception("ERROR : creation type not defined !")

    @pytest.mark.parametrize(
        "p_test_data, "
        "p_type_id, "
        "p_static_data, "
        "expected_typename,"
        "expected_omf_type",
        [
            # Case 1 - pressure / Number
            (
                # Origin - Sensor data
                {"asset_code": "pressure", "asset_data": {"pressure": 921.6}},

                # type_id
                "0001",

                # Static Data
                {
                    "Location": "Palo Alto",
                    "Company": "Dianomic"
                },

                # Expected
                'pressure_typename',
                {
                    'pressure_typename':
                    [
                        {
                            'classification': 'static',
                            'id': '0001_pressure_typename_sensor',
                            'properties': {
                                            'Company': {'type': 'string'},
                                            'Name': {'isindex': True, 'type': 'string'},
                                            'Location': {'type': 'string'}
                            },
                            'type': 'object'
                        },
                        {
                            'classification': 'dynamic',
                            'id': '0001_pressure_typename_measurement',
                            'properties': {
                                'Time': {'isindex': True, 'format': 'date-time', 'type': 'string'},
                                'pressure': {'type': 'number'}
                            },
                            'type': 'object'
                         }
                    ]
                }
            ),
            # Case 2 - luxometer / Integer
            (
                    # Origin - Sensor data
                    {"asset_code": "luxometer", "asset_data": {"lux": 20}},

                    # type_id
                    "0002",

                    # Static Data
                    {
                        "Location": "Palo Alto",
                        "Company": "Dianomic"
                    },

                    # Expected
                    'luxometer_typename',
                    {
                        'luxometer_typename':
                        [
                            {
                                'classification': 'static',
                                'id': '0002_luxometer_typename_sensor',
                                'properties': {
                                    'Company': {'type': 'string'},
                                    'Name': {'isindex': True, 'type': 'string'},
                                    'Location': {'type': 'string'}
                                },
                                'type': 'object'
                            },
                            {
                                'classification': 'dynamic',
                                'id': '0002_luxometer_typename_measurement',
                                'properties': {
                                    'Time': {'isindex': True, 'format': 'date-time', 'type': 'string'},
                                    'lux': {'type': 'integer'}
                                },
                                'type': 'object'
                            }
                        ]
                    }

            ),

            # Case 3 - switch / string
            (
                # Origin - Sensor data
                {"asset_code": "switch", "asset_data": {"button": "up"}},

                # type_id
                "0002",

                # Static Data
                {
                    "Location": "Palo Alto",
                    "Company": "Dianomic"
                },

                # Expected
                'switch_typename',
                {
                    'switch_typename':
                    [
                        {
                            'classification': 'static',
                            'id': '0002_switch_typename_sensor',
                            'properties': {
                                'Company': {'type': 'string'},
                                'Name': {'isindex': True, 'type': 'string'},
                                'Location': {'type': 'string'}
                            },
                            'type': 'object'
                        },
                        {
                            'classification': 'dynamic',
                            'id': '0002_switch_typename_measurement',
                            'properties': {
                                'Time': {'isindex': True, 'format': 'date-time', 'type': 'string'},
                                'button': {'type': 'string'}
                            },
                            'type': 'object'
                        }
                    ]
                }

            )

        ]
    )
    def test_create_omf_type_automatic(self,
                                       p_test_data,
                                       p_type_id,
                                       p_static_data,
                                       expected_typename,
                                       expected_omf_type):
        """ Tests the generation of the OMF messages starting from Asset name and data
            using Automatic OMF Type Mapping"""

        sending_process_instance = []
        config = []
        config_omf_types = []
        logger = MagicMock()

        omf_north = omf.OmfNorthPlugin(sending_process_instance, config, config_omf_types, logger)

        type_id = p_type_id
        omf_north._config_omf_types = {"type-id": {"value": type_id}}
        omf_north._config = {"StaticData": p_static_data}

        with patch.object(omf_north, 'send_in_memory_data_to_picromf', return_value=True) \
                as patched_send_in_memory_data_to_picromf:

            typename, omf_type = omf_north._create_omf_type_automatic(p_test_data)

        assert typename == expected_typename
        assert omf_type == expected_omf_type

        assert patched_send_in_memory_data_to_picromf.called

    @pytest.mark.parametrize(
        "p_test_data ",
        [
            # Case 1 - pressure / Number
            (
                {
                    'dummy': 'dummy'
                }
            ),

        ]
    )
    def test_send_in_memory_data_to_picromf_ok(
                                                self,
                                                p_test_data):
        class Response:
            """ Used to mock the Response object, simulating a successful communication"""

            status_code = 200
            text = "OK"

        sending_process_instance = []
        config = []
        config_omf_types = []
        logger = MagicMock()

        omf_north = omf.OmfNorthPlugin(sending_process_instance, config, config_omf_types, logger)

        omf_north._config = dict(producerToken="dummy_producerToken")
        omf_north._config["URL"] = "dummy_URL"
        omf_north._config["OMFRetrySleepTime"] = 1
        omf_north._config["OMFHttpTimeout"] = 1

        # Good Case
        omf_north._config["OMFMaxRetry"] = 1

        response_ok = Response()
        response_ok.status_code = 200
        response_ok.text = "OK"

        with patch.object(omf_north._logger, 'warning', return_value=True) \
                as patched_logger:

            with patch.object(requests, 'post', return_value=response_ok) \
                    as patched_requests:

                omf_north.send_in_memory_data_to_picromf("Type", p_test_data)

        assert patched_requests.called
        assert patched_requests.call_count == 1
        assert not patched_logger.called

    @pytest.mark.parametrize(
        "p_test_data ",
        [
            # Case 1 - pressure / Number
            (
                {
                    'dummy': 'dummy'
                }

            ),

        ]
    )
    def test_send_in_memory_data_to_picromf_bad(self,
                                                p_test_data):
        """ Tests the behaviour  in case of communication error:
            exception erased,
            message logged
            and number of retries """

        class Response:
            """ Used to mock the Response object, simulating an error"""

            status_code = 400
            text = "ERROR"

        sending_process_instance = []
        config = []
        config_omf_types = []
        logger = MagicMock()

        omf_north = omf.OmfNorthPlugin(sending_process_instance, config, config_omf_types, logger)

        omf_north._config = dict(producerToken="dummy_producerToken")
        omf_north._config["URL"] = "dummy_URL"
        omf_north._config["OMFRetrySleepTime"] = 1
        omf_north._config["OMFHttpTimeout"] = 1

        # Bad Case
        omf_north._config["OMFMaxRetry"] = 3

        response_ok = Response()
        response_ok.status_code = 400
        response_ok.text = "ERROR"

        # To avoid the wait time
        with patch.object(time, 'sleep', return_value=True):

            with patch.object(omf_north._logger, 'warning', return_value=True) as patched_logger:

                with patch.object(requests, 'post', return_value=response_ok) as patched_requests:

                    # Tests the raising of the exception
                    with pytest.raises(Exception):
                        # To ignore messages sent to the stderr
                        sys.stderr = to_dev_null()

                        omf_north.send_in_memory_data_to_picromf("Type", p_test_data)

        assert patched_requests.call_count == 3
        assert patched_logger.called

    @pytest.mark.parametrize(
        "p_type, "
        "p_test_data ",
        [
            # Case 1 - pressure / Number
            (
                "Type",
                {
                    'pressure_typename':
                    [
                        {
                            'classification': 'static',
                            'id': '0001_pressure_typename_sensor',
                            'properties': {
                                            'Company': {'type': 'string'},
                                            'Name': {'isindex': True, 'type': 'string'},
                                            'Location': {'type': 'string'}
                            },
                            'type': 'object'
                        },
                        {
                            'classification': 'dynamic',
                            'id': '0001_pressure_typename_measurement',
                            'properties': {
                                'Time': {'isindex': True, 'format': 'date-time', 'type': 'string'},
                                'pressure': {'type': 'number'}
                            },
                            'type': 'object'
                         }
                    ]
                }

            ),

        ]
    )
    def test_send_in_memory_data_to_picromf_data(
                                                self,
                                                p_type,
                                                p_test_data):
        """ Tests the data sent to the PI Server in relation of an OMF type"""

        class Response:
            """ Used to mock the Response object, simulating a successful communication"""
            status_code = 200
            text = "OR"

        sending_process_instance = []
        config = []
        config_omf_types = []
        logger = MagicMock()

        omf_north = omf.OmfNorthPlugin(sending_process_instance, config, config_omf_types, logger)

        # Values for the test
        test_url = "test_URL"
        test_producer_token = "test_producerToken"
        test_omf_http_timeout = 1
        test_headers = {
                        'producertoken': test_producer_token,
                        'messagetype': p_type,
                        'action': 'create',
                        'messageformat': 'JSON',
                        'omfversion': '1.0'}

        omf_north._config = dict(producerToken=test_producer_token)
        omf_north._config["URL"] = test_url
        omf_north._config["OMFRetrySleepTime"] = 1
        omf_north._config["OMFHttpTimeout"] = test_omf_http_timeout
        omf_north._config["OMFMaxRetry"] = 1

        response_ok = Response()
        response_ok.status_code = 200
        response_ok.text = "OK"

        # To avoid the wait time
        with patch.object(time, 'sleep', return_value=True):

            with patch.object(omf_north._logger, 'warning', return_value=True) as patched_logger:

                with patch.object(requests, 'post', return_value=response_ok) as patched_requests:

                    # To ignore messages sent to the stderr
                    sys.stderr = to_dev_null()

                    omf_north.send_in_memory_data_to_picromf(p_type, p_test_data)

        assert not patched_logger.called

        str_data = json.dumps(p_test_data)
        patched_requests.assert_called_with(
                                            test_url,
                                            headers=test_headers,
                                            data=str_data,
                                            verify=False,
                                            timeout=test_omf_http_timeout)
        assert patched_requests.call_count == 1

    @pytest.mark.parametrize(
        "p_asset,"
        "p_type_id, "
        "p_static_data, "        
        "p_typename,"
        "p_omf_type, "
        "expected_container, "
        "expected_static_data, "
        "expected_link_data ",
        [
            # Case 1 - pressure / Number
            (
                # p_asset
                {"asset_code": "pressure", "asset_data": {"pressure": 921.6}},

                # type_id
                "0001",

                # Static Data
                {
                    "Location": "Palo Alto",
                    "Company": "Dianomic"
                },

                # p_typename
                'pressure_typename',

                # p_omf_type
                {
                    'pressure_typename':
                    [
                        {
                            'classification': 'static',
                            'id': '0001_pressure_typename_sensor',
                            'properties': {
                                            'Company': {'type': 'string'},
                                            'Name': {'isindex': True, 'type': 'string'},
                                            'Location': {'type': 'string'}
                            },
                            'type': 'object'
                        },
                        {
                            'classification': 'dynamic',
                            'id': '0001_pressure_typename_measurement',
                            'properties': {
                                'Time': {'isindex': True, 'format': 'date-time', 'type': 'string'},
                                'pressure': {'type': 'number'}
                            },
                            'type': 'object'
                         }
                    ]
                },

                # expected_container
                [
                    {
                        'typeid': '0001_pressure_typename_measurement',
                        'id': '0001measurement_pressure'
                    }
                ],

                # expected_static_data
                [
                    {
                        'typeid': '0001_pressure_typename_sensor',
                        'values': [
                                    {
                                        'Company': 'Dianomic',
                                        'Location': 'Palo Alto',
                                        'Name': 'pressure'
                                    }
                        ]
                    }
                ],

                # expected_link_data
                [
                    {
                        'typeid': '__Link', 'values': [
                            {
                                    'source': {'typeid': '0001_pressure_typename_sensor', 'index': '_ROOT'},
                                    'target': {'typeid': '0001_pressure_typename_sensor', 'index': 'pressure'}
                            },
                            {
                                    'source': {'typeid': '0001_pressure_typename_sensor', 'index': 'pressure'},
                                    'target': {'containerid': '0001measurement_pressure'}
                            }
                        ]
                     }
                ]
            )

        ]
    )
    def test_create_omf_object_links(
                                        self,
                                        p_asset,
                                        p_type_id,
                                        p_static_data,
                                        p_typename,
                                        p_omf_type,
                                        expected_container,
                                        expected_static_data,
                                        expected_link_data
    ):

        sending_process_instance = []
        config = []
        config_omf_types = []
        logger = MagicMock()

        omf_north = omf.OmfNorthPlugin(sending_process_instance, config, config_omf_types, logger)

        type_id = p_type_id
        omf_north._config_omf_types = {"type-id": {"value": type_id}}
        omf_north._config = {"StaticData": p_static_data}

        with patch.object(omf_north, 'send_in_memory_data_to_picromf', return_value=True) \
                as patched_send_to_picromf:

            omf_north._create_omf_object_links(p_asset["asset_code"], p_typename, p_omf_type)

        assert patched_send_to_picromf.call_count == 3

        patched_send_to_picromf.assert_any_call("Container", expected_container)
        patched_send_to_picromf.assert_any_call("Data", expected_static_data)
        patched_send_to_picromf.assert_any_call("Data", expected_link_data)

    @pytest.mark.parametrize(
        "p_configuration_key, "
        "p_type_id, "
        "p_data_from_storage, "
        "expected_data, ",
        [

            # Case 1
            (
                # p_configuration_key
                "SEND_PR1",
                
                # p_type_id
                "0001",

                # p_data_from_storage
                {
                    "rows":
                    [

                        {
                            "configuration_key": "SEND_PR1",
                            "type_id": "0001",
                            "asset_code": "asset_code_1"
                        },
                        {
                            "configuration_key": "SEND_PR1",
                            "type_id": "0001",
                            "asset_code": "asset_code_2"
                        }

                    ]
                },

                # expected_data
                [
                    "asset_code_1",
                    "asset_code_2"
                ]
            )
        ]
    )
    def test_retrieve_omf_types_already_created(
                                                self,
                                                p_configuration_key,
                                                p_type_id,
                                                p_data_from_storage,
                                                expected_data
    ):
        """Tests _retrieve_omf_types_already_created """

        sending_process_instance = MagicMock()
        config = []
        config_omf_types = []
        logger = MagicMock()
        payload_builder = MagicMock()

        omf_north = omf.OmfNorthPlugin(sending_process_instance, config, config_omf_types, logger)

        omf_north._sending_process_instance._storage = MagicMock(spec=StorageClient)

        with patch.object(payload_builder, 'PayloadBuilder', return_value=True):

            with patch.object(omf_north._sending_process_instance._storage,
                              'query_tbl_with_payload',
                              return_value=p_data_from_storage):

                retrieved_rows = omf_north._retrieve_omf_types_already_created(p_configuration_key, p_type_id)

        assert retrieved_rows == expected_data

    @pytest.mark.parametrize(
        "p_asset_code, "
        "expected_asset_code, ",
        [
            # p_asset_code   # expected_asset_code
            ("asset_code_1 ",  "asset_code_1"),
            (" asset_code_2 ", "asset_code_2"),
            ("asset_ code_3",  "asset_code_3"),
        ]
    )
    def test_generate_omf_asset_id(
            self,
            p_asset_code,
            expected_asset_code
    ):
        """Tests _generate_omf_asset_id """

        sending_process_instance = MagicMock()
        config = []
        config_omf_types = []
        logger = MagicMock()

        omf_north = omf.OmfNorthPlugin(sending_process_instance, config, config_omf_types, logger)

        generated_asset_code = omf_north._generate_omf_asset_id(p_asset_code)

        assert generated_asset_code == expected_asset_code

    @pytest.mark.parametrize(
        "p_type_id, "
        "p_asset_code, "
        "expected_measurement_id, ",
        [
            # p_type_id  - p_asset_code    - expected_asset_code
            ("0001",     "asset_code_1 ",  "0001measurement_asset_code_1"),
            ("0002",     " asset_code_2 ", "0002measurement_asset_code_2"),
            ("0003",     "asset_ code_3",  "0003measurement_asset_code_3"),
        ]
    )
    def test_generate_omf_measurement(
            self,
            p_type_id,
            p_asset_code,
            expected_measurement_id
    ):
        """Tests _generate_omf_measurement """

        sending_process_instance = MagicMock()
        config = []
        config_omf_types = []
        logger = MagicMock()

        omf_north = omf.OmfNorthPlugin(sending_process_instance, config, config_omf_types, logger)

        omf_north._config_omf_types = {"type-id": {"value": p_type_id}}

        generated_measurement_id = omf_north._generate_omf_measurement(p_asset_code)

        assert generated_measurement_id == expected_measurement_id

    @pytest.mark.parametrize(
        "p_asset_code, "
        "expected_typename, ",
        [
            # p_asset_code     - expected_asset_code
            ("asset_code_1 ",  "asset_code_1_typename"),
            (" asset_code_2 ", "asset_code_2_typename"),
            ("asset_ code_3",  "asset_code_3_typename"),
        ]
    )
    def test_generate_omf_typename_automatic(
            self,
            p_asset_code,
            expected_typename
    ):
        """Tests _generate_omf_typename_automatic """

        sending_process_instance = MagicMock()
        config = []
        config_omf_types = []
        logger = MagicMock()

        omf_north = omf.OmfNorthPlugin(sending_process_instance, config, config_omf_types, logger)

        generated_typename = omf_north._generate_omf_typename_automatic(p_asset_code)

        assert generated_typename == expected_typename

    @pytest.mark.parametrize(
        "p_type_id, "
        "p_asset_code_omf_type, "
        "expected_typename, "
        "expected_omf_type, ",
        [
            # Case 1
            (
                # p_type_id
                "0001",
                
                # p_asset_code_omf_type
                {
                    "typename": "position",
                    "static": {
                        "Name": {
                            "type": "string",
                            "isindex": True
                        },
                        "Location": {
                            "type": "string"
                        }
                    },
                    "dynamic": {
                        "Time": {
                            "type": "string",
                            "format": "date-time",
                            "isindex": True
                        },
                        "x": {
                            "type": "number"
                        },
                        "y": {
                            "type": "number"
                        },
                        "z": {
                            "type": "number"
                        }
                    }
                },

                # expected_typename
                "position",

                # expected_omf_type
                {
                    "position": [
                        {
                            "id": "0001_position_sensor",
                            "type": "object",
                            "classification": "static",
                            "properties": {
                                "Name": {
                                     "type": "string",
                                     "isindex": True
                                     },
                                "Location": {
                                     "type": "string"
                                      }
                            }
                        },
                        {
                            "id": "0001_position_measurement",
                            "type": "object",
                            "classification": "dynamic",
                            "properties": {
                                "Time": {
                                    "type": "string",
                                    "format": "date-time",
                                    "isindex": True
                                },
                                "x": {
                                    "type": "number"
                                },
                                "y": {
                                    "type": "number"
                                },
                                "z": {
                                    "type": "number"
                                }

                            }
                        }

                    ]
                }
            )
        ]
    )
    def test_create_omf_type_configuration_based(
            self,
            p_type_id,
            p_asset_code_omf_type,
            expected_typename,
            expected_omf_type
    ):
        """ Tests the generation of the OMF messages using Configuration Based OMF Type Mapping"""

        sending_process_instance = MagicMock()
        config = []
        config_omf_types = []
        logger = MagicMock()

        omf_north = omf.OmfNorthPlugin(sending_process_instance, config, config_omf_types, logger)

        omf_north._config_omf_types = {"type-id": {"value": p_type_id}}

        with patch.object(omf_north, 'send_in_memory_data_to_picromf', return_value=True) as patched_send_to_picromf:
            generated_typename, \
                generated_omf_type = omf_north._create_omf_type_configuration_based(p_asset_code_omf_type)

        assert generated_typename == expected_typename
        assert generated_omf_type == expected_omf_type

        patched_send_to_picromf.assert_any_call("Type", expected_omf_type[expected_typename])

    @pytest.mark.parametrize(
        "p_key, "
        "p_value, "
        "expected, ",
        [
            # Good cases
            ('producerToken', "xxx", "good"),

            # Bad cases
            ('NO-producerToken', "", "exception"),
            ('producerToken', "", "exception")
        ]
    )
    def test_validate_configuration(
                                    self,
                                    p_key,
                                    p_value,
                                    expected):
        """ Tests the validation of the configurations retrieved from the Configuration Manager
            handled by _validate_configuration """

        omf._logger = MagicMock()

        data = {p_key: {'value': p_value}}

        if expected == "good":
            assert not omf._logger.error.called

        elif expected == "exception":
            with pytest.raises(ValueError):
                omf._validate_configuration(data)

            assert omf._logger.error.called

    @pytest.mark.parametrize(
        "p_key, "
        "p_value, "
        "expected, ",
        [
            # Good cases
            ('type-id', "xxx", "good"),

            # Bad cases
            ('NO-type-id', "", "exception"),
            ('type-id', "", "exception")
        ]
    )
    def test_validate_configuration_omf_type(
                                    self,
                                    p_key,
                                    p_value,
                                    expected):
        """ Tests the validation of the configurations retrieved from the Configuration Manager
            related to the OMF types """

        omf._logger = MagicMock()

        data = {p_key: {'value': p_value}}

        if expected == "good":
            assert not omf._logger.error.called

        elif expected == "exception":
            with pytest.raises(ValueError):
                omf._validate_configuration_omf_type(data)

            assert omf._logger.error.called
