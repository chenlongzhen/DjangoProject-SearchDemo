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


class bert_index():

    def __init__(self, csvfile):
        self.csvfile = csvfile
        self.topk = 5
        self.annoy_file_name = 'annoy.index'
        self.id2que = None
        self.vec_len = None
        self.port = 4000
        self.port_out = 4001
        self.questions = None
        self.annoy_service = None

    def _build_annoy(self, vecs):
        '''
        '''
        print(f'build index...')
        # vec len
        f = len(vecs[0])
        self.vec_len = f
        print(f'vec len {len(vecs)}*{len(vecs[0])}')
        t = AnnoyIndex(f, 'angular')  # Length of item vector that will be indexed
        for i, vec in enumerate(vecs):
            t.add_item(i, vec)

        t.build(10)  # 10 trees
        t.save(self.annoy_file_name)
        print(f'build done!')
        return f

    def _getQueFromId(self, ids, id2que):
        '''
        '''
        que_list = []
        for i in ids:
            que_list.append(id2que[i])
        return que_list

    def _load(self):
        '''

        :return:
        '''
        print(f"load corpus: {self.csvfile}")
        with open(self.csvfile) as fp:
            questions = [line.strip().split(',')[0] for line in fp if line.strip() != '']
            print(f'some qs: {questions[:10]}')
            print(
                '%d questions loaded, avg. len of %d' % (len(questions), np.mean([len(d.split()) for d in questions])))

            # id 2 que dict
            self.id2que = dict(zip(range(0, len(questions)), questions))
        self.questions = questions
        print(f"load corpus: {self.csvfile} done!")

    def _BuilQuesEmbIndex(self):
        '''
        :return:
        '''
        print(f"_BuilQuesEmbIndex")
        with BertClient(ip='localhost', port=self.port, port_out=self.port_out) as bc:
            doc_vecs = bc.encode(self.questions)
        self._build_annoy(doc_vecs)
        print(f"_BuilQuesEmbIndex done")

    def bertBuild(self):
        '''

        :return:
        '''
        self._load()
        self._BuilQuesEmbIndex()

        # load to annoy
        self.annoy_service = AnnoyIndex(self.vec_len, 'angular')
        self.annoy_service.load(self.annoy_file_name)

    def bertQuery(self, question):
        '''

        :return:
        '''
        if self.annoy_service is None:
            # load annoy
            self.annoy_service = AnnoyIndex(self.vec_len, 'angular')
            self.annoy_service.load(self.annoy_file_name)

        with BertClient(ip='localhost', port=self.port, port_out=self.port_out) as bc:

            query_vec = bc.encode([question])[0]

            # get sim from annoy index
            top_Ids = self.annoy_service.get_nns_by_vector(query_vec, self.topk, search_k=-1, include_distances=False)

            # id 2 ques
            top_qus = self._getQueFromId(top_Ids, self.id2que)
            print('top %d questions similar to "%s"' % (self.topk, colored(question, 'green')))

            for idx, qus in zip(top_Ids, top_qus):
                print('> %s\t%s' % (colored(idx, 'cyan'), colored(qus, 'yellow')))
        return top_qus
