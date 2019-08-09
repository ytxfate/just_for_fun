#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import requests
import logging
from bs4 import BeautifulSoup
import time
import random
import re
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

"""
HTTP Live Streaming downloader
"""


class HlsDownloader:
    USER_AGENT_LIST = [
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E)',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E) QQBrowser/6.9.11079.201',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0)',
        'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; GTB7.0)',
        'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; InfoPath.3)',
        'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.41 Safari/535.1 QQBrowser/6.9.11079.201',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
        'Mozilla/5.0 (Windows; U; Windows NT 6.1; ) AppleWebKit/534.12 (KHTML, like Gecko) Maxthon/3.0 Safari/534.12',
        'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.33 Safari/534.3 SE 2.X MetaSr 1.0',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E)',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; Tablet PC 2.0; .NET4.0E)',
        'Opera/9.80 (Windows NT 6.1; U; zh-cn) Presto/2.9.168 Version/11.50'
    ]
    IP_PROXY_URL = "https://www.xicidaili.com/"
    TS_PATH = 'ts'

    def __init__(self):
        # 日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        # ip 代理
        self.list_ip_proxy = []

    def md5_convert(self, ts_str):
        """
        计算字符串md5值
        :param ts_str: 输入字符串
        :return: 字符串md5
        """
        if isinstance(ts_str, str):
            # 如果是unicode先转utf-8
            ts_str = ts_str.encode("utf-8")
        m = hashlib.md5()
        m.update(ts_str)
        return m.hexdigest()

    def get_proxy_page_html(self, name, url):
        """
        获取网页 HTML 代码
        """
        while 1:
            try:
                self.logger.info("(get_proxy_page_html)begin to get url (" + name + ") web html data...")
                headers = {'User-Agent': random.choice(self.USER_AGENT_LIST)}
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    self.logger.info("(get_proxy_page_html)get url (" + name + ") web html data ending.")
                    return resp.text
                elif resp.status_code == 503:
                    self.logger.error("(get_proxy_page_html)get url (" + name + ") web html error,restart after 60 second...")
                    time.sleep(63)
                else:
                    self.logger.error("(get_proxy_page_html)get url (" + name + ") web html error,restart after 10 second...")
                    time.sleep(13)
            except Exception as e:
                self.logger.error('(get_proxy_page_html)' + str(e))
                time.sleep(5)

    def get_user_input(self):
        while 1:
            url_str = input("please input HLS url ：\n")
            url_str = url_str.strip()
            if (url_str and url_str.startswith('http') and '.com' in url_str and url_str.endswith('m3u8')):
                self.logger.info("(get_user_input)user input is : " + url_str)
                return url_str

    def get_ip_proxy(self):
        self.list_ip_proxy = []
        proxy_html = self.get_proxy_page_html("IP 代理", self.IP_PROXY_URL)
        self.logger.info("(get_ip_proxy)begin to parse ip proxy html...")
        bs_obj = BeautifulSoup(proxy_html, 'lxml')
        table_obj = bs_obj.find("table", {"id": "ip_list"})
        tr_objs = table_obj.findAll("tr")
        i = 0   # 记录 tr 标签中 th 出现的次数
        for tr_obj in tr_objs:
            if tr_obj.find("th"):
                i += 1
                if i == 3:  # i=3时,高匿IP代理爬取完毕
                    break
            td_objs = tr_obj.findAll("td")
            if len(td_objs) == 0:
                continue
            else:
                ip_str = td_objs[5].get_text().lower() + "://" + td_objs[1].get_text() + ":" + td_objs[2].get_text()
                dict_tmp = {
                    td_objs[5].get_text().lower(): ip_str
                }
                self.list_ip_proxy.append(dict_tmp)
        self.logger.info("(get_ip_proxy)parse ip proxy html over!\n" + str(self.list_ip_proxy))

    def get_base_url(self, hls_url):
        regexp = re.compile(r'(.*\.com).*')
        re_match = re.match(regexp, hls_url)
        base_url = re_match.group(1)
        self.logger.info('(get_base_url)base url is : ' + base_url)
        return base_url

    def web_file_downloader(self, hls_url):
        hls_list = []
        while 1:
            try:
                self.logger.info("(web_file_downloader)begin to get url (" + hls_url + ") web data...")
                headers = {'User-Agent': random.choice(self.USER_AGENT_LIST)}
                proxy = random.choice(self.list_ip_proxy)
                resp = requests.get(hls_url, headers=headers, proxies=proxy)
                if resp.status_code == 200:
                    bodys = resp.content.decode(encoding="utf-8").split('\n')
                    hls_list = []
                    for b_str in bodys:
                        new_b_str = b_str.strip()
                        if new_b_str.startswith('#'):
                            pass
                        else:
                            if new_b_str:
                                hls_list.append(new_b_str)
                    self.logger.info("(web_file_downloader)get url (" + hls_url + ") web data ending.\n" + str(hls_list))
                    break
                else:
                    self.logger.error("(web_file_downloader)get url (" + hls_url + "),response code" + str(resp.status_code))
                    time.sleep(2)
            except Exception as e:
                self.logger.error('(web_file_downloader)' + str(e))
                time.sleep(2)
        return hls_list

    def ts_downloader(self, download_url, file_name):
        while 1:
            try:
                self.logger.info("(ts_downloader)begin to get url (" + download_url + ") web html data...")
                headers = {'User-Agent': random.choice(self.USER_AGENT_LIST)}
                proxy = random.choice(self.list_ip_proxy)
                resp = requests.get(
                    download_url, headers=headers, proxies=proxy)
                if resp.status_code == 200:
                    with open(file_name, 'wb') as f:
                        f.write(resp.content)
                    self.logger.info("(ts_downloader)get url (" + download_url + ") web data ending.")
                    break
                else:
                    time.sleep(3)
                    self.logger.error("(ts_downloader)get url (" + download_url + "),response code" + str(resp.status_code))
            except Exception as e:
                self.logger.error('(ts_downloader)' + str(e))
                time.sleep(3)

    def muti_thread_download(self, base_url, ts_list):
        pool = ThreadPoolExecutor()
        tasks = []
        for ts in ts_list:
            download_url = base_url + ts
            file_name = self.TS_PATH + '/' + self.md5_convert(ts)
            task = pool.submit(self.ts_downloader, download_url, file_name)
            tasks.append(task)
        # 主线程阻塞，直到满足设定的要求
        wait(tasks, return_when=ALL_COMPLETED)
        # for task in tasks:
        #     print(task.result())
        self.logger.info("====== files download over! ======")

    def build_up_files(self, ts_list):
        # out_file_name = str(int(time.time() * 1000)) + ''
        out_file_name = 'out'
        with open(out_file_name, 'wb') as f_out:
            for ts in ts_list:
                file_name = self.md5_convert(ts)
                with open(self.TS_PATH + '/' + file_name, 'rb') as f_read:
                    f_out.write(f_read.read())
        self.logger.info('====== build up over! ======')

    def main(self):
        # 获取用户输入
        hls_url = self.get_user_input()
        # url 解析到域名
        base_url = self.get_base_url(hls_url)
        # 获取 IP 代理
        self.get_ip_proxy()
        # 获取 hls 文件
        hls_list = self.web_file_downloader(hls_url)
        # 最后一个画质最高
        ts_list = self.web_file_downloader(base_url + hls_list[-1])
        # 判断路径是否存在
        if not os.path.isdir(self.TS_PATH):
            os.mkdir(self.TS_PATH)
        # 删除路径下的旧数据(也许有)
        for f_n in os.listdir(self.TS_PATH):
            os.remove(os.path.join(self.TS_PATH, f_n))
        # 多线程下载
        self.muti_thread_download(base_url, ts_list)
        # 组装
        self.build_up_files(ts_list)


if __name__ == '__main__':
    start = time.clock()
    HlsDownloader().main()
    end = time.clock()
    print(' ***** use time: ' + str(end - start) + ' seconds. ***** ')
