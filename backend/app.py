from flask import Flask, jsonify, request
import requests
import json
import utils
from flask_cors import CORS
import uuid
from covidApi import CovidPlatform
from tasks import generateFile
import os

app = Flask(__name__)
CORS(app)

######################
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 ' \
     'Safari/537.36'
HEADERS = {'User-Agent': UA}
PREFIX = ''

######################

global conf
with open('config.json', 'r') as f:
    conf = json.load(f)


@app.route(PREFIX + '/hello')
def hello():
    return jsonify({
        'code': 0,
        'msg': 'world!',
    })


@app.route(PREFIX + '/getCaptcha')
def getCaptcha():
    """
    获取验证码
    :return:
    """

    resp = requests.get(
        url='https://yqpt.qingdao.gov.cn:8443/schoolapi/captchaImage',
        headers=HEADERS
    )
    resp = json.loads(resp.text)

    ret = {
        'code': resp['code'],
        'msg': resp['msg'],
        'img': resp['img'],
        'uuid': resp['uuid']
    }

    return jsonify(ret)


@app.route(PREFIX + '/login', methods=['POST'])
def login():
    """
    用户登陆
    :return:
    """
    json_re = json.loads(request.get_data())
    headers = {
        'User-Agent': UA,
        'Cookie': 'username=' + json_re['username'],
        'Content-Type': 'application/json;charset=UTF-8'
    }
    login_data = {
        'username': json_re['username'],
        'password': json_re['password'],
        'code': json_re['code'],
        'uuid': json_re['uuid']
    }

    resp = requests.post(
        url='https://yqpt.qingdao.gov.cn:8443/schoolapi/login',
        headers=headers,
        data=json.dumps(login_data)
    )

    resp = json.loads(resp.text)

    userAlias = ''
    token = ''
    classCount = 0

    if resp['code'] == 200:
        userAlias = resp['userName']
        token = resp['token']

        # 获取班级数目

        try:
            classCount = utils.getClassList(token)['total']
        except:
            pass
    ret = {
        'code': resp['code'],
        'msg': resp['msg'],
        'userAlias': userAlias,
        'token': token,
        'classCount': classCount
    }

    return jsonify(ret)


@app.route(PREFIX + '/college/generateFile', methods=['POST'])
def college_generateFile():
    json_re = json.loads(request.get_data())
    specific_date = False
    date_list = []
    if 'specific_date' in json_re.keys():
        if 'date_list' not in json_re.keys() or not json_re['date_list']:
            return jsonify({
                'code': -1,
                'msg': '请指定日期！'
            })
        else:
            specific_date = json_re['specific_date']
            date_list = json_re['date_list']

    file_name = str(uuid.uuid4()) + '.xls'

    ret = {
        'code': 200,
        'msg': 'ok',
        'file_name': file_name
    }

    generateFile.delay(file_name, json_re['token'], specific_date, date_list)

    return jsonify(ret)


@app.route(PREFIX + '/getDownloadPath', methods=['GET'])
def getDownloadPath():
    file_name = request.args.get("file_name")

    ret = {
        'code': 200,
        'msg': 'ok',
        'is_generated': 0,
        'file_url': ''
    }

    print(conf['static_path'] + file_name)
    if os.path.exists(conf['static_path'] + file_name):
        ret['is_generated'] = 1
        ret['file_url'] = conf['download_url'] + file_name

    return jsonify(ret)


@app.route(PREFIX + '/checkLogin', methods=['GET'])
def checkLogin():
    token = request.args.get('token')
    hd = HEADERS.copy()
    hd['Authorization'] = 'Bearer ' + token

    resp = requests.get(
        url='https://yqpt.qingdao.gov.cn:8443/schoolapi/college/info/getMyViewInfo',
        headers=hd

    )

    resp = json.loads(resp.text)
    return jsonify(resp)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8001)
