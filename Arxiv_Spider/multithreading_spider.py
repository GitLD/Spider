import queue as Queue
import sys
import requests
import os
import threading
import time
import re

class Worker(threading.Thread):  # 处理工作请求
  def __init__(self, workQueue, resultQueue, **kwds):
    threading.Thread.__init__(self, **kwds)
    self.setDaemon(True)
    self.workQueue = workQueue
    self.resultQueue = resultQueue


  def run(self):
    while 1:
      try:
        callable, args, kwds = self.workQueue.get(False)  # get task
        res = callable(*args, **kwds)
        self.resultQueue.put(res)  # put result
      except Queue.Empty:
        break

class WorkManager:  # 线程池管理,创建
  def __init__(self, num_of_workers=10):
    self.workQueue = Queue.Queue()  # 请求队列
    self.resultQueue = Queue.Queue()  # 输出结果的队列
    self.workers = []
    self._recruitThreads(num_of_workers)

  def _recruitThreads(self, num_of_workers):
    for i in range(num_of_workers):
      worker = Worker(self.workQueue, self.resultQueue)  # 创建工作线程
      self.workers.append(worker)  # 加入到线程队列


  def start(self):
    for w in self.workers:
      w.start()

  def wait_for_complete(self):
    while len(self.workers):
      worker = self.workers.pop()  # 从池中取出一个线程处理请求
      worker.join()
      if worker.isAlive() and not self.workQueue.empty():
        self.workers.append(worker)  # 重新加入线程池中
    print('All jobs were complete.')


  def add_job(self, callable, *args, **kwds):
    self.workQueue.put((callable, args, kwds))  # 向工作队列中加入请求

  def get_result(self, *args, **kwds):
    return self.resultQueue.get(*args, **kwds)

# User Defined
def getCSList(CS_homeUrl):
    print('Start Getting CSList ...')
    # 获取Computing Research Repository分类与Url，并返回字典
    html = requests.get(CS_homeUrl)
    pattern = re.compile('<li class="column.*?"><a href="(.*?)">(.*?)</a></li>')
    info = re.findall(pattern,html.text)
    url = [i[0] for i in info]
    field = [i[1] for i in info]
    CSList = dict(zip(field,url))
    print('Getting CSList Finished!')
    return CSList

def getCSpapers(CSList,home_Url):
    print('Start Getting CSPapers Url ...')
    filepath_list = []
    PageUrls = []
    for [field,url] in CSList.items():
        filepath = './CS/%s' % field
        if not os.path.exists(filepath):
            os.makedirs(filepath)
            
        html = requests.get(url)
        pat = re.compile('<a href=.*?fewer</a> |  <a href=.*?more</a> |  <a href="(.*?)">all</a>')
        url = re.findall(pat,html.text)[-1]
        if not url.startswith('http'):
            url = home_Url + url
        html = requests.get(url)
        
        pattern = re.compile('\[<a href="(.*?)" title="Download PDF">pdf</a>')
        pdfUrls = re.findall(pattern,html.text)
        for i in range(len(pdfUrls)):
            if not pdfUrls[i].startswith('http'):
                PageUrls.append(home_Url + pdfUrls[i])
            else:
                PageUrls.append(pdfUrls[i])
            filepath_list.append(filepath)
    print('Getting CSPapers Url Finished!')
    return [PageUrls,filepath_list]
    
def getPDF(pdfUrl,filePath):
    pdfName = '%s.pdf' % pdfUrl.split('/')[-1]
    path = '%s/%s' % (filePath,pdfName)
    if not os.path.exists(path): 
        html = requests.get(pdfUrl)
        pdfContent = html.content
        with open(path,'wb') as f:
            f.write(pdfContent)

def main():
  try:
    num_of_threads = int(sys.argv[1])
  except:
    num_of_threads = 10
  _st = time.time()
  wm = WorkManager(num_of_threads)
  print(num_of_threads)
  # User Defined
  home_Url = 'https://arxiv.org'
  CS_homeUrl = 'https://arxiv.org/corr/home'
  CSList = getCSList(CS_homeUrl)
  [PageUrls,filepath_list] = getCSpapers(CSList,home_Url)
  for (filePath,pdfUrl) in zip(filepath_list,PageUrls):
    wm.add_job(getPDF,pdfUrl,filePath)
  print('Start Downloading Papers ...')
  wm.start()
  wm.wait_for_complete()
  print(time.time() - _st)

if __name__ == '__main__':
  main()
