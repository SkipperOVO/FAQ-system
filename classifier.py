import nltk
from pyltp import Segmentor,SentenceSplitter,Postagger
import json,pickle

# 词性标注字典
# 各个词性的解释参考：https://blog.csdn.net/enter89/article/details/86009453?depth_1-utm_source=distribute.pc_relevant.none-task-blog-BlogCommendFromMachineLearnPai2-2&utm_source=distribute.pc_relevant.none-task-blog-BlogCommendFromMachineLearnPai2-2
pos_mapping = {
	'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,'j':10,
	'k':11,'m':12,'n':13,'nd':14,'nh':15,'ni':16,'nl':17,'ns':18,
	'nt':19,'nz':20,'o':21,'p':22,'q':23,'r':24,'u':25,'v':26,
	'wp':27,'ws':28,'x':29,'z':30,'%':31
}

cws_model_path = "/home/skipper/myApps/ltp/ltp_data_v3.4.0/cws.model"
pos_model_path = "/home/skipper/myApps/ltp/ltp_data_v3.4.0/pos.model"

segmentor = Segmentor();
postagger = Postagger()
segmentor.load(cws_model_path)
postagger.load(pos_model_path)

stop_words_path = "/media/skipper/DATA/1personal/NLP/project/data/stop_words_slim.txt"
stop_words_list = []

# 加载停用词文件,返回停用词列表
with open("data/stop_words.txt",'r') as file_obj:
	for line in file_obj:
		stop_words_list.append(line.rstrip())


def read_data(path):
	with open(path,'r') as f:
		data = json.load(f)

		return data

# 去除停用词
def del_stop_words(words):
	for word in stop_words_list:
		if word in words:
			words.remove(word)


# 由于在之前的两层过滤中，我们已经考虑过词的共现和其重要性。所以现在分类器重点在于句子
# 结构和句式。所以特征向量使用问句和候选句的词性序列，。问句给予 15 位词性位，答句给予 35 
# 位词性位。所以特征向量维数：50	。由于考虑了词性出现的顺序，所以特征向量维数比较高。。。（不会设计特征向量)
def get_feature(question,answer,label=None):
	sentences = SentenceSplitter.split(answer)
	if len(sentences) >= 2:														# 答案只要一句话
		return None
	answer_words = segmentor.segment(answer)
	del_stop_words(list(answer_words))
	question_words = segmentor.segment(question)
	del_stop_words(list(question_words))
	pos_answer = postagger.postag(answer_words)
	pos_question = postagger.postag(question_words)

	# # test
	# for (w,v) in zip(answer_words,pos_answer):
	# 	print("(" + w + "/" + v + ")",end=' ')
	# print()

	# for (w,v) in zip(question_words,pos_question):
	# 	print("(" + w + "/" + v + ")",end=' ')
	# print()
	# #

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
		if input_feature is None:
			continue
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
	answers = ["我问你牛奶保质期多久",'牛奶保质期能有多久啊','谁知道牛奶保质期多久','牛奶保质期一般为45天','别说这些没用的，东扯西扯的','一个月']

	for answer in answers:
		output_prediction_detial(question,answer,classifier)

if __name__ == '__main__':
	start()