#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Matthew Davidson
# Created Date: 2023-01-23
# version ='1.0'
# ---------------------------------------------------------------------------
"""a_short_module_description"""
# ---------------------------------------------------------------------------
import pyads
from mqtt_node_network.node import (MQTTNode, MQTTBrokerConfig)
from mqtt_node_network.configure import load_config
import logging
import socket
import time

logger = logging.getLogger("__name__")

PLC_FILEPATH = "./config/plc_info.yaml"
file = load_config(PLC_FILEPATH)
PLC_AMS_NET_ID: str = file["plc"]["ams_net_id"]
PLC_IP: str = file["plc"]["ip_address"]
PLC_PORT: str = file["plc"]["plc_port"]
PLC_VAR: dict[str, str] = file["plc"]["var_names"]
PLC_USERNAME: str = "Administrator"
PLC_PASSWORD: str = "1"


def get_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def connect_to_plc(client_ip:str) -> None:
    client_ams_net_id: str = client_ip + ".1.1"
    pyads.set_local_address(client_ams_net_id)  # Sender AMS is Linux IP + 1.1
    route_flag: bool = pyads.add_route_to_plc(
        sending_net_id = client_ams_net_id,
        adding_host_name = client_ip,
        ip_address = PLC_IP,
        username = PLC_USERNAME,
        password = PLC_PASSWORD,
    )
    print(f"Set local address: {route_flag}")


class PlcNode (MQTTNode):
    def __init__(
            self,
            broker_config: MQTTBrokerConfig,
            name: str = None,
            node_id: str = None,
            node_type: str = None,
            logger = None,
            subscriptions: list = None,
        ):
        MQTTNode.__init__(
            self,
            broker_config = broker_config,
            name = name,
            node_id = node_id,
            node_type = node_type,
            logger = logger,
            subscriptions = subscriptions
        )
        client_ip: str = get_ip()
        connect_to_plc(client_ip)
        pyads.open_port()
        self.plc = pyads.Connection(PLC_AMS_NET_ID, PLC_PORT, PLC_IP)
        
        attempt:int = 0
        plc_state = None
        while (attempt < self.reconnect_attempts) and (plc_state is None):
            try:
                self.plc.open()
            except pyads.ADSError as e:
                print(f"{e}")
                time.sleep(self.timeout)
                attempt += 1
                pass

            try:
                plc_state = self.plc.read_state()
            except pyads.ADSError as e:
                print(f"{e}")
                time.sleep(self.timeout)
                attempt += 1
        
        if plc_state is None:
            raise TimeoutError("Timeout occurred trying to connect to PLC")


    def __enter__(self) -> None:
        self.plc.open()

    
    def __exit__(self, type, value, traceback) -> None:
        self.plc.close()        


    def get_data(self) -> dict[str, float]:
        data: dict[str, float] = {}
        for (plc_variable_name, published_variable_name) in PLC_VAR.items():
            # CHECK IF VARIABLE NAME EXISTS
            value: float = self.plc.read_by_name(plc_variable_name)
            if isinstance(value, float):
                data.update({published_variable_name: value})
        return data
            

    def process_data(self) -> dict[str, float]:
        if self.plc.is_open:
            return self.get_data()
        else:
            with self.plc:
                return self.get_data()
    

    def publish(self, debug: bool = False) -> tuple[str, float]:
        data: dict[str, float] = self.process_data()
        if data: # data is not empty
            for (datum, value) in data.items():
                topic: str = f"testing/{self.node_id}/temperature/{datum}"
                payload: float = value
                MQTTNode.publish(
                    self,
                    topic = topic,
                    payload = payload
                )
        if debug:
            if data:
                return (topic, payload)
        else:
            return None