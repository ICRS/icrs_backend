import pymiwifi 
from dotenv import load_dotenv
import json
load_dotenv()
import requests
import random
import os

mac_set = set(json.loads(os.environ['MAC_ADDRESS']))
router_pwd = os.environ["ROUTER_PWD"]

miwifi = pymiwifi.MiWiFi(address="http://192.168.31.1/")
print("Login:", miwifi.login(router_pwd))

current_mac = miwifi.get_api_endpoint("xqnetwork/wan_info")["info"]["mac"]
print("Current mac:", current_mac)
mac_set.remove(current_mac)

new_mac = random.choice(tuple(mac_set))
o = {"mac": new_mac}
print(requests.get(f"{miwifi.address}/cgi-bin/luci/;stok={miwifi.token}/api/xqnetwork/mac_clone", params=o).json())


reboot_param = {"client":"web"}

print(requests.get(f"{miwifi.address}/cgi-bin/luci/;stok={miwifi.token}/api/xqsystem/reboot", params=reboot_param).json())

