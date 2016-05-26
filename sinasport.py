#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: hyzhangyong
# @Date:   2016-05-19 22:14:59
# @Last Modified by:   hyzhangyong
# @Last Modified time: 2016-05-26 13:37:32
from lxml.html import fromstring
import requests
import os
import re
from threading import Thread
import Queue,threading
import urllib2

#线程池
class Worker(Thread):
    worker_count=0
    timeout=1
    def __init__(self, workQueue,resultQueue,**kwds):
        Thread.__init__(self,**kwds)
        self.id=Worker.worker_count
        Worker.worker_count+=1
        self.setDaemon(True)
        self.workQueue=workQueue
        self.resultQueue=resultQueue
        self.start()

    def run(self):
    #the get-some-work,do-some-work main loop of worker threads
        while True:
            try:
                callable,args,kwds=self.workQueue.get(timeout=Worker.timeout)
                res=callable(*args,**kwds)
                self.resultQueue.put(res)
            except Queue.Empty:
                break
            except:
                pass


class WorkerManager:
    def __init__(self, num_of_workers=10,timeout=2):
        self.workQueue=Queue.Queue()
        self.resultQueue=Queue.Queue()
        self.workers=[]
        self.timeout=timeout
        self._recruitThreads(num_of_workers)

    def _recruitThreads(self,num_of_workers):
        for i in range(num_of_workers):
            worker=Worker(self.workQueue,self.resultQueue)
            self.workers.append(worker)

    def wait_for_complete(self):
        #then,wait for each of them to terminate
        while len(self.workers):
            worker=self.workers.pop()
            worker.join(10)
            if worker.isAlive() and not self.workQueue.empty():
                self.workers.append(worker)

    def add_job(self,callable,*args,**kwds):
        self.workQueue.put((callable,args,kwds))

    def get_result(self,*args,**kwds):
        return self.resultQueue.get(*args,**kwds)
# 创建文件夹
def mkdir(name,ospath=os.getcwd()):
    path=os.path.join(ospath,name)
    isExists=os.path.exists(path)
    if not isExists:
        print name.decode('utf-8').encode('gbk'),u'创建成功!'
        os.makedirs(path)
    else:
        print name.decode('utf-8').encode('gbk'),u'已存在!'
    return path

# 获取分类标题，分类子标题、链接
def get_classifytitle(html,class_):
    classifytitle=fromstring(html).xpath(('//section[@class="%s"]/h2[@class="tit01"]/a/text()') % class_)
    subtitles=fromstring(html).xpath('//section[@class="ppcs pfootballchina"]//ul//a/text()')
    subtitleurls=fromstring(html).xpath('//section[@class="ppcs pfootballchina"]//ul//a/@href')
    subtitles_urls=zip(subtitles,subtitleurls)
    return classifytitle,subtitles_urls

# 替换创建文件夹的非法字符
def title_replace(title):
    charmap={':':'：','?':'？','|':''}
    title=re.sub(r'[\:\?\|]',lambda x:charmap[x.group(0)],title)
    return title

# 新闻下载函数
def news_download(url,newTitle,newspath):
    html=requests.get(url).content
    newsContent=fromstring(html).xpath('//div[@class="blkContainerSblk"]/div/p/text()')
    imgs=fromstring(html).xpath('//div[@class="blkContainerSblk"]/div/div[@class="img_wrapper"]//img/@src')
    imgTitles=fromstring(html).xpath('//div[@class="blkContainerSblk"]/div/div[@class="img_wrapper"]//span/text()')
    imgs_imgTitleslist=zip(imgs,imgTitles)
    header={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }
    with open(os.path.join(newspath,newTitle+'.txt'), 'w') as f:
        f.write('\n'.join(newsContent))
    for img,imgTitle in imgs_imgTitleslist:
        local=os.path.join(newspath,imgTitle+'.jpg')
        request=urllib2.Request(img,headers=header)
        response=urllib2.urlopen(request)
        jpg=response.read()
        with open(local,'wb') as f:
                f.write(jpg)
# 线程调用
def run_start(classifytitle,subtitles_urls):
    path=mkdir(classifytitle[0])
    wm=WorkerManager(10)
    for subtitle,subtitleurl in subtitles_urls:
        subtitle=title_replace(subtitle)
        subtitlePath=mkdir(subtitle,path)
        wm.add_job(news_download,subtitleurl,subtitle,subtitlePath)
    wm.wait_for_complete()

# 爬虫主函数
def Spider(url):
    global classifytitle,subtitles_urls
    html=requests.get(url).content
    # 获取中国足球标签及新闻列表内容
    classifytitle,subtitles_urls=get_classifytitle(html,'ppcs pfootballchina')
    run_start(classifytitle,subtitles_urls)
    # 国际足球
    classifytitle,subtitles_urls=get_classifytitle(html,'ppcs pfootballglobal')
    run_start(classifytitle,subtitles_urls)
    # 获取NBA标签及新闻列表内容
    classifytitle,subtitles_urls=get_classifytitle(html,'ppcs pnba')
    run_start(classifytitle,subtitles_urls)
    # 获取综合体育标签及新闻列表内容
    classifytitle,subtitles_urls=get_classifytitle(html,'ppcs psportsother')
    run_start(classifytitle,subtitles_urls)

if __name__ == '__main__':
    url='http://sports.sina.com.cn/'
    Spider(url)
