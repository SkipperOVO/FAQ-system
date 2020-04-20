# coding = utf-8
# -!- coding: utf-8 -!-
#! python = 3.6

import bs4,re,requests
import urllib,time
from my_thread import MyThread
import traceback

question = "牛奶保质期多久"


# 根据用户问句从百度知道页面爬取相关问题搜索结果(question_list_html)返回 句子-链接 字典的列表
def get_sim_questions(html_text):
	similar_questions = []
	soup = bs4.BeautifulSoup(html_text,"lxml")
	for dt in soup.find_all(name='dt'):								# 所有的 dt
		question_text = dt.a.get_text()								# 获得具体的问句的文本
		question_link = dt.a['href']								# 句子对应的链接
		similar_questions.append({'sentence':question_text,'link':question_link})

	return similar_questions


# 根据问题详情页面的 html 文本获得该问题的前 5 个答案。
def get_ans_from_html(html_text):
	answers = []															# 返回的答案集
	ending_mark = ['。','！','？','；']										# 句子结尾标记
	soup = bs4.BeautifulSoup(html_text,'lxml')
	# 先将每个答案中的 “展开全部” 这四个干扰字去掉。暂时策略是搜索到所有的这个节点，然后替换成空来处理
	wgt_answer_mask = soup.find_all(name='div',attrs={'class':'wgt-answers-mask'})
	for answer_mask in wgt_answer_mask:
		answer_mask.div.replace_with('')
	# 去掉莫名其妙的东西
	qb_blur_dom = soup.find_all(name='span',attrs={'class':'qb-blur-dom'})
	for blur_dom in qb_blur_dom:
		blur_dom.replace_with("")

	# 特别处理
	wgt_best_mask = soup.find(name='div',attrs={'class':'wgt-best-mask'})
	wgt_best_mask.div.replace_with('')

	all_answers_div = soup.find_all(name='div',attrs={'accuse':'aContent'})	# 获取所有包含答案文本的 div 块
	for answer in all_answers_div:
		answer_text = answer.get_text().strip()[:500]						# 获得所有文本同时去掉前后空白并限制长度。
		if(answer_text[-1:] not in ending_mark):							# 如果结尾没有分句符，手动加句号，便于准确分句。
			answer_text += '。'
		answers.append("".join(answer_text.split()))						# join 和 split 是为了去除 \xa0 空白符								

	return answers

# 从本地代理服务器池获取可用代理服务器
def get_proxy():
	url = "http://127.0.0.1:5010/get"
	response = requests.get(url)
	host = eval(response.text)['proxy']										# 获得 ip 和 端口
	proxy = {}
	proxy['http'] = "http://" + host
	proxy['https'] = "https://" + host

	return proxy


#网页请求方法。根据给定 url 返回对应的网页 html 文本
def get_page_by_url(url):
	headers = {
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
		(KHTML, like Gecko) Chrome/69.0.3497.81 Safari/537.36',
		'Cookie': """PSTM=1537323233; MCITY=-268%3A; BIDUPSID=BF0DC73DEE6273AE85D13A0A16280412; BAIDUID=788CAC5630F5A348F8BAC4F7875A532A:FG=1; BDUSS=1uQVFxVTVxdm9yR0FXQ094RG1vVTJvMkJweDVLYUdZLTExMXBPV0p4NVpEN0plRUFBQUFBJCQAAAAAAAAAAAEAAABWvbOmx-vE-szu0LTTwzIwMDgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFmCil5ZgopeaW; BDRCVFR[feWj1Vr5u3D]=I67x6TjHwwYf0; delPer=0; PSINO=1; H_PS_PSSID=1465_31169_21127_31341_30901_30823_31085_26350_31164; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; shitong_key_id=2; ZD_ENTRY=bing; Hm_lvt_6859ce5aaf00fb00387e6434e4fcc925=1587048971,1587116973,1587116991,1587117281; Hm_lpvt_6859ce5aaf00fb00387e6434e4fcc925=1587117286; shitong_data=2416d7818af703566190fa328a03b6b28147281f085e78daa12c3fab7b67f427d2cfcee80fe4ecb39885aabdddb49b97173aecf0eacc7f77f12d6148d686a0b1367b350db5f3b3929702432e513184460dbe63e1eff62a6defe49bf77624aeaa6de2b1cdc0e1a22831876aac192d8fb1f06faf72997e1ea532c1facc0478271e; shitong_sign=c2f9b888"""
	}
	retry = 30 
	while retry > 0:
		proxy = get_proxy()
		try:
			response = requests.get(url,headers=headers,proxies=proxy,timeout=3.5)
			response.encoding = 'gbk'												# 注意 request 的中文编码问题
			if response.status_code == requests.codes.ok:
				return response.text
		# else:
		# 	retry -= 1
		except :
			# traceback.print_exc()
			matchObj = re.match(r'http://(.*):.*',proxy['http'])
			host = matchObj.group(1)
			del_url = "http://127.0.0.1:5010/delete?proxy=host:" + host 
			requests.get(del_url)													# 删除不可用代理服务器
			retry -= 1

	print("没有可用的代理服务器导致请求失败！")
	return None


# 根据用户问题请求百度知道搜索结果页
def get_baiduzd_page(question):
	url_base = "https://zhidao.baidu.com/search?lm=0&rn=10&pn=0&fr=search&ie=gbk&word="
	url = url_base + urllib.parse.quote(question,encoding='gbk')			# 根据用户问题拼接请求 url

	return get_page_by_url(url)
	

total_request = 0
total_failed = 0

# 根据特定的问题链接获得该问题的详情答案
def get_a_question_ans(url):
	global total_request
	global total_failed
	total_request += 1
	html_text = get_page_by_url(url)
	if(html_text is None):
		total_failed += 1
		print("爬取百度知道答案详情页面失败！")
		return None
	print("爬取成功！")
	return get_ans_from_html(html_text)										# 返回该问题对应的答案集


# 根据用户输入句子爬取百度知道的答案。返回所有答案组成的列表
def get_baiduzd_faq(question):
	answers = []															# 返回值
	question_list_html = None							# 返回百度知道搜索结果的第一页 html 文本
	while question_list_html is None:
		question_list_html = get_baiduzd_page(question)							# 返回百度知道搜索结果的第一页 html 文本

	if(question_list_html is None):
		print("爬取百度知道答案列表页面失败！")
		return None
	questions = get_sim_questions(question_list_html)						# questions 为 问题句子-链接 字典
	threadPool = []															# 线程队列
	for question in questions:												# 遍历每个问题链接，获取该问题的前 5 个答案
		thread = MyThread(get_a_question_ans,args=(question['link']))		# 多线程加速
		thread.start()
		threadPool.append(thread)

	for thread in threadPool:
		thread.join()

	for thread in threadPool:
		res = thread.get_result()
		if res is not None:
			answers += res

	return answers


if __name__ == '__main__':
	answers = get_baiduzd_faq(question)
	# answers += get_360_wenku(question)
	print("总请求数：" + str(total_request))
	print("总失败数：" + str(total_failed))
	print(''.join(answers))
