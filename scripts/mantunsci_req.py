import requests
from XNBackend.api_client.mantunsci import MantunsciAuthInMemory


def data_req(req_body):
    s = requests.Session()
    s.auth = MantunsciAuthInMemory(
        'http://10.100.101.198:8088/ebx-rook/',
        'prod',
        'abc123++',
        'O000000063',
        '590752705B63B2DADD84050303C09ECF',
        'http://10.100.101.198:8088/ebx-rook/demo.jsp',
    )
    resp = s.post('http://10.100.101.198/ebx-rook/invoke/router.as', req_body)
    return resp
