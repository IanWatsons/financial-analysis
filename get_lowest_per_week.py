# encoding: utf-8

import requests
import time
import execjs
import calendar
import datetime
import collections
import argparse

from bs4 import BeautifulSoup
from prettytable import *

parser = argparse.ArgumentParser()
parser.add_argument('--code', dest='code', help='基金代码')
parser.add_argument('--start_year', dest='start_year', help='起始年份')
parser.add_argument('--end_year', dest='end_year', help='结束年份')

def date_list_fun(starttime, endtime):
    """
    计算输入的起始日期和结束日期之间的所有日期
    :param starttime: 起始日期
    :param endtime: 结束日期
    :return: 起始日期和结束日期之间的日期
    """
    _u = datetime.timedelta(days=1)
    start_date = datetime.datetime.strptime(starttime,'%Y%m%d')
    end_date = datetime.datetime.strptime(endtime,'%Y%m%d')
    n = 0
    date_list = []
    if start_date <= end_date:
        while 1:
            _time = start_date + n*_u
            date_list.append(_time.strftime('%Y%m%d'))
            n = n + 1
            if _time == end_date:
                break
    return date_list

 
def all_weeks(year):
    """
    计算一年内所有周的起始日期
     week_date_start_end {1: ['20181231','20190106'],...}
    :param year: 输入年份
    :return: 一年内所有周的其实和结束日期list
    """
    start_date = datetime.datetime.strptime(str(int(year)-1) + '1224', '%Y%m%d')
    end_date = datetime.datetime.strptime(str(int(year)) + '1231', '%Y%m%d')
    _u = datetime.timedelta(days=1)
    n = 0
    week_date = {}
    while 1:
        _time = start_date+n*_u
        y, w = _time.isocalendar()[:2]
        if y == year:
            week_date.setdefault(w, []).append(_time.strftime('%Y%m%d'))
        n = n+1
        if _time == end_date:
            break
    week_date_start_end = {}
    for i in week_date:
        week_date_start_end[i] = [week_date[i][0],week_date[i][-1]]
    return week_date_start_end


def get_lowest(code, sdate, edate):
    """
    获取一周内基金净值最低的一天
    :param code: 基金代码
    :param sdate: 起始日期
    :param edate: 结束日期
    :return: 净值最低的一天
    """
    records = get_fund_data(code, sdate, edate)
    asset_value = 100
    date_lowest = 0
    if not records:
        print("Records is NULL between date: %s and %s!" % (sdate, edate))
        return False
    if len(records) != 5:
        # 判断是否一周五天基金值是否完整，如果不要求完整的五天，可注释此条件
        print("Records is not 5 between date: %s and %s!" % (sdate, edate))
        return False
    for each in records:
        each_value = float(each["NetAssetValue"])
        if each_value < asset_value:
            asset_value = each_value
            date_lowest = each["Date"]
    year_low = int(date_lowest.split('-')[0])
    month_low = int(date_lowest.split('-')[1])
    day_low = int(date_lowest.split('-')[2]) 
    weekday_low = calendar.weekday(year_low, month_low, day_low)
    return weekday_low
        

def get_url(url, params=None, proxies=None):
    """
    获取url的返回值
    :param url:
    :param params:
    :param proxies:
    :return:url的返回值，此处为基金网站的数据
    """
    rsp = requests.get(url, params=params, proxies=proxies)
    rsp.raise_for_status()
    return rsp.text


def get_fund_data(code, start='', end=''):
    """
    获取基金在指定日期内的数据
    :param code: 基金代码
    :param start: 起始日期
    :param end: 结束日期
    :return: 基金在指定日期内的数据
    """
    record = {'Code': code}
    url = 'http://fund.eastmoney.com/f10/F10DataApi.aspx'
    params = {'type': 'lsjz', 'code': code, 'page': 1, 'per': 65535, 'sdate': start, 'edate': end}
    html = get_url(url, params)
    soup = BeautifulSoup(html, 'html.parser')
    records = []
    tab = soup.findAll('tbody')[0]
    for tr in tab.findAll('tr'):
        if tr.findAll('td') and len((tr.findAll('td'))) == 7:
            record['Date'] = str(tr.select('td:nth-of-type(1)')[0].getText().strip())
            record['NetAssetValue'] = str(tr.select('td:nth-of-type(2)')[0].getText().strip())
            record['ChangePercent'] = str(tr.select('td:nth-of-type(4)')[0].getText().strip())
            records.append(record.copy())
    return records


def get_year_low(code, year):
    """
    获取一年内所有周的净值最低日
    :param code: 基金代码
    :param year: 年份
    :return: 最低净值日list
    """
    low_list = []
    weeks_start_end = all_weeks(int(year))
    for each_week in weeks_start_end.values():
        s_date = each_week[0]
        sdate = s_date[0:4] + "-" + s_date[4:6] + "-" + s_date[6:8]
        e_date = each_week[1]
        edate = e_date[0:4] + "-" + e_date[4:6] + "-" + e_date[6:8]
        low_day = get_lowest(code, sdate, edate)
        low_list.append(low_day)
    return low_list


def get_low_perc(low_list):
    """
    获取最低值百分比
    :param low_list:周净值最低日列表
    :return:最低净值百分比
    """
    dict_day_count = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    dict_num_weekday = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五"}
    dict_weekday_percent = {"周一": 0, "周二": 0, "周三": 0, "周四": 0, "周五": 0}
    total_weeks = len(low_list)
    for each_low in low_list:
        if each_low in dict_day_count.keys():
            dict_day_count[each_low] = dict_day_count[each_low] + 1
    for key in dict_day_count.keys():
        weekday = dict_num_weekday[key]
        dict_weekday_percent[weekday] = dict_day_count[key] / total_weeks
    return dict_weekday_percent


def get_low_percent_years(code, syear, eyear):
    """
    获取基金在起始年份到结束年份内的周最低净值百分比
    :param code: 基金代码
    :param syear: 起始年份
    :param eyear: 结束年份
    :return:周最低净值百分比
    """
    low_list = []
    for each_year in range(syear, eyear + 1):
        low_list = low_list + get_year_low(code, each_year)
    return get_low_perc(low_list)


if __name__ == '__main__':
    """
    易方达：110011
    """
    args = parser.parse_args()
    code = args.code
    start_year = int(args.start_year)
    end_year = int(args.end_year)
    print(get_low_percent_years(code, start_year, end_year))
    



