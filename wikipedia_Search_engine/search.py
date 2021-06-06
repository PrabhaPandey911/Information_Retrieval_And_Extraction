import sys
import json
from itertools import islice
import operator
import os
import time
from bisect import bisect_left
import nltk
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords

stop_words = set(stopwords.words('english'))
stop_words_dict = {}

def take(n, iterable):
	return list(islice(iterable, n))

def BinarySearch(a, x): 
	i = bisect_left(a, x) 
	if i != len(a) and a[i] == x: 
		return i 
	else: 
		return -1

def tokenize(word):
	tokenizer = RegexpTokenizer(r'[a-zA-Z]+|(?<!\d)\d{1,4}(?!\d)')
	tokens = tokenizer.tokenize(word)
	tokens = [x for x in tokens if len(x)<200]
	tokens = [x for x in tokens if not x in stop_words]
	stemmer = SnowballStemmer('english')
	words = []
	for x in tokens:
		if x not in stop_words_dict.keys():
			stop_words_dict[x] = stemmer.stem(x)
		words.append(stop_words_dict[x])
	return words

def field_query_function(i,data,feild_query_list,feild_query_list_with_freq):
	splitted = i.split(":")

	#find field
	feild = splitted[0].strip()[0]

	#find query word
	word = tokenize(splitted[1].strip())
	if len(word) == 0:
		return

	i=word[0].strip()

	#find file to which that query word belongs to
	file_for_query = ""
	for d in data:
		first_word = d[1][0]
		last_word = d[1][1]
		if first_word <= i and i<=last_word:
			file_for_query = d[0]
			break

	#store the content of desired file
	file_content = []
	with open(file_for_query, 'r') as f:
		for line in f:
			file_content.append(json.loads(line))

	word_keys = [w[0] for w in file_content]#extract the word list of the file
	if i in word_keys:
		chota_list=[]
		chota_list_with_freq = []
		word_posting_list = next(post_list for (word, post_list) in file_content if word == i)
		posting_list_splitted = word_posting_list.split(',')
		doc_ids_post_list = [(p.split('=')[0],p.split('=')[1]) for p in posting_list_splitted]
		for did in doc_ids_post_list:
			feild_freq = {}
			fields = did[1].split('/')
			for el in fields:
				if el.split('+')[0] == feild:
					chota_list.append(did[0])
					chota_list_with_freq.append((did[0],el.split('+')[1]))
		feild_query_list.append(chota_list)
		chota_list_with_freq.sort(key = operator.itemgetter(1), reverse=True)
		feild_query_list_with_freq.append(chota_list_with_freq)


def field_query_processing(feild_query_list,feild_query_list_with_freq,docs_title):
	#feild_query_list is a list of lists which has list of documents for each feild query made
	#example: title:new body:york links:city
	#feild_query_list = [[doc_ids which had new in title],[doc_ids which had york in body],[doc_ids which had city in links]]
	#now we are supposed to take intersection of these lists and print the title corresponding to 
	#doc_id in intersected list.
	if len(feild_query_list)==0:
		return
	out_list = list(set.intersection(*map(set,feild_query_list)))
	out_list = take(10,out_list)
	if len(out_list)==0:
		out_list2 = list(set.union(*map(set,feild_query_list_with_freq)))
		out_list2.sort(key = operator.itemgetter(1), reverse=True)
		out_list2=list(set([i[0] for i in out_list2]))
		out_list = take(10,out_list2)
	for elem in out_list:
		doc_id_file = ""
		for d in docs_title:
			first_doc = d[1][0]
			last_doc = d[1][1]
			if first_doc <= int(elem) and int(elem)<=last_doc:
				doc_id_file = d[0]
				break

		with open(doc_id_file, 'r') as f:
			lines=f.readlines()
			doc_id_lines = []
			titles_lines = []
			for l in lines:
				doc_id_lines.append(int(l.split('-',1)[0].strip()))
				titles_lines.append(l.split('-',1)[1].strip())
			index = BinarySearch(doc_id_lines, int(elem))
			print(titles_lines[index])
	

def non_field_query_function(i,non_feild_query,data):
	if i[-1]=='\n':
		i = i[:-1]  
	x = tokenize(i)	
	if len(x)==0:
		return 
	i = x[0]

	#find the range_file which has query i
	file_for_query = ""
	for d in data:
		first_word = str(d[1][0])
		last_word = str(d[1][1])
		if first_word <= i and i<=last_word:
			file_for_query = d[0]
			break

	#store the content of desired file
	file_content = []
	with open(file_for_query, 'r') as f:
		for line in f:
			file_content.append(json.loads(line))

	word_keys = [w[0] for w in file_content]  #store all the words appeared in the file

	#if i appears in the word_keys   
	if i in word_keys:
		keys_list=[]

		#fetch out the posting list string from file_content for word i
		word_posting_list = next(post_list for (word, post_list) in file_content if word == i)

		#split the posting list by ',' to get content wrt each document that has the word i
		posting_list_splitted = word_posting_list.split(',')

		#make a list of doc_id and corressponding posting list 
		doc_ids_post_list = [(p.split('=')[0],p.split('=')[1]) for p in posting_list_splitted]

		#for each doc_id check of all ('a') frequency => as it is non-feild query
		for x in doc_ids_post_list:
			post_list1 = x[1].split('/')
			for e in post_list1:
				if e.split('+')[0] == 'a':
					keys_list.append((int(x[0]),int(e.split('+')[1])))

		#keys_list would have doc_id and absolute frequency of word i in that doc
		#reverse sort the keys_list according to the frequency, so that doc having highest freq of word i
		#stays at top of keys_list
		keys_list.sort(key = operator.itemgetter(1), reverse=True)

		#take the list of top 10 and append it to 
		non_feild_query.append(keys_list)

def handle_one_query_word_doc_list(non_feild_query,docs_title):
	non_feild_query.sort(key = operator.itemgetter(1), reverse=True)
	document_ids = [d[0] for d in non_feild_query]
	for doc_id in document_ids:
		file_for_title = ""
		for d in docs_title:
			first_doc = d[1][0]
			last_doc = d[1][1]
			if int(first_doc) <= int(doc_id) and int(doc_id) <= int(last_doc):
				file_for_title = d[0]
				break
		with open(file_for_title, 'r') as f:
			lines=f.readlines()
			doc_id_lines = []
			titles_lines = []
			for l in lines:
				doc_id_lines.append(int(l.split('-',1)[0].strip()))
				titles_lines.append(l.split('-',1)[1].strip())
			index = BinarySearch(doc_id_lines, doc_id)
			print(titles_lines[index])


def non_field_query_processing(non_feild_query,docs_title):
	if len(non_feild_query)==1:
		non_feild_query[0].sort(key = operator.itemgetter(1), reverse=True)
		listofTpls=take(10,non_feild_query[0])
		handle_one_query_word_doc_list(listofTpls,docs_title)
	else:
		result_list = {}
		for q in non_feild_query:
			for elem in q:
				if elem[0] not in result_list.keys():
					result_list[int(elem[0])]=int(elem[1])
				else:
					result_list[int(elem[0])]+=int(elem[1])

		listofTuples = sorted(result_list.items(), key=lambda x: x[1],reverse=True)
		handle_one_query_word_doc_list(take(10,listofTuples),docs_title)


def search(path_to_index_folder, query):
	'''Write your code here'''

	data = []
	location = os.path.join(path_to_index_folder,'../range_files')
	with open(os.path.join(location,'file_first_last_word_mapping.txt'), 'r') as f:
		for line in f:
			data.append(json.loads(line))

	docs_title = []
	with open('file_first_last_doc_title_mapping.txt','r') as f:
		for line in f:
			docs_title.append(json.loads(line))

	outputs=[]
	query = query.lower()
	original_query = query 
	if ':' in query:
		a = query.split()
		query=[]
		str = ""
		pref = ""

		for i in a:
			if ':' in i:
				 if i not in query:
				 	if len(i.split(':')[1].strip())!=0:
				 		query.append(i)
				 str = i
				 pref = str.split(':',1)[0]
			else:
				str=pref+':'+i
				query.append(str)
	else:
		query = query.split(" ")

	output_query=[]
	non_feild_query = []
	feild_query_list = []
	feild_query_list_with_freq = []
	for q in query:
		if ':' not in q:
			non_field_query_function(q,non_feild_query,data)
		else:
			field_query_function(q,data,feild_query_list,feild_query_list_with_freq)

	if ':' in original_query:
		field_query_processing(feild_query_list,feild_query_list_with_freq,docs_title)
	else:
		non_field_query_processing(non_feild_query,docs_title)


def main():
	path_to_index_folder = sys.argv[1]
	# query_file = sys.argv[2]

	try:
		while True:
			query = input("Enter your query (Ctrl+c to Terminate): ")
			if len(query)==0:
				continue
			print()
			start_time = time.time()
			search(path_to_index_folder, query)
			print("---Response Time = %s seconds ---" % str((time.time() - start_time)))
			print()
	except KeyboardInterrupt:
		print()
		print('Search Engine Terminated!')
		sys.exit(0)

if __name__ == '__main__':
	main()
