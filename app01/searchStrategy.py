from django.shortcuts import render, HttpResponse, redirect
from django.db.models import Max, Min
from app01 import models
import json, csv, os
from pypinyin import lazy_pinyin


def _search(request, DB, bert_index_, fix_name):

    max_len = 50

    error_content = ''
    quer = request.GET['q']
    if quer is None or quer == '':
        return render(request, 'search_cxbc.html')

    ret = DB.objects.filter(key=quer)  # key字段
    #   1.完全匹配
    key_temp = []  # 去重
    exact_values = []  # 精确结果
    if ret:
        for res in ret:
            exact_values.append(res)
        key_temp.append(quer)
        # return render(request, 'search_cxbc.html', {'res_values': value, 'default_value': quer})

    # 2. 模糊匹配 使用contains
    results = DB.objects.filter(key__icontains=quer)  # key字段
    results = list(set(results))

    ## 2.1 匹配每个只取前5个
    fuzzy_values = []  # 模糊结果
    for res in results:
        if res.key in key_temp:
            continue
        key_temp.append(res.key)
        values = DB.objects.filter(key__icontains=res.key)  # key字段
        fuzzy_values.extend(values[:5])  # 取前5个value

    # 2.2 模糊匹配 使用拼音
    results = DB.objects.filter(
        key_pinyin__icontains="".join(lazy_pinyin(quer)))  # key字段

    results = list(set(results))
    for res in results:
        if res.key in key_temp:
            continue
        key_temp.append(res.key)
        values = DB.objects.filter(key__icontains=res.key)  # key字段
        fuzzy_values.extend(values[:5])  # 取前5个value

    # 3 bert
    ##  判断是否全是拼音，如果是就是用fuzzy的第一个结果返回bert
    # if quer.isalpha() and len(fuzzy_values)>0:
    #    quer = fuzzy_values[0].key

    bert_values = []  # bert 结果
    sim_keys = bert_index_.bertQuery(quer)
    if sim_keys is not None:
        for sim_key in sim_keys:
            ret = DB.objects.filter(key=sim_key)  # key字段
            bert_values.extend(ret[:5])
    else:
        error_content = 'bert模型数据未进行索引，请在upload页面上传相应类型数据！'

    # 合并结果
    return {'default_value': quer,
                   f'exact_result_{fix_name}': exact_values[:max_len],
                   f'fuzzy_result_{fix_name}': fuzzy_values[:max_len],
                   #f'merge_e_f_result': (exact_values + fuzzy_values)[:max_len],
                   f'bert_result_{fix_name}': bert_values[:max_len],
                   f'error_content_{fix_name}': error_content
                   }

