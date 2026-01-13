import datetime
import logging
import ssl
import os
import requests

class TEMPAPI:
    end_point = 'https://eactivities.union.ic.ac.uk/API'

    paths = {
        'list_csp':                     '/CSP',
        'csp_details':                  '/CSP/{code}',

        'list_all_products':            '/CSP/{code}/Products',
        'product_details':              '/CSP/{code}/Products/{id}',
        'product_sales':                '/CSP/{code}/Products/{id}/Sales',

        'profile_entry':                '/CSP/{code}/ProfileEntry',

        'list_purchase_orders':         '/CSP/{code}/PurchaseOrders',
        'purchase_order_details':       '/CSP/{code}/PurchaseOrders/{id}',

        'list_committee':               '/CSP/{code}/Reports/Committee?year={year}',
        'list_members':                 '/CSP/{code}/Reports/Members?year={year}',
        'list_online_sales':            '/CSP/{code}/Reports/OnlineSales?year={year}',
        'list_products':                '/CSP/{code}/Reports/Products?year={year}',
        'list_transaction_lines':       '/CSP/{code}/Reports/TransactionLines?year={year}',

        'list_signups':                 '/CSP/{code}/Signups',
        'signup_details':               '/CSP/{code}/Signups/{id}',

        'list_whatson':                 '/CSP/{code}/WhatsOn',
        'whatson_details':              '/CSP/{code}/WhatsOn/{id}',

        'list_years':                   '/CSP/{code}/Years',
    }

    def __init__(self, csp_code, api_key, year, verify=True):
        self.csp_code = csp_code
        self.headers = {
            'X-API-Key': api_key,
        }
        self.year = year
        self.verify = verify
        self.__setup_functions()

    def __setup_functions(self):
        for function_name in self.paths.keys():
            self.__setattr__(function_name, self.__create_function(function_name))

    def __get(self, path):
        return requests.get(self.end_point + path, headers=self.headers, verify=self.verify)

    def __get_json(self, path):
        return self.__get(path).json()

    def __create_function(self, function_name):
        def __call_function(*args, **kwargs):
            path_format = self.paths[function_name]
            year = kwargs.get('year') or self.year
            path = path_format.format(code=self.csp_code, year=year, **kwargs)
            return self.__get_json(path)
        return __call_function

# from icu_ea_api import ICUEActivitiesAPI
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
LAB_ACCESS_ID = [54837, 54174]

# ===== Get the API key =====

api_key = os.getenv('API_KEY')
society_api = TEMPAPI(CSP_CODE, api_key, year_string, verify=False)

# =========================================


society_members = []
passes = []
last_update = datetime.datetime(2000, 1, 1)
last_update_passes = datetime.datetime(2000, 1, 1)
timeout = datetime.timedelta(seconds=5)

api = TEMPAPI(CSP_CODE, api_key, year_string, verify=False)

def update_labpasses(function):
    def query_api(*args, **kwargs):
        global last_update_passes
        now = datetime.datetime.now()

        if now > last_update_passes + timeout:
            global passes
            passes.clear()
            for prodid in LAB_ACCESS_ID:
                passes += api.product_sales(id=prodid)
            last_update_passes = now
            logging.debug("updated lab passes")
        
            return function(*args, **kwargs)
    return query_api

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

@update_labpasses
def has_labpass(shortcode : str) -> bool:
    return shortcode in [item["Customer"]["Login"] for item in passes]