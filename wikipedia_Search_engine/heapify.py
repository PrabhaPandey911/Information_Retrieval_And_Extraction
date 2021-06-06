import heapq
import os
import json
import sys

class build_heap():
	def __init__(self,path_to_index_folder):
		self.path_to_index_folder = path_to_index_folder
		self.map_key_to_posting_list = {}
		self.output_dictionary = {}
		self.heapinput = []
		self.recent_key = ""

	def push_elements(self,element):
		if element[0] not in self.map_key_to_posting_list.keys():
			self.map_key_to_posting_list[element[0]] = element[1]
		else:
			self.map_key_to_posting_list[element[0]] += element[1]
		self.recent_key = element[0]
		
		heapq.heappush(self.heapinput,(element[0],element[2].name))

	def pop_element(self,file_pointer,range_file_count,file_first_last_word_mapping):
		if len(self.heapinput)==0:
			file_pointer="done"
			return file_pointer,range_file_count
		popped_element = heapq.heappop(self.heapinput)
		file_pointer = popped_element[1]
		if len(self.map_key_to_posting_list.keys())==10001:
			for key in self.map_key_to_posting_list.keys():
				if key!=self.recent_key:
					self.output_dictionary[key] = self.map_key_to_posting_list[key]

			temp_dictionary = {}
			for key in self.map_key_to_posting_list.keys():
				if key==self.recent_key:
					temp_dictionary[key]=self.map_key_to_posting_list[key]
			self.map_key_to_posting_list={}
			self.map_key_to_posting_list = temp_dictionary

			self.output_dictionary = dict(sorted(self.output_dictionary.items()))
			print("making range_file_"+str(range_file_count))
			first_word = list(self.output_dictionary.keys())[0]
			last_word = list(self.output_dictionary.keys())[-1]
			file_first_last_word_mapping[os.path.join(self.path_to_index_folder,'range_file_'+str(range_file_count)+'.txt')]=(first_word,last_word)
			with open(os.path.join(self.path_to_index_folder,'range_file_'+str(range_file_count)+'.txt'), 'w+') as file:
				for i in self.output_dictionary.keys():
					file.write(json.dumps((i,self.output_dictionary[i])))
					file.write("\n")
			self.output_dictionary={}
			range_file_count+=1
		return file_pointer,range_file_count