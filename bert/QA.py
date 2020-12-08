#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author:clz 760590023@qq.com
# 使用annoy库进行的bert 相似召回
# bert 使用的是 bert as service
# 注意 py36 tf 1.10.0

import numpy as np
from bert_serving.client import BertClient
from termcolor import colored
from annoy import AnnoyIndex

prefix_q = '##### **Q:** '
topk = 5
file_name = 'corpus.txt'
annoy_file_name = 'annoy.index'

def build_annoy(vecs):
	'''
	'''
	print(f'build index...')
	# vec len
	f = len(vecs[0]) 
	print(f'vec len {len(vecs)}*{len(vecs[0])}')
	t = AnnoyIndex(f, 'angular')  # Length of item vector that will be indexed
	for i,vec in enumerate(vecs):
		t.add_item(i, vec)

	t.build(10) # 10 trees
	t.save(annoy_file_name)	
	print(f'build done!')
	return f

def getQueFromId(ids, id2que):
	'''
	'''
	que_list = []
	for i in ids:
		que_list.append(id2que[i])
	return que_list

with open(file_name) as fp:
	#questions = [v.replace(prefix_q, '').strip() for v in fp if v.strip() and v.startswith(prefix_q)]
	questions = [line.strip().split(',')[0] for line in fp]

	print(f'some qs: {questions[:10]}')
	print('%d questions loaded, avg. len of %d' % (len(questions), np.mean([len(d.split()) for d in questions])))

# id 2 que dict
id2que = dict(zip(range(0,len(questions)), questions))

with BertClient(port=4000, port_out=4001) as bc:
	doc_vecs = bc.encode(questions)
	# build annoy
	f = build_annoy(doc_vecs)
	# load annoy
	u = AnnoyIndex(f, 'angular')
	u.load(annoy_file_name)	

	while True:
		query = input(colored('your question: ', 'green'))
		query_vec = bc.encode([query])[0]

		# get sim from annoy index
		top_Ids = u.get_nns_by_vector(query_vec, topk, search_k=-1, include_distances=False)

		# id 2 ques
		top_qus = getQueFromId(top_Ids ,id2que)
		print('top %d questions similar to "%s"' % (topk, colored(query, 'green')))

		for idx,qus in zip(top_Ids, top_qus):
			print('> %s\t%s' % (colored(idx, 'cyan'), colored(qus, 'yellow')))
