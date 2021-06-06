import sys
import xml.sax
import re
import time
import nltk
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
import gc 
import json
import os
import heapify
import process_index

stop_words = set(stopwords.words('english'))
stop_words_dict = {}

range_file_count = 0
file_first_last_word_mapping = {}
file_first_last_doc_title_mapping = {}
file_pointer = ""
	
class Inverted_index_creation():
	def put_in_posting_list(self,inverted_index,key_word,doc_id,field):
		if key_word not in inverted_index.keys():
			inverted_index[key_word]={doc_id:{field:1,'a':1}}
		else:
			if doc_id not in inverted_index[key_word].keys():
				inverted_index[key_word][doc_id]={field:1,'a':1}
			elif field not in inverted_index[key_word][doc_id].keys():
				inverted_index[key_word][doc_id][field]=1
				inverted_index[key_word][doc_id]['a']+=1
			else:
				inverted_index[key_word][doc_id][field]+=1
				inverted_index[key_word][doc_id]['a']+=1
	
	def tokenize(self,text,inverted_index,pageNumber,feild):
		tokenizer = RegexpTokenizer(r'[a-zA-Z]+|(?<!\d)\d{1,4}(?!\d)')
		tokens = tokenizer.tokenize(text)
		tokens = [x for x in tokens if len(x)<200]
		tokens = [x for x in tokens if not x in stop_words]
		stemmer = SnowballStemmer('english')
		words = []
		for x in tokens:
			if x not in stop_words_dict.keys():
				stop_words_dict[x] = stemmer.stem(x)
			words.append(stop_words_dict[x])
		for w in words:
			self.put_in_posting_list(inverted_index,w,pageNumber,feild)
	
	def process_categories(self,text, pageNumber,inverted_index):
		regex_category = r"\[\[Category:(.*?)\]\]"
		category_regex = re.compile(regex_category)
		cat = category_regex.findall(text)
		category_list = []
		for c in cat:
			text = text.replace('[[Category:'+c+']]',' ')
			if '|' in c:
				category_list.append(c.split('|')[0])
			else:
				category_list.append(c)
		category_str = ' '.join(category_list)
		self.tokenize(category_str,inverted_index,pageNumber,'c')
		return text
		
			
	def process_links(self,text,pageNumber,inverted_index):
		ext_text  = text.replace("\n",'')
		links = ext_text.split('==External links==')[1]
		if len(links)!=0:
			text = text.replace(links,'')
			self.tokenize(links,inverted_index,pageNumber,'l')
			return text

			
	def process_body(self,text,pageNumber,inverted_index):
		if text==None:
			return text
		equal = re.findall('==(.*?)==',text)
		text1=""
		for x in equal:
			text = text.replace(x,'')

		# equal = re.findall('\{\{(.*?)\}\}',text)
		# for x in equal:
		# 	text = text.replace(x,' ')
		
		self.tokenize(text,inverted_index,pageNumber,'b')
		return text

				
	def process_ref(self,text,pageNumber,inverted_index):
		if '==References==' in text:
			ext_text  = text.replace("\n",'')
			links = ext_text.split('==References==')[1]
			if len(links)!=0:
				text = text.replace(links,'')
				self.tokenize(links,inverted_index,pageNumber,'r')
				
		ref_regex = re.compile('.*< ref (.*?)< /ref >.*',re.DOTALL)
		ref_tag = ref_regex.findall(text)
		ref_text = ""                       
		if len(ref_tag)!=0:
			for r in ref_tag:
				r = '< ref '+r+'< /ref >'
				text = text.replace(r,'')
				r =  r.split('< ref ')[1].split('< /ref >')[0]
				splits = r.split("|")
				useful_splits=[]
				append = useful_splits.append
				for s in splits:
					if '=' in s:
						s=s.split('=',1)[1]
					append(s)
				ref_string=' '.join(useful_splits) 
				ref_text+=ref_string
			self.tokenize(ref_text,inverted_index,pageNumber,'r') 
			return text
				
	def process_infobox(self,text,pageNumber,inverted_index):
		info_box=""
		infobox_start = re.compile('{{Infobox')
		start_index = re.search(infobox_start, text)
		
		if start_index:
			start = start_index.start()
			brackets = 2
			end=start+len('{{Infobox ')
			while(end<len(text)):
				if text[end]=='}':
					brackets-=1
				if text[end]=='{':
					brackets+=1
				if brackets==0:
					break
				end+=1
			if end+1 < len(text):
				info_box = text[start:end+1]
				text = text.replace(info_box,'')
				info_box = re.sub(r'<.*>',' ',info_box)
				info_box_split = info_box.split('\n')
				info_box_result=[]
				append = info_box_result.append
				for x in info_box_split:
					x = re.sub('|','',x)
					if '=' in x:
						x = x.split('=',1)[1]
					if len(x.strip())!=0:
						append(x)
				infobox_string=' '.join(info_box_result)
				self.tokenize(infobox_string,inverted_index,pageNumber,'i')
				return text
			
			

			
	def update_posting_list(self,inverted_index,pages,doc_id_plus_title):
		gc.disable()
		count=0
		for i in pages: 
			count+=1
			print("page no. ",count," being processed")
			#title
			title=i[1]
			doc_id_plus_title[i[0]]=title.strip()
			words = self.tokenize(title,inverted_index,i[0],'t')

			text=i[2]

			text= text.replace('#REDIRECT','')
			
			#category
			if text!=None:
				text=self.process_categories(text,i[0],inverted_index)


			#infobox    
			if text!=None:
				text=self.process_infobox(text,i[0],inverted_index)

			#links
			if text!=None:
				regex_link = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
				link_regex = re.compile(regex_link)
				links = link_regex.findall(text)     
				if len(links)!=0:
					text=re.sub(regex_link, '', text)
			   
				if '==External links==' in text:
					text=self.process_links(text,i[0],inverted_index)

			#ref
			if text!=None:
				text=self.process_ref(text,i[0],inverted_index)
			
			#body
			if text!=None:
				text = text.replace("\n",'')
				text=self.process_body(text,i[0],inverted_index)
			
		gc.enable()
		return inverted_index,doc_id_plus_title
	
	
class WikiHandler( xml.sax.ContentHandler ):
	def __init__(self,path_to_index_folder):
		self.CurrentData = ""
		self.title = ""
		self.id = 0
		self.text = []
		self.value = {}
		self.page=[]
		self.count_block = 1
		self.finaltext=""
		self.path_to_index_folder = path_to_index_folder
			  
   # Call when an element starts
	def startElement(self, tag, attributes):
		self.CurrentData = tag
		if tag == "page":
			self.id+=1
			title = self.title

   # Call when an elements ends
	def endElement(self, tag):
		if tag == "text":
			self.finaltext=' '.join(self.text)
			self.text=[]
		if tag == "page":
			self.value['title']=self.title
			self.value['text']=self.finaltext
			self.page.append((self.id,self.value['title'],self.value['text']))
			print("No. of pages: ",len(self.page))
			if len(self.page)==10000:
				dictionary = {}
				doc_id_plus_title = {}
				create_posting_list=Inverted_index_creation()
				dictionary,doc_id_plus_title=create_posting_list.update_posting_list(dictionary,self.page,doc_id_plus_title)
				self.page = []
				dictionary = dict(sorted(dictionary.items()))
				print("number of keys: ",len(dictionary.keys()))
				with open(os.path.join(self.path_to_index_folder,'posting_list'+str(self.count_block)+'.txt'), 'w+') as file:
					for i in dictionary.keys():
						key = i
						string=str(key)
						string+='-'
						for j in dictionary[i].keys():
							string+=str(j)
							string+='='
							for k in dictionary[i][j].keys():
								string+=str(k)
								string+='+'
								string+=str(dictionary[i][j][k])
								string+='/'
							string+=','
						file.write(string[:-1])
						file.write("\n")

				first_doc = list(doc_id_plus_title.keys())[0]
				last_doc = list(doc_id_plus_title.keys())[-1]
				file_first_last_doc_title_mapping['id_title'+str(self.count_block)+'.txt']=(first_doc,last_doc)
				with open('id_title'+str(self.count_block)+'.txt', 'w+') as file:
					for i in doc_id_plus_title.keys():
						file.write(str(i)+"-"+doc_id_plus_title[i])
						file.write("\n")

				self.count_block+=1

		self.CurrentData = ""

   # Call when a character is read
	def characters(self, content):
		if self.CurrentData == "title":
			self.title = content
		elif self.CurrentData == "redirect_title":
			self.redirect_title = content
		elif self.CurrentData == "text":
			self.text.append(content)
			

def create_index(path_to_data_dump, path_to_index_folder):
	'''Write your code here.'''
	# create an XMLReader
	parser = xml.sax.make_parser()
	# turn off namepsaces
	parser.setFeature(xml.sax.handler.feature_namespaces, 0)

	# override the default ContextHandler
	Handler = WikiHandler(path_to_index_folder)
	parser.setContentHandler( Handler )
   
	parser.parse(path_to_data_dump)
	if len(Handler.page)!=0:
		inverted_index={}
		gc.disable()
		doc_id_plus_title = {}

		create_posting_list=Inverted_index_creation()
		inverted_index,doc_id_plus_title=create_posting_list.update_posting_list(inverted_index,Handler.page,doc_id_plus_title)
					
		gc.enable()

		inverted_index = dict(sorted(inverted_index.items()))
		print("number of keys: ",len(inverted_index.keys()))
		with open(os.path.join(path_to_index_folder,'posting_list.txt'), 'w+') as file:
			for i in inverted_index.keys():
				key = i
				string=str(key)
				string+='-'
				for j in inverted_index[i].keys():
					string+=str(j)
					string+='='
					for k in inverted_index[i][j].keys():
						string+=str(k)
						string+='+'
						string+=str(inverted_index[i][j][k])
						string+='/'
					string+=','
				file.write(string[:-1])
				file.write('\n')

		first_doc = list(doc_id_plus_title.keys())[0]
		last_doc = list(doc_id_plus_title.keys())[-1]
		file_first_last_doc_title_mapping['id_title.txt']=(first_doc,last_doc)
		with open('id_title.txt', 'w+') as file:
			for i in doc_id_plus_title.keys():
				file.write(str(i)+"-"+doc_id_plus_title[i])
				file.write("\n")

		with open('file_first_last_doc_title_mapping.txt', 'w+') as file:
			for i in file_first_last_doc_title_mapping.keys():
				file.write(json.dumps((i,file_first_last_doc_title_mapping[i])))
				file.write("\n")

def main():
	path_to_data_dump = sys.argv[1]
	path_to_index_folder = sys.argv[2]
	start_time = time.time()
	# create_index(path_to_data_dump, path_to_index_folder)
	print("indices created")
	process_index.process_indexes(path_to_index_folder,range_file_count,file_pointer,file_first_last_word_mapping)
	print("---Time for index creation is %s seconds ---" % str((time.time() - start_time)))


if __name__ == '__main__':
	main()
