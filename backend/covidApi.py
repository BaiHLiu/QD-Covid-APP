from datetime import datetime
import requests
import base64
import json
from threading import Thread
import math
import xlwt
import traceback

from utils import Requests

global conf
with open('config.json', 'r') as f:
    conf = json.load(f)


class CovidPlatform:
    def __init__(self, token, file_name, isSpecific=False, specificDate=[]) -> None:
        self.__user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
        self.__token = token
        self.__file_name = file_name
        self.__ret_list = []

        self.__workForCollage()
        if isSpecific:
            self.__printSpecificResult(specificDate)
        else:
            self.__printTodayResult()

    def __workForClass(self, stu_list, class_info):
        """
        获取班级情况
        :param stu_list:
        :return:
        """

        # 多线程
        thread_list = []
        split_count = 4
        times = math.ceil(len(stu_list) / split_count)
        count = 0

        for item in range(times):
            _list = stu_list[count: count + split_count]
            thread = Thread(target=self.__getLatestRecord, args=(_list, class_info))
            thread_list.append(thread)
            thread.start()
            count += split_count

        for _item in thread_list:
            _item.join()

    def __printTodayResult(self):
        """
        整理当日结果
        """

        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Sheet1')
        worksheet.write(0, 0, label='导出时间：' + str(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M')))
        worksheet.write(1, 0, label='班级')
        worksheet.write(1, 1, label='姓名')
        worksheet.write(1, 2, label='电话')
        worksheet.write(1, 3, label='今日已采')
        worksheet.write(1, 4, label='最新时间')
        worksheet.write(1, 5, label='辅导员姓名')
        worksheet.write(1, 6, label='辅导员电话')
        worksheet.write(1, 7, label='学生状态')

        count_yes = 0
        count_no = 0

        for idx, stu in enumerate(self.__ret_list):
            try:
                # 可能没有采样时间
                if stu['peopleTestResultList']:
                    gather_dt = datetime.strptime(stu['peopleTestResultList'][0]['gatheringTime'], '%Y-%m-%d %H:%M')
                else:
                    gather_dt = datetime.strptime('1970-01-01 00:00', '%Y-%m-%d %H:%M')

                today_d = datetime.today().date()

                worksheet.write(idx + 2, 0, label=stu['class_name'])
                worksheet.write(idx + 2, 1, label=stu['data']['studentName'])
                worksheet.write(idx + 2, 2, label=stu['data']['telephone'])
                worksheet.write(idx + 2, 7, label=stu['data']['studentStatus'])

                worksheet.col(0).width = 256 * 25
                worksheet.col(2).width = 256 * 15
                worksheet.col(4).width = 256 * 20
                worksheet.col(6).width = 256 * 15

                if today_d != gather_dt.date():
                    worksheet.write(idx + 2, 3, '否')
                    count_no += 1
                else:
                    worksheet.write(idx + 2, 3, '是')
                    count_yes += 1

                worksheet.write(idx + 2, 4, datetime.strftime(gather_dt, '%Y-%m-%d %H:%M'))
                worksheet.write(idx + 2, 5, stu['teacher_name'])
                worksheet.write(idx + 2, 6, stu['teacher_phone'])
            except:
                print("写入错误：" + stu['data']['studentName'])
                traceback.print_exc()
                continue

        workbook.save(conf['static_path'] + self.__file_name)

    def __printSpecificResult(self, date_list):
        """
        整理指定日期结果
        """

        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Sheet1')
        worksheet.write(0, 0, label='导出时间：' + str(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M')))
        worksheet.write(1, 0, label='班级')
        worksheet.write(1, 1, label='姓名')
        worksheet.write(1, 2, label='电话')
        worksheet.write(1, 3 + len(date_list), '均未检测')
        worksheet.write(1, 4 + len(date_list), '学生状态')
        worksheet.write(1, 5 + len(date_list), '辅导员姓名')
        worksheet.write(1, 6 + len(date_list), '辅导员电话')

        for _c, _dt in enumerate(date_list):
            worksheet.write(1, 3 + _c, str(_dt))

        # 遍历学生
        for _r, _stu in enumerate(self.__ret_list):
            # 填入基本信息
            worksheet.write(_r + 2, 0, _stu['class_name'])
            worksheet.write(_r + 2, 1, _stu['data']['studentName'])
            worksheet.write(_r + 2, 2, _stu['data']['telephone'])
            worksheet.write(_r + 2, 4 + len(date_list), _stu['data']['studentStatus'])
            worksheet.write(_r + 2, 5 + len(date_list), _stu['teacher_name'])
            worksheet.write(_r + 2, 6 + len(date_list), _stu['teacher_phone'])

            # 遍历日期
            gather_date_list = []
            if _stu['peopleTestResultList']:
                for _gather in _stu['peopleTestResultList']:
                    gather_date_list.append(datetime.strptime(_gather['gatheringTime'], '%Y-%m-%d %H:%M').date())

            g_flag = 0
            for _c, _dt in enumerate(date_list):
                _dt = datetime.strptime(_dt, '%Y-%m-%d').date()
                if _dt in gather_date_list:
                    worksheet.write(_r + 2, 3 + _c, '是')
                    g_flag = 1
                else:
                    worksheet.write(_r + 2, 3 + _c, '否')

            # 均未检测
            if g_flag == 0:
                worksheet.write(_r + 2, 3 + len(date_list), '是')
            else:
                worksheet.write(_r + 2, 3 + len(date_list), '否')

        workbook.save(conf['static_path'] + self.__file_name)

    def __getStudentList(self, classId):
        """
        获取学生列表
        """
        headers = {
            'Authorization': 'Bearer ' + self.__token
        }
        resp = requests.get(
            url='https://yqpt.qingdao.gov.cn:8443/schoolapi/student/info/list',
            params={
                'pageNum': 1,
                'pageSize': 50000,
                'classId': classId
            },
            headers=headers
        )

        resp = json.loads(resp.text)
        if resp['code'] != 200:
            print(resp['msg'])
            return

        else:
            return resp['rows']

    def __getClassList(self):
        headers = {
            'Authorization': 'Bearer ' + self.__token
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
        if resp['code'] != 200:
            print('获取班级列表: ' + resp['msg'])
        else:
            return resp['rows']

    def __getLatestRecord(self, stu_list, class_info):
        """
        获取最新一次采集记录
        """
        headers = {
            'Authorization': 'Bearer ' + self.__token
        }
        for stu in stu_list:
            resp = Requests.get(
                url='https://yqpt.qingdao.gov.cn:8443/schoolapi/student/info/getViewInfo',
                params={
                    'id': stu['id']
                },
                headers=headers
            )
            resp_ext = json.loads(resp.text)

            resp_ext['class_name'] = class_info['className']
            resp_ext['teacher_name'] = class_info['headTeacher']
            resp_ext['teacher_phone'] = class_info['telephone']

            self.__ret_list.append(resp_ext)

    def __identify_captcha(self, img64):
        with open('captcha.gif', 'wb') as f:
            f.write(base64.b64decode(img64))

        code = input('请输入验证码：')
        return code

    def __workForCollage(self):
        """
        学院工作专用
        """
        # 获取班级列表
        class_list = self.__getClassList()

        print('获取班级列表成功：共计' + str(len(class_list)) + '个班级')

        for idx, cla in enumerate(class_list):
            print(f"处理{str(idx + 1)}/{str(len(class_list))} : {cla['className']}")
            try:
                # 获取学生列表
                stu_list = self.__getStudentList(cla['id'])
                # 处理各班级
                self.__workForClass(stu_list, cla)
            except:
                print("出错：" + cla['className'])
