import pytest
import pyads
from mqtt_node_network.node import (MQTTNode, MQTTBrokerConfig)
from plc_node.plc_node import PlcNode

# Tutorial on how to mock
# https://www.freblogg.com/pytest-functions-mocking-1

BROKER_CONFIG = MQTTBrokerConfig(
    username = "test_user",
    password = "test_password",
    keepalive = 60,
    hostname = "test_host",
    port = 1883,
    timeout = 1,
    reconnect_attempts = 3
)


def test_plc(mocker):  
    mocker.patch("pyads.connection.Connection.open", return_value = None)
    mocker.patch("pyads.connection.Connection.read_state", return_value = (5,0))
    mocker.patch("plc_node.plc_node.connect_to_plc", return_value = None)

    plc = PlcNode(
        BROKER_CONFIG,
        name = "test_plc",
        node_id = "test_node",
        node_type = "node_type",
        logger = None,
        subscriptions = None
    )

    assert plc.name == "test_plc"
    assert plc.node_id == "test_node"
    assert plc.node_type == "node_type"
    assert plc._username == "test_user"
    assert plc._password == "test_password"
    assert plc.port == 1883
    assert plc.timeout == 1
    assert plc.reconnect_attempts == 3
    assert plc.keepalive == 60
    assert plc.hostname == "test_host"


def test_read_correct_plc_value(mocker):
    fake_data: dict[str, float] = {
        "TC 1": 20.0,
        "TC 2": 20.0
    }
    
    mocker.patch("pyads.connection.Connection.open", return_value = None)
    mocker.patch("pyads.connection.Connection.read_state", return_value = (5,0))
    mocker.patch("plc_node.plc_node.connect_to_plc", return_value = None)
    mocker.patch("pyads.connection.Connection.read_by_name", return_value = 20.0)

    plc = PlcNode(
        BROKER_CONFIG,
        name = "test_plc",
        node_id = "test_node",
        node_type = "node_type",
        logger = None,
        subscriptions = None
    )

    with plc:
        data = plc.process_data()
    
    assert(data == fake_data)


def test_read_incorrect_plc_value(mocker):
    fake_data: dict[str, float] = {
        "TC 1": 20.0,
        "TC 2": 20.0
    }
    
    mocker.patch("pyads.connection.Connection.open", return_value = None)
    mocker.patch("pyads.connection.Connection.read_state", return_value = (5,0))
    mocker.patch("plc_node.plc_node.connect_to_plc", return_value = None)
    mocker.patch("pyads.connection.Connection.read_by_name", return_value = "not a float")

    plc = PlcNode(
        BROKER_CONFIG,
        name = "test_plc",
        node_id = "test_node",
        node_type = "node_type",
        logger = None,
        subscriptions = None
    )

    with plc:
        data = plc.process_data()
    
    assert(data == {})


def test_publish(mocker):
    mocker.patch("pyads.connection.Connection.open", return_value = None)
    mocker.patch("pyads.connection.Connection.read_state", return_value = (5,0))
    mocker.patch("plc_node.plc_node.connect_to_plc", return_value = None)
    mocker.patch("pyads.connection.Connection.read_by_name", return_value = 20.0)
    mocker.patch("mqtt_node_network.node.MQTTNode.publish", return_value = None)

    plc = PlcNode(
        BROKER_CONFIG,
        name = "test_plc",
        node_id = "test_node",
        node_type = "node_type",
        logger = None,
        subscriptions = None
    )

    with plc:
        topic, payload = plc.publish(debug = True)
    
    assert(topic == "testing/test_node/temperature/TC 2")
    assert(payload == 20.0)