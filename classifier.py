import nltk
# from pyltp import Segmentor,SentenceSplitter,Postagger
from pyltp import SentenceSplitter
import json,pickle

import jieba
import jieba.posseg as pseg

# 词性标注字典
# 各个词性的解释参考：https://blog.csdn.net/enter89/article/details/86009453?depth_1-utm_source=distribute.pc_relevant.none-task-blog-BlogCommendFromMachineLearnPai2-2&utm_source=distribute.pc_relevant.none-task-blog-BlogCommendFromMachineLearnPai2-2
# 该版本针对：LTP 词性标注
# pos_mapping = {
# 	'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,'j':10,
# 	'k':11,'m':12,'n':13,'nd':14,'nh':15,'ni':16,'nl':17,'ns':18,
# 	'nt':19,'nz':20,'o':21,'p':22,'q':23,'r':24,'u':25,'v':26,
# 	'wp':27,'ws':28,'x':29,'z':30,'%':31
# }

# 该版本针对 jieba 词性标注
# pos_mapping = {
# 	n 名词
# 　　　　nr 人名
# 　　　　ns 地名
# 　　　　nt 机构团体名
# 　　　　nz 其它专名	
# 	t
# 	s
# 	f
# 	v 动词
# 　　　　vd 副动词
# 　　　　vn 名动词
# 　　　　vshi 动词“是”
# 　　　　vyou 动词“有”
# 	a
# 	b 区别词
# 	r 代词
# 　　　　rr 人称代词
# 　　　　rz 指示代词
# 　　　　rzt 时间指示代词
# 　　　　rzs 处所指示代词
# 　　　　ry 疑问代词
# 　　　　ryt 时间疑问代词
# 　　　　rys 处所疑问代词
# 	m 数词
# 	mq 数量词
# 	q 量词
# 	p 介词
# 	c 连词
# }
# jieba 词性标注映射（用于构建特征向量）
pos_mapping = {
	'n':1,'nr':2,'ns':3,'nt':4,'nz':5,	't':6,'s':7,'f':8,\
	'v':9,'vd':10,'vn':11,'vshi':12,'vyou':13,'a':14,'b':15,\
	'r':16,'rr':17,'rz':18,'rzt':19,'rzs':20,'ry' :21,'ryt':22,\
	'rys':23,'m':24,'mq':25,'q':26,'p':27,'c':28
}

def read_data(path):
	with open(path,'r') as f:
		data = json.load(f)

		return data

# 过滤出合适的词性，扔掉不重要的词性
def filter_pos(cut):
	words,poses = [],[]
	for (w,v) in cut:
		if v in pos_mapping.keys():
			words.append(w)
			poses.append(v)
	return {'words':words,'poses':poses} 


# 由于在之前的两层过滤中，我们已经考虑过词的共现和其重要性。所以现在分类器重点在于句子
# 结构和句式。所以特征向量使用问句和候选句的词性序列，。问句给予 15 位词性位，答句给予 35 
# 位词性位。所以特征向量维数：50	。由于考虑了词性出现的顺序，所以特征向量维数比较高。。。（不会设计特征向量)
def get_feature(question,answer,label=None):
	sentences = SentenceSplitter.split(answer)
	if len(sentences) >= 2:														# 答案只要一句话
		answer = sentences[0]	

	question_cut = pseg.cut(question)
	answer_cut = pseg.cut(answer)
	question_pos = filter_pos(question_cut)
	answer_pos = filter_pos(answer_cut)

	# test 
	words ,pos_question = question_pos['words'],question_pos['poses']
	# n = len(words)
	# for i in range(n):
	# 	print("(%s/%s)" % (words[i],pos_question[i]),end=' ')
	# print()
	words ,pos_answer = answer_pos['words'],answer_pos['poses']
	# n = len(words)
	# for i in range(n):
	# 	print("(%s/%s)" % (words[i],pos_answer[i]),end=' ')
	# print()
	# print()
	# 

	vector_a = {}
	i = 0
	for pos in pos_answer:
		if i < 20: 
			vector_a[i] = pos_mapping[pos]											# 由于 features 是字典，无序，所以将字典 key 设为下标 i 表示该词性的位置
		else :
			vector_a[i] = 0
		i += 1

	vector_b = {}
	for pos in pos_question:
		if i < 45: 
			vector_b[i] = pos_mapping[pos]
		else :
			vector_b[i] = 0
		i += 1

	vector_union = {}
	vector_union.update(vector_a)
	vector_union.update(vector_b)

	if label is None:
		return (vector_union)
	else :
		return (vector_union,label)


def construct_data_set(feature_set,path):

	data = read_data(path)

	for id in data.keys():
		item = data[id]
		question = item['question']
		answer = item['answer']
		label = item['label']
		input_feature = get_feature(question,answer,label)						# ({'feature_name':f1,...},C)
		feature_set.append(input_feature)


def save_model(model_name,model):
	with open("model/"+ model_name + ".pickle","wb") as f:
		pickle.dump(model,f,protocol=pickle.HIGHEST_PROTOCOL)


def load_model(model_name):
	with open("model/"+ model_name + ".pickle","rb") as f:
		model = pickle.load(f)

		return model


def output_prediction_detial(question,answer,classifier,label=None):

	print("问题:",question)
	print("答案：",answer)
	print("正确答案：",label)
	print("模型预测：",classifier.classify(get_feature(question,answer)))
	print("概论分布：")
	probDist = classifier.prob_classify(get_feature(question,answer))
	samples = probDist.samples()
	for sample in samples:
		print(sample,probDist.prob(sample))
	print()


def start():

	train_features = []
	test_features = []
	path = "data/my_sample_train_set.json"
	# construct_data_set(train_features,path)
	path = "data/my_sample_validation_ann.json"
	# construct_data_set(test_features,path)

	# classifier = nltk.NaiveBayesClassifier.train(train_features)
	# save_model("NaiveBayesClassifier",classifier)

	# print("accuracy：", nltk.classify.accuracy(classifier, test_features))

	classifier = load_model("NaiveBayesClassifier")


	# test_data = read_data("data/my_sample_validation_ann.json")
	# for id in test_data.keys():
	# 	item = test_data[id]
	# 	output_prediction_detial(item['question'],item['answer'],classifier,item['label'])
	# 	break

	# 实际场景测试
	question = "牛奶保质期多久？"
	answers = ["请教一下连锁品牌加盟西式牛排在三明选哪个品牌好？","我问你牛奶保质期多久",'牛奶保质期能有多久啊','谁知道牛奶保质期多久','牛奶保质期一般为45天','别说这些没用的，东扯西扯的','一个月']

	for answer in answers:
		output_prediction_detial(question,answer,classifier)

	question = "汶川地震多少级？"
	answers = ['没人知道','谁知道汶川地震多少级啊','当年汶川大地震影响十分大','发生在汶川的地震对国家造成了极大损害','汶川大地震那年我7岁','汶川地震为8.0级大地震','8.0级','地瓜烤熟了真的很好吃，又便宜']
	for answer in answers:
		output_prediction_detial(question,answer,classifier)


if __name__ == '__main__':
	start()