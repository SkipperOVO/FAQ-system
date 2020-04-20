#! python = 3.6
#! coding = utf-8

import OpenHowNet
from math import log,sqrt

class VSM :
	__sentences = []
	__idf = {}
	__tf = {}
	__hda = None

	def init(self,sentences,hda):

		self.__sentences = sentences;
		self.__hda = hda
		self.__caculate_idf()


	# 计算一个句子的 tf 字典
	# 注：tf 是和每个句子相关的，而不是整个文档。即一个句子有一个自己的 tf
	def caculate_tf(self,words):		

		tf = {}
		sen_len = len(words)
		for w in words:
			if w not in tf.keys():
				tf[w] = 1/sen_len										# 每次加 1/sen_len 而不是 1 是因为：直接在统计次数的同时把频率算出来省的在遍历一次
			else:
				tf[w] += 1/sen_len
		return tf;


	def get_idf(self,w):

		return self.__idf[w]


	# 计算 idf
	# 注：idf 是和整个文档库（句子集）相关的，所以一次计算整个文档库上的 idf
	def __caculate_idf(self):

		count_of_sentences = len(self.__sentences)

		wi_in_sentence = {}												# 某个词 wi 出现在的句子数（文档数）
		for sentence in self.__sentences:
			words = sentence['words']
			for word in set(words):										# 同一句话中的相同词不能被重复计算。我们要统计的是某一个句子中一个词在整个文档中出现的次数
				if word not in wi_in_sentence.keys():
					wi_in_sentence[word] = 1
				else:
					wi_in_sentence[word] += 1

		for (word,times) in wi_in_sentence.items():
			# test
			# print(word,' ',times)
			self.__idf[word] = log(count_of_sentences / times+1 )			# 计算每个词的 idf


	def get_sim(self,w1,w2):
		return self.__hda.calculate_word_similarity(w1,w2)


    # 利用同义词将两个句子的词序列统一成一致的。即 A 与 B 同义，那么两个词序列的 A(B) 全化成 B(A)
    # 注意在同一化词的时候，要确保原有词顺序不变，因为之后的计算要确保顺序。所以不能用 remove，append，而是 pop，insert
    # 虽然这会使得代码不好理解，但是也是没有办法的
	def __unified(self,words_1,words_2):
		replace_table = []												# 记录 words2 的替换情况
		len1,len2 = len(words_1),len(words_2)
		for id1 in range(len1):
			for id2 in range(len2):
				w1,w2 = words_1[id1],words_2[id2]
				if w2 in replace_table:									# w2 是被置换过的，所以不去考虑他，因为置换后本就是一个有误差的词，再去求同义词会导致误差更大.这种情况一般发生在 一个句子中本身就存在喝多同义词。
					continue
				if self.get_sim(w1,w2) >= 0.85:
					if w1 in self.__idf.keys():									# 同一化时一定要用语料库中存在的词来替换，不然其 tf 值为 0，就容易变成正交了
						words_2.pop(id2)
						words_2.insert(id2,w1)
						replace_table.append(w2)						# words2 移走了 w2 用 w1 代替
					else:
						words_1.pop(id1)
						words_1.insert(id1,w2)
		# test
		# for w in words_1:
		# 	print(w,end=' ')
		# print()
		# for w in words_2:
		# 	print(w,end=' ')
		# print()


	def __construct_vector(self,words_1,words_2):

		vec_1,vec_2 = [],[]
		self.__unified(words_1,words_2)								# 语义归一化
		tf1 = self.caculate_tf(words_1)
		tf2 = self.caculate_tf(words_2)
		union_words = list(set(words_1).union(set(words_2)))		# 两个词序列的并集
		count_of_sentences = len(self.__sentences)

		for w in union_words:
			if w in words_1:															# not in : 如果语料中无问句中的词，那么认为该词在语料中的频率为 0
				if w in self.__idf.keys():
					vec_1.append(tf1[w]*self.__idf[w])
				else:
					vec_1.append(tf1[w]*log(count_of_sentences))				# 如果语料库中没有 w 这个词，那么直接计算 idf[w] = log(文档数/(0+1))
			else:
				vec_1.append(0)

			if w in words_2:
				if w in self.__idf.keys():
					vec_2.append(tf2[w]*self.__idf[w])
				else:
					vec_2.append(tf2[w]*log(count_of_sentences))
			else:
				vec_2.append(0)

		# test
		# for item in self.__idf.items():
		# 	print(item,end=' ')
		# print()

		# for w in vec_1:
		# 	print(w,end=' ')
		# print()
		# for w in vec_2:
		# 	print(w,end=' ')
		# print()

		return vec_1,vec_2


 	# 计算两个特征向量的余弦值
	def __get_cosa(self,vec_1,vec_2):

		numerator,denominator1,denominator2 = 0,0,0				# 分子，分母，分母
		size = len(vec_1)
		for i in range(size):							# 注：两个向量的长度相同，长度都为二者的并集大小
			numerator += vec_1[i]*vec_2[i]
			denominator1 += vec_1[i]*vec_1[i]
			denominator2 += vec_2[i]*vec_2[i]
		denominator = sqrt(denominator1)*sqrt(denominator2)
		if denominator == 0:
			return 0
		cosa = (numerator)/(denominator)									

		return cosa


	# 计算 query_text 和 当前句子集中所有句子的相似度。
	def sim_of_all_sentence(self,query_words):

		words_1 = query_words
		for sentence in self.__sentences:
			words_2 = sentence['words']
			vec_1,vec_2 = self.__construct_vector(words_1,words_2)			# 构造两个句子的 TF-IDF 向量
			cosa = self.__get_cosa(vec_1,vec_2)
			sentence['score'] = cosa

		return self.__sentences

