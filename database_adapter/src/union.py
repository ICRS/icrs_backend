import datetime
import logging
from icu_ea_api import ICUEActivitiesAPI
import os
from datetime import date


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


society_members = []
last_update = datetime.datetime(2000, 1, 1)
timeout = datetime.timedelta(seconds=5)


def update_members(function):
    def query_api(*args, **kwargs):
        global last_update
        now = datetime.datetime.now()

        if now > last_update + timeout:
            global society_members
            society_members = society_api.list_members()
            last_update = now
            logging.debug("Updated society members list")

        return function(*args, **kwargs)
    return query_api


@update_members
def isMember(shortcode: str) -> bool:
    return shortcode in [member['Login']
                         for member in society_members]


@update_members
def getShortcodesToCIDAndName(shortcodes) -> list:
    d = {member['Login']: (f"{member['FirstName']} {member['Surname']}",
                           member['CID'], member['Login'])
         for member in society_members}
    return list(set(d[s] for s in shortcodes if s in d))


@update_members
def is_member_list(shortcodes: list[str]) -> bool:
    try:
        members = set(member['Login'] for member in society_members)
        shortcodes = [code for code in shortcodes if code in members]
        return shortcodes
    except Exception:
        print("Error contacting Society API")
        return False


@update_members
def cid_to_shortcode(cid: str) -> str | None:
    return next(
        (member["Login"] for member in society_members
         if member["CID"] == cid),
        None)
