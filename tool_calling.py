
tools = [
    {
        "type": "function",
        "function": {
            "name": "add_device",
            "description": "Add a new network device, switch our router to Catalyst Center. "
                           "Call this function when user asks to add a network device, device, node, host, "
                           "to the inventory or Catalyst Center while providing an IP address of device "
                           "to manage the device. For example: an user asks for 'add device'",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_ip_address": {
                        "type": "string",
                        "description": "This is the device IP address that will be used to manage the device"
                        },
                "required": [
                    "device_ip_address"
                    ]
                }
            }
        }
    }
]






