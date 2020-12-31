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
import os,re


class bert_index():

    def __init__(self, file_name, topk = 5, port = 4000, port_out = 4001):
        self.topk = topk
        self.corpus_file_name =  os.path.join('data', file_name+ "_corpus")
        self.annoy_file_name = os.path.join('data' ,file_name + "_annoy")
        self.id2que = None
        self.vec_len = 768 #任务重启时默认设置为768, 如果换长度了需要重复
        self.port = port
        self.port_out = port_out
        self.questions = None
        self.annoy_service = None

    def _build_annoy(self, vecs, annoy_file_name):
        '''

        '''
        print(f'build index... { self.corpus_file_name} {self.annoy_file_name}')
        # vec len
        f = len(vecs[0])
        self.vec_len = f
        print(f'vec len {len(vecs)}*{len(vecs[0])}')
        t = AnnoyIndex(f, 'angular')  # Length of item vector that will be indexed
        for i, vec in enumerate(vecs):
            t.add_item(i, vec)

        t.build(10)  # 10 trees
        t.save(annoy_file_name)
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
        print(f"load corpus: {self.corpus_file_name}")
        questions = []
        with open(self.corpus_file_name) as fp:
            for line in fp:
                #segs = line.strip().split("[SEP]",1)
                segs = re.split("\[SEP\]|;|\t", line.strip())
                if len(segs) != 2:
                    print(f"error line: {line}")
                    continue

                key = segs[0]
                value = segs[1].replace('[SEP]', ' ')
                if key == '' or value == '':
                    print(f"error line: {line}")
                    continue

                if key not in questions:
                    questions.append(key)

            print(f'some qs: {questions[:10]}')

            # id 2 que dict
            self.id2que = dict(zip(range(0, len(questions)), questions))
        self.questions = questions
        print(f"load corpus: {self.corpus_file_name} done!")

    def _BuilQuesEmbIndex(self):
        '''
        :return:
        '''
        print(f"_BuildQuesEmbIndex")
        with BertClient(ip='localhost', port=self.port, port_out=self.port_out) as bc:
            doc_vecs = bc.encode(self.questions)
        self._build_annoy(doc_vecs, self.annoy_file_name)
        print(f"_BuildQuesEmbIndex done")

    def bertBuild(self, only_annoy = True):
        '''

        :return:
        '''
        self._load()
        # 如果annoy文件已有加载已有的不用重新bert build
        if only_annoy:
            self._BuilQuesEmbIndex()

        # load to annoy
        self.annoy_service = AnnoyIndex(self.vec_len, 'angular')
        self.annoy_service.load(self.annoy_file_name)

    def bertQuery(self, question):
        '''

        :return:
        '''
        if self.annoy_service is None:
            if os.path.isfile(self.annoy_file_name):
                print(f"====annoy file exists loading...")
                self.bertBuild(False)
            else:
                print(f"====annoy file not exists building...")
                self.bertBuild()

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
