import requests
import json

from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def getClassList(token):
    headers = {
        'Authorization': 'Bearer ' + token
    }
    resp = requests.get(
        url='https://yqpt.qingdao.gov.cn:8443/schoolapi/class/info/myCollegeClassList',
        params={
            'pageNum': 1,
            'pageSize': 50000
        },
        headers=headers
    )

    resp = json.loads(resp.text)
    return resp
    

class Requests:
    def post(url, data, headers=None):
        s = requests.Session()
        s.mount('http://',
                HTTPAdapter(max_retries=Retry(total=3, backoff_factor=5, method_whitelist=frozenset(['GET', 'POST']))))
        s.mount('https://',
                HTTPAdapter(max_retries=Retry(total=3, backoff_factor=5, method_whitelist=frozenset(['GET', 'POST']))))

        r = s.post(url=url, data=data, timeout=5, headers=headers)
        return r

    def get(url, params, headers=None):
        s = requests.Session()
        s.mount('http://',
                HTTPAdapter(max_retries=Retry(total=3, backoff_factor=5, method_whitelist=frozenset(['GET', 'POST']))))
        s.mount('https://',
                HTTPAdapter(max_retries=Retry(total=3, backoff_factor=5, method_whitelist=frozenset(['GET', 'POST']))))

        r = s.get(url=url, params=params, timeout=5, headers=headers)
        return r


