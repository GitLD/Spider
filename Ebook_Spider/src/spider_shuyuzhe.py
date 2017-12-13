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
def getPageList(home_page):
    PageList = []
    html = requests.get(home_page)
    pattern = re.compile('&nbsp;&nbsp;<a href="https://book.shuyuzhe.com/catalogue/Pdf/(.*?)">末页</a>')
    page_num = int(re.findall(pattern,html.text)[0])
    for i in range(1,page_num+1):
        PageList.append('%s/%d' % (home_page,i))
    return PageList 

def getBookList(page_url):
    print('Get Book List on Page %s' % page_url.split('/')[-1])
    BookList = []
    html = requests.get(page_url)
    pattern = re.compile('<a href="(.*?)" title="Book.ShuYuZhe.com书语者_(.*?)" target="_blank">')
    BookList = re.findall(pattern,html.text)
    return BookList

def getDownloadUrl(book_url):
    html = requests.get(book_url)
    pattern = re.compile('<a href="(.*?)">下载此书</a>')
    download_url = re.findall(pattern,html.text)
    print(download_url)
    download_url = download_url[0]
    return download_url
    
def getDownloadUrls(book_url,book_name,download_urls):
    download_url = getDownloadUrl(book_url)
    download_urls.append((download_url,book_name))
    

def getPDF(download_url,book_name):
    path = './PDF/%s' % (book_name)
    print('Downloading %s ...'%book_name)
    if not os.path.exists(path): 
        html = requests.get(download_url)
        pdfContent = html.content
        with open(path,'wb') as f:
            f.write(pdfContent)
        
def main():
    filepath = './PDF'
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    try:
        num_of_threads = int(sys.argv[1])
    except:
        num_of_threads = 10
    _st = time.time()
    wm1 = WorkManager(num_of_threads)
    wm2 = WorkManager(num_of_threads)
    print(num_of_threads)
    # User Defined
    home_page = 'https://book.shuyuzhe.com/catalogue/Pdf'
    PageList = getPageList(home_page)
    download_urls = []
    for page_url in PageList:
        BookList = getBookList(page_url)
        for book_url,book_name in BookList:
            wm1.add_job(getDownloadUrls,book_url,book_name,download_urls)
    wm1.start()
    wm1.wait_for_complete()
    for download_url,book_name in download_urls:
        wm2.add_job(getPDF,download_url,book_name)
    print('Start Downloading Papers ...')
    wm2.start()
    wm2.wait_for_complete()
    print(time.time() - _st)

if __name__ == '__main__':
    main()
