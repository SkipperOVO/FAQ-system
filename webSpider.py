# coding = utf-8
#! python = 3.6

import bs4,re,requests
import urllib,time

question = "汶川地震多少级？"


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


#网页请求方法。根据给定 url 返回对应的网页 html 文本
def get_page_by_url(url):
	headers = {
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
		(KHTML, like Gecko) Chrome/69.0.3497.81 Safari/537.36'
	}
	response = requests.get(url,headers=headers)
	response.encoding = 'gbk'												# 注意 request 的中文编码问题
	if response.status_code == requests.codes.ok:
		return response.text
	else:
		return None


# 根据用户问题请求百度知道搜索结果页
def get_baiduzd_page(question):
	url_base = "https://zhidao.baidu.com/search?lm=0&rn=10&pn=0&fr=search&ie=gbk&word="
	url = url_base + urllib.parse.quote(question,encoding='gbk')			# 根据用户问题拼接请求 url

	return get_page_by_url(url)
	

# 根据特定的问题链接获得该问题的详情答案
def get_a_question_ans(url):
	html_text = get_page_by_url(url)
	if(html_text is None):
		print("爬取百度知道答案详情页面失败！")
		return None
	return get_ans_from_html(html_text)										# 返回该问题对应的答案集


# 根据用户输入句子爬取百度知道的答案。返回所有答案组成的列表
def get_baiduzd_answer(question):
	answers = []															# 返回值
	question_list_html = get_baiduzd_page(question)							# 返回百度知道搜索结果的第一页 html 文本
	if(question_list_html is None):
		print("爬取百度知道答案列表页面失败！")
		return None
	questions = get_sim_questions(question_list_html)						# questions 为 问题句子-链接 字典
	for question in questions:												# 遍历每个问题链接，获取该问题的前 5 个答案
		answers += get_a_question_ans(question['link'])
		time.sleep(1)														# 防止访问频率过高被百度禁 ip

	return answers


if __name__ == '__main__':
	answers = get_baiduzd_answer(question)
	print(''.join(answers))
