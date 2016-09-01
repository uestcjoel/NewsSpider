#!/usr/bin/env python
# -*- coding: utf-8  -*-

# A Powerful Spider(Web Crawler) System in python2.7
#Author:WangHui<997554953@qq.com>
#Created on 2016-08-23



import urllib2
from multiprocessing import Pool
import re
import time
import sys
import os
import ctypes
import chardet


#存放urlList.txt的文件路径列表
UrlListLoc = []

#存放解析结果的文件路径列表
SaveLocList = []

#url集合，会根据爬取网页中的超链接更新，其中的每个url生成一个爬取进程
UrlList = []

#爬取过的url集合，用于判断一个url是否已经被爬取
ReadedUrlList = []

#添加的url集合,用户可以在爬取过程中加入新的url
AddtionUrlList = []

#设置的时间的格式，用于保存页面的内容的文件名
ISOTIMEFORMAT='%Y-%m-%d %X'


#记录taskAttribute.txt文件中的内容,用于任务分级
taskAttList = []



#程序开始时间
StartTime = time.time ()


#获取脚本文件的当前路径
def GetCurFilePath():
     #获取脚本路径
     path = sys.path[0]
     #判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的文件，则返回的是编译后的文件路径
     if os.path.isdir(path):
         return path
     elif os.path.isfile(path):
         return os.path.dirname(path)


#存放当前执行程序的路径
CurrentPath = GetCurFilePath()


#导入解析动态链接库
parserPath = CurrentPath + "/parser.so"
pdll = ctypes.CDLL (parserPath)


#初始化taskAttList
def InitTaskAttList ():
	
	#读取设置任务的时间间隔
	taskAttributePath = CurrentPath + "/taskAttribute.txt"
	f = open (taskAttributePath, 'r')
	line = f.readline ()
	
	assert line == "Task Attribute:\n"

	#提取任务总数
	line = f.readline ()
	TaskNum = int (line [(len (line) - 2) : (len (line) - 1)])

	#断言所有给出的任务总数相等
	assert taskLocNum == TaskNum

	print "执行的任务总数： ",TaskNum
	print "\n"
	#初始化UrlList,ReadedUrlSet和AddtionUrlList
	for x in range (TaskNum):

		UrlList.append (set ())
		ReadedUrlList.append (set ())
		AddtionUrlList.append (set ())

	line = f.readline ()
	
	while line:

		taskAttList.append (line)
		line = f.readline ()

	f.close ()



#读取taskAttribute.txt中对应索引的任务的属性，获取其运行标示
def GetRunFlag (index):
	
	runFlagPath = UrlListLoc [index] + "/runFlag.txt"
	
	f = open (runFlagPath, 'r')
	line = f.readline ()
	assert line == "Run Flag:\n"
	
	flagLine = f.readline ()

	if flagLine == "0\n":
		runFlag = False 

	else:
		runFlag =True

	return runFlag



#初始化urlListLoc
def InitUrlListLoc (filePath):
	
	#读取的任务数
	taskLocNum = 0
	f = open (filePath, 'r')
	path = f.readline ()
	assert path == "Url List Location:\n"
	path = f.readline ()
	
	while path:
		realPath = path [0 : (len (path) - 1)]
		
		UrlListLoc.append (realPath)
		taskLocNum += 1
		path = f.readline ()

	f.close ()
	
	return taskLocNum


#初始化saveLocList
def InitSaveLocList (filePath):
	
	#存储的任务数
	taskSaveLocNum = 0
	f = open (filePath, 'r')
	path = f.readline ()
	assert path == "Save parse Pages Location:\n"
	path = f.readline ()
	
	while path:
		realPath = path [0 : (len (path) - 1)]
		
		SaveLocList.append (realPath)
		taskSaveLocNum += 1
		path = f.readline ()

	f.close ()	
	
	return taskSaveLocNum


#根据给定的url文件初始化url集合
def InitUrlList (index):
	
	urlLocation = UrlListLoc [index] + "/urlList.txt"
	
	with open (urlLocation, 'r') as f:
		line = f.readline ()
		while line:
			
			#去掉url中的换行符
			if line [(len (line) - 1) : len (line)] == "\n":
				line = line [0 : (len (line) - 1)]
			
			UrlList [index].add (line,)
			line = f.readline ()	
	f.close ()
	print urlLocation,"中包含的url数： ", len (UrlList [index])
	print "\n\n"

	

#爬取网页
def Get (realUrl):
	
	req = urllib2.Request (realUrl)
	
	#在http请求中添加头部，伪装成浏览器
	req.add_header('User-Agent', 'fake-client')  

	
	try:
		#设置访问超时时间
		response = urllib2.urlopen (req, timeout = 10)
	
	except Exception,e:
		print e
		return ""	
	else:
		try:
			html = response.read()
		except Exception, e:
			print e
			html = ""
		return html
		

#提取超链接
def ExtractHyperLinks (pageContent):
	
	linkList = re.findall ('"https?://news?.*?"', pageContent)
	return linkList



#获取用户添加的url文件中url的行数
def GetAddUrlNum (index):

	#print "检查用户添加的超链接"

	#默认addtionUrlList.txt文件与urlList.txt文件在同一个目录	
	addtionUrlPath = UrlListLoc [index] + "/addtionUrlList.txt"
	
	f = open (addtionUrlPath, 'r')
	addtionUrl = f.readline ()

	addtionUrlNum = 0

	while addtionUrl:

		addtionUrlNum += 1
		addtionUrl = f.readline ()
		
	f.close ()

	return addtionUrlNum



#更新用户添加的url
def UpdateAddLink (index):



	#根据读取的addtionUrlList.txt文件中的行数判断用户是否添加了新的url判断
	if GetAddUrlNum (index) >= len (AddtionUrlList [index]):
		#print "\n\n检测到用户添加的url..."
		
		addtionUrlPath = UrlListLoc [index] + "/addtionUrlList.txt"
		f = open (addtionUrlPath, 'r')
		addtionUrl = f.readline ()

		while addtionUrl:
			
			#去掉url后面的换行符
			if addtionUrl [(len (addtionUrl) - 1) : len (addtionUrl)] == "\n":
				
				addtionUrl = addtionUrl [0 : (len (addtionUrl) - 1)]

			#print "添加的url: ",addtionUrl

			#更新AddtionUrlList
			AddtionUrlList [index].add (addtionUrl)

			#更新UrlList
			UrlList [index].add (addtionUrl)
				
			addtionUrl = f.readline ()
			
		
		f.close ()

		

#更新UrlList
def UpdateUrlList (linkList, index):


	#检查用户添加的超链接，如有则更新
	UpdateAddLink (index)

	#更新提取到的网页中的超链接
	for link in linkList:
		
		UrlList [index].add (link)
	

				
#更新ReadedUrlList
def UpdateReadedUrl (url, index):
	ReadedUrlList [index].add (url)









#Spider Class
class PySpider:

	#初始化
	def __init__ (self, filePath, pageContent):
		
		self.__filePath = filePath
		self.__pageContent = pageContent


	#读取url对应的网页
	def GetPage (self, url):
		
		#获取real url，去除提取的超链接中的首尾双引号
		if url[0] == '"' and url [len (url)-1] == '"':
			
			realUrl = url [1:(len (url) - 1)]
			
		else:
			realUrl = url
		
		self.__pageContent = Get(realUrl)


	#获取当前爬取的网页内容
	def GetPageContent (self):
		
		return self.__pageContent
	



	def ParsePage (self, url, kcluser):


		if len (self.__pageContent) > 0:
			
			
			#获取网页编码方式
			encodingWay = chardet.detect (self.__pageContent) ['encoding']
			#print "当前网页的编码方式： ", encodingWay
	
			if encodingWay == 'GB2312' or encodingWay == 'GBK' or encodingWay == 'GB18030': 

				try:
					#包含的字符数 GB2312 < GbK < GB18030,因此全部解码成Gb18030
					decodePage= self.__pageContent.decode ('gb18030',"ignore")

						
					encodePage = decodePage.encode ('utf8')
					
					
					self.__pageContent = encodePage
						
	
				except Exception,e:
					print e
				

			pdll.parseWeb (self.__pageContent, url, kcluser, self.__filePath)
	
			

	#开始爬取网页
	def Start (self, url):
		
		self.GetPage (url)
		if len (self.__pageContent) != 0:
			self.ParsePage (url, 3)
		








#爬取进程核心，代表每一个爬取的进程，对应每一个任务
def CoreSpider (timeInterval, Index):
	

	InitUrlList (Index)
	#循环的周期，用于定时	
	cycleTimes = 0

	#用于更新定时的cycleTimes
	newCycleTimes = 0
	
	#定时标示,若其为True,则重新读取urlList.txt文件初始化UrlList，并重新爬取当前任务
	timingFlag = False
	
	#根据UrlSet循环爬取网页
		
	#while len (UrlList [Index]) != len (ReadedUrlList [Index]):
	while True:

		#迭代每一次的所有url对应的超链接列表
		ItHyperLinkList = []

		
		for globalUrl in UrlList [Index]:

			runFlag = GetRunFlag (Index)
	

			if runFlag == False:

				print "结束第",Index + 1,"个任务"

				return -1

			if globalUrl in ReadedUrlList [Index]:
				continue
			
			spider = PySpider (SaveLocList [Index], "")
			
			spider.Start (globalUrl)
			
			UpdateReadedUrl (globalUrl, Index)		
					
		
			pageContent = spider.GetPageContent ()
			
		
			HyperLinkList = ExtractHyperLinks (pageContent)
			
			for link in HyperLinkList:
					
				ItHyperLinkList.append (link)

			#获取当前系统时间
			CurrentTime = time.time ()
			
			newCycleTimes = (int(CurrentTime - StartTime )) / (int(timeInterval * 3600))
			
			if newCycleTimes - 1 >= cycleTimes:

				timingFlag = True
				cycleTimes = newCycleTimes
				break
	

		if timingFlag == False:
	
			UpdateUrlList (ItHyperLinkList, Index)
		
		else:
			#定时的核心
			print "\n\n\n"
			print "****************************************************"
			print "达到当前任务的时间间隔，重启该任务,请稍后...\n"
				
			#休眠5秒，方便用户观察重启当前任务的效果
			time.sleep (5)
			
			#删除当前UrlList中的所有元素
			UrlList [Index].clear ()
			
			#重新初始化
			InitUrlList (Index)

			timingFlag = False






#初始化urlListLoc和saveLocList
def InitListLoc ():

	taskLocPath = CurrentPath + "/urlListLoc.txt"
	taskLocNum = InitUrlListLoc (taskLocPath)

	taskSaveLocPath = CurrentPath + "/saveLocList.txt"
	taskSaveLocNum = InitSaveLocList (taskSaveLocPath)

	#断言读取的任务总数等于存储的任务总数
	assert taskLocNum == taskSaveLocNum
	
	return taskLocNum





#整个爬取进程，爬取多个任务
def FinalSpider ():

	InitTaskAttList ()
	#设置默认进程数,最好等于cpu核数
	p = Pool (processes = 100)

	IterIndex = 0

	if __name__=='__main__':

		#多进程爬取网页并解析，每个line对应一个task
		for line in taskAttList:
			
			#冒号的位置，用于找出任务间隔和任务运行标示
			splitFlag = ":"
			splitLocation = line.find (splitFlag)
			taskInterval = float (line [0 : splitLocation])
			assert len (line) - 2 == splitLocation + 1
			taskRunFlag = int (line [(splitLocation + 1) : (len (line) - 1)])
			assert isinstance (taskInterval, float)
			assert taskRunFlag == 1 or taskRunFlag == 0


			#跳过运行标示为0的任务

			if taskRunFlag == 1:

				print "间隔为",taskInterval,"h的爬取任务开始执行"
				print "请等待...\n"

				#开启单个进程
				p.apply_async (CoreSpider, (taskInterval, IterIndex))

	
			#给未开启的任务预留存储空间
			IterIndex = IterIndex + 1

	
	p.close ()
	p.join ()

		
		




#----------- 程序的入口处 -----------    
print u"""  
---------------------------------------  
   程序：FinalSpider.py  
   版本：1.0  
   作者：WangHui  
   日期：2016-08-23  
   语言：Python 2.7    
   功能：爬取并解析新闻 
---------------------------------------  
"""  



taskLocNum = InitListLoc ()

FinalSpider ()
	
print('等待所有子进程运行...')
print "所有任务完成..."
	


	

		
