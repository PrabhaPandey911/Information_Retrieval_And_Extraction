import heapify
import json
import os
import sys
def process_indexes(path_to_index_folder,range_file_count,file_pointer,file_first_last_word_mapping):
	files = []
	#open all the files
	for r, d, f in os.walk(path_to_index_folder):
		for file in f:
			if '.txt' in file:
				fP = open(os.path.join(r, file),'r')
				files.append(fP)

	#make directory to store merged files if it already does not exist
	path_to_index_folder = os.path.join(path_to_index_folder,'../range_files')
	if os.path.exists(path_to_index_folder)==False:
		os.mkdir(path_to_index_folder)

	#build heap
	heap_tree = heapify.build_heap(path_to_index_folder)
	
	#push the first line of each file in the heap
	for f in range(0,len(files)):
		if files[f].closed==False:
			line = files[f].readline()
		else:
			files.remove(files[f])
			continue
		line = line[:-1]
		if len(line.strip())==0:
			files[f].close()
			continue
		lines = line.split("-",1)
		key = lines[0]
		value = lines[1]
		heap_tree.push_elements((key,value,files[f]))
	
	while heap_tree.heapinput!=0:
		file_name,range_file_count = heap_tree.pop_element(file_pointer,range_file_count,file_first_last_word_mapping)
		if file_name=="done":
			break
		file_pointer = ""
		for h in files:
			if h.name==file_name:
				file_pointer=h
		if file_pointer.closed==False:
			line = file_pointer.readline()
		else:
			files.remove(file_pointer)
			continue
		line = line[:-1]
		if len(line.strip())==0:
			file_pointer.close()
			continue
		lines = line.split("-",1)
		key = lines[0]
		value = lines[1]
		heap_tree.push_elements((key,value,file_pointer))
	
	if len(heap_tree.map_key_to_posting_list.keys())!=0:
		for key in heap_tree.map_key_to_posting_list.keys():
			if key!=heap_tree.recent_key:
				heap_tree.output_dictionary[key] = heap_tree.map_key_to_posting_list[key]
		heap_tree.output_dictionary = dict(sorted(heap_tree.output_dictionary.items()))
		first_word = list(heap_tree.output_dictionary.keys())[0]
		last_word = list(heap_tree.output_dictionary.keys())[-1]
		file_first_last_word_mapping[os.path.join(path_to_index_folder,'range_file_'+str(range_file_count)+'.txt')]=(first_word,last_word)
		print("making range_file_"+str(range_file_count))
		with open(os.path.join(path_to_index_folder,'range_file_'+str(range_file_count)+'.txt'), 'w+') as file:
			for i in heap_tree.output_dictionary.keys():
				file.write(json.dumps((i,heap_tree.output_dictionary[i])))
				file.write("\n")

	with open(os.path.join(path_to_index_folder,'file_first_last_word_mapping.txt'), 'w+') as file:
		for i in file_first_last_word_mapping.keys():
			file.write(json.dumps((i,file_first_last_word_mapping[i])))
			file.write("\n")
