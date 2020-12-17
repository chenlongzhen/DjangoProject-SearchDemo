from django.shortcuts import render, HttpResponse, redirect
from django.db.models import Max, Min
from app01 import models
import json, csv, os
import jieba
from pypinyin import lazy_pinyin
from app01.CONSTANTS import *


def _black_search(quer, DB, bert_index_, fix_name):
    """
    黑名单搜索召回策略
    :param quer:
    :param DB:
    :param bert_index_:
    :param fix_name:
   return:
    """
    exact_values = []
    segs = jieba.cut_for_search(quer)
    for seg in segs:
        if len(seg) < 2:
            continue
        ret = DB.objects.filter(key__contains=seg)
        if ret:
            # 合并结果
            for res in ret:
                exact_values.append(res)

        return {'default_value': quer,
                f'exact_result_{fix_name}': exact_values[:5],
                f'fuzzy_result_{fix_name}': [],
                # f'merge_e_f_result': (exact_values + fuzzy_values)[:max_len],
                f'bert_result_{fix_name}': [],
                f'error_content_{fix_name}': ""
                }


def _search(request, DB, bert_index_, fix_name):
    max_len = 50

    error_content = ''
    quer = request.GET['q']
    if quer is None or quer == '':
        return render(request, 'search_cxbc.html')

    # 黑名单单独走策略
    if BLACKBOX.__eq__(fix_name):
        return _black_search(quer, DB, bert_index_, fix_name)

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
            # f'merge_e_f_result': (exact_values + fuzzy_values)[:max_len],
            f'bert_result_{fix_name}': bert_values[:max_len],
            f'error_content_{fix_name}': error_content
            }


def _merge_strategy(res_dict):
    '''
    结果合并：
        1.黑名单
        2. 精确匹配结果 + 模糊匹配结果
        3. 模型结果补充
        4. 取top 20 个
    '''
    #  搜索结果合并
    merge_result = []

    # black box
    black_exact_values = res_dict.get(f'exact_result_{BLACKBOX}')
    black_fuzzy_values = res_dict.get(f'fuzzy_result_{BLACKBOX}')

    # basic
    basic_exact_values = res_dict.get(f'exact_result_{BASIC}')
    basic_fuzzy_values = res_dict.get(f'fuzzy_result_{BASIC}')
    basic_model_values = res_dict.get(f'bert_result_{BASIC}')

    # activity
    activity_exact_values = res_dict.get(f'exact_result_{ACTIVITY}')
    activity_fuzzy_values = res_dict.get(f'fuzzy_result_{ACTIVITY}')
    activity_model_values = res_dict.get(f'bert_result_{ACTIVITY}')

    activity_result = []
    activity_result.extend(activity_exact_values)
    activity_result.extend(activity_fuzzy_values)
    activity_result.extend(activity_model_values)

    # search
    search_exact_values = res_dict.get(f'exact_result_{SEARCH}')
    search_fuzzy_values = res_dict.get(f'fuzzy_result_{SEARCH}')
    search_model_values = res_dict.get(f'bert_result_{SEARCH}')

    search_result = []
    search_result.extend(search_exact_values)
    search_result.extend(search_fuzzy_values)
    search_result.extend(search_model_values)
    search_result = search_result[:5]  # 取5个结果

    # 有黑名单就加黑名单 没有加 basic
    if len(black_exact_values) > 0:
        merge_result.extend(black_exact_values)
    elif len(black_fuzzy_values) > 0:
        merge_result.extend(black_fuzzy_values)
    elif len(basic_exact_values) > 0:
        merge_result.extend(basic_exact_values)
        merge_result.extend(basic_fuzzy_values)
        merge_result.extend(basic_model_values)

    # 去重
    dup_set = []
    merge_result_dup = []
    count = 0
    max_result = 20
    for res in merge_result:
        if count >= max_result:
            break
        if res.value not in dup_set:
            merge_result_dup.append(res)
            dup_set.append(res.value)
            count += 1

    # activity
    dup_set = []
    activity_result_dup = []
    count = 0
    max_result = 20
    for res in activity_result:
        if count >= max_result:
            break
        if res.value not in dup_set:
            activity_result_dup.append(res)
            dup_set.append(res.value)
            count += 1

    new_dict = {
        'merge_result_dup': merge_result_dup,
        'activity_result_dup': activity_result_dup,
        'merge_search_result': search_result
    }

    res_dict.update(new_dict)
    return res_dict
