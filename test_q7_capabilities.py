import asyncio
import logging
from roborock.web_api import RoborockApiClient
from roborock.devices.device_manager import create_device_manager, UserParams

# Configure logging
logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

async def main():
    email = input("Enter your email address: ")
    web_api = RoborockApiClient(email)
    
    print("Requesting login code...")
    await web_api.request_code_v4()
    
    code = input("Enter the verification code sent to your email: ")
    print("Logging in...")
    user_data = await web_api.code_login_v4(code)
    
    print("Discovering devices...")
    device_manager = await create_device_manager(UserParams(email, user_data))
    devices = await device_manager.get_devices()
    
    if not devices:
        print("No devices found.")
        return

    print(f"Found {len(devices)} devices.")
    
    for i, device in enumerate(devices):
        print(f"Device {i}: {device.name} (Product: {device.product.model})")
        
        if device.b01_q7_properties:
            print(f"  - Has Q7 Properties (B01)")
            print("  - Available attributes/methods in b01_q7_properties:")
            
            # Inspect the properties object
            props = device.b01_q7_properties
            for attr in dir(props):
                if not attr.startswith("_"):
                    val = getattr(props, attr)
                    if callable(val):
                        print(f"    - Method: {attr}")
                    else:
                        print(f"    - Property: {attr}")
            
            # Example of using a command if you know the name
            # await props.set_fan_speed(101) 
        else:
            print("  - No Q7 Properties found")

if __name__ == "__main__":
    asyncio.run(main())
