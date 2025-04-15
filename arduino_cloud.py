from arduino_iot_client import ArduinoCloudClient, DeviceV2, Thing, PropertyValue
from arduino_iot_client.rest import ApiException
from arduino_iot_client.configuration import Configuration

import time

class ArduinoCloudManager:
    def __init__(self, device_id, client_id, client_secret):
        self.device_id = device_id
        self.client_id = client_id
        self.client_secret = client_secret 

        config = Configuration()
        config.client_id = self.client_id
        config.client_secret = self.client_secret

        self.client = ArduinoCloudClient(config)

        # Get device and things
        self.device = self.client.devices_v2.get_device(self.device_id)
        self.thing_id = self.device.associated_things[0] if self.device.associated_things else None
        self.properties = self.client.things_v2.list_properties(self.thing_id)

    def set_variable(self, variable_name, value):
        for prop in self.properties:
            if prop.name == variable_name:
                self.client.properties_v2.publish(self.thing_id, prop.id, PropertyValue(value=value))
                return True
<<<<<<< HEAD
        return False
=======
        return False
>>>>>>> 621a48c (connnection)
