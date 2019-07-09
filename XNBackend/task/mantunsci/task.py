import requests
from mantunsci_auth.auth import MantunsciAuthBase
from XNBackend.task import celery


auth_url = ''
username = ''
password = ''
app_key = ''
app_secret = ''
project_code = ''
redirect_uri = ''


@celery.task()
def power_month():
    r = request.post(auth_url, auth=MantunsciAuthBase(auth_url, username, password, app_key, app_secret, project_code, redirect_uri))    


@celery.task()
def power_day():
    r = request.post(auth_url, auth=MantunsciAuthBase(auth_url, username, password, app_key, app_secret, project_code, redirect_uri))    


@celery.task()
def power_current():
    r = request.post(auth_url, auth=MantunsciAuthBase(auth_url, username, password, app_key, app_secret, project_code, redirect_uri))    






