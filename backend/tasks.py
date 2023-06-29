import time
from celery import Celery
from covidApi import CovidPlatform

celery = Celery('tasks', broker='redis://localhost:6379/10')

@celery.task
def generateFile(file_name, token, is_specific, specific_date_list):
    CovidPlatform(token, file_name, is_specific, specific_date_list)