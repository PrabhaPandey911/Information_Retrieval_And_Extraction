The project consists of 6 files:
	1)index.py
	2)heapify.py
	3)process_index.py
	4)search.py
	5)index.sh
	6)search.sh

index.sh is to be run as follows:
	bash index.sh <path_to_data_dump_file> <path_to_index_folder>

This would result in index files being created in <path_to_index_folder> and files having document ID to title mapping would be created in the same folder where index.sh is located.

heapify.py and process_index.py are to be used by index.py, which is being called from index.py

To fire query, run search.sh as follows:
	bash search.sh <path_to_index_folder>

search.sh and index.sh should be in the same folder.

when search.sh is run, user will be asked to query repeatedly until s/he terminates the program by ctrl+c.
