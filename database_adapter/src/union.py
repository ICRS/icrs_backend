from icu_ea_api import ICUEActivitiesAPI
import os
from dotenv import load_dotenv
from datetime import date


load_dotenv()


# ===== Get the current date =====
date_now = date.today()
month_now = date_now.month
year_now = str(date_now.year)
if month_now >= 8:
    year_string = f"{year_now[2:]}-{int(year_now[2:])+1}"
else:
    year_string = f"{int(year_now[2:])-1}-{year_now[2:]}"

# =================================

CSP_CODE = 625

# ===== Get the API key =====

api_key = os.getenv('API_KEY')
society_api = ICUEActivitiesAPI(CSP_CODE, api_key, year_string)

# =========================================


def isMember(shortcode: str) -> bool:
    return shortcode in [member['Login']
                         for member in society_api.list_members()]


def getShortcodesToCIDAndName(shortcodes) -> list:
    d = {member['Login']: (f"{member['FirstName']} {member['Surname']}",
                           member['CID'], member['Login'])
         for member in society_api.list_members()}
    return list(set(d[s] for s in shortcodes if s in d))


def is_member_list(shortcodes: list[str]) -> bool:
    try:
        members = set(member['Login'] for member in society_api.list_members())
        shortcodes = [code for code in shortcodes if code in members]
        return shortcodes
    except Exception:
        print("Error contacting Society API")
        return False
