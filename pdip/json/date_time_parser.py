import re
from datetime import datetime


def date_time_parser(dct):
    for k, v in dct.items():
        reg_T = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.{0,1}\d{0,6}$')
        reg_iso = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.{0,1}\d{0,6}$')
        if isinstance(v, str) and reg_T.match(v):
            dct[k] = datetime.strptime(v, "%Y-%m-%dT%H:%M:%S.%f")
        elif isinstance(v, str) and reg_iso.match(v):
            dct[k] = datetime.strptime(v, "%Y-%m-%d %H:%M:%S.%f")
    return dct
