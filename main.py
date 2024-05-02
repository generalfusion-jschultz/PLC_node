#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Matthew Davidson
# Created Date: 2023-01-23
# version ='1.0'
# ---------------------------------------------------------------------------
"""Connects to a Beckhoff PLC using pyads and publishes data through MQTT"""
# ---------------------------------------------------------------------------
from plc_node.plc_node import PlcNode
from mqtt_node_network.initialize import initialize
import time

config, logger = initialize(
    config="config/config.toml", secrets=".env", logger="config/logger.yaml"
)
BROKER_CONFIG = config["mqtt"]["broker"]
PUBLISH_PERIOD = 2

def main():
    plc = PlcNode(
        broker_config = BROKER_CONFIG,
        name = "plc",
        node_id = "plc_node_0"
    )
    t = 0.0
    with plc:
        while True:
            plc.write_data_to_plc("MAIN.tc2", t)
            print(f"{t} written to PLC variable 'MAIN.tc2'.")
            t += 0.25
            plc.publish()
            # logger.info(f"{plc.get_data()}")
            print(f"{plc.get_data()}")
            time.sleep(PUBLISH_PERIOD)


if __name__ == "__main__":
    main()
