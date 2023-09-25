from icu_ea_api import ICUEActivitiesAPI
import os
from dotenv import load_dotenv
load_dotenv()

csp_code = 625
api_key = os.getenv('API_KEY')
year = '23-24'
society_api = ICUEActivitiesAPI(csp_code, api_key, year)

def isMember(shortcode: str) -> bool:
    return shortcode in [member['Login'] for member in society_api.list_members()]

def getShortcodesToCIDAndName(shortcodes) -> list:
    d = {member['Login']: (f"{member['FirstName']} {member['Surname']}", member['CID']) for member in society_api.list_members()}
    return [d[s] for s in shortcodes if s in d]