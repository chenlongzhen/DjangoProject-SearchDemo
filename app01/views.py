from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, HttpResponse, redirect
from django.db.models import Max, Min
from app01 import models
import json, csv, os
from pypinyin import lazy_pinyin

from app01 import bert_index
from app01 import searchStrategy

from app01.CONSTANTS import *

os.makedirs('./data', exist_ok=True)

# Create your views here.
# https://www.cnblogs.com/petrolero/p/9909985.html
# https://www.cnblogs.com/lelezuimei/p/12199041.html


DB_DICT = {
    BASIC: models.SearchDB,
    ACTIVITY: models.ActivityDB,
    BLACKBOX: models.BlackBoxDB,
    SEARCH: models.Search2SearchDB
}

BERT_INDEX_DICT = {
    BASIC: bert_index.bert_index(BASIC),
    ACTIVITY: bert_index.bert_index(ACTIVITY),
    BLACKBOX: bert_index.bert_index(BLACKBOX),
    SEARCH: bert_index.bert_index(SEARCH)
}


def upload(request, mode):
    # 设置默认mode为basic
    mode = BASIC if mode not in DB_DICT.keys() else mode
    # 匹配DB
    DB = DB_DICT.get(mode, models.SearchDB)
    # 匹配bert index
    BERT_INDEX = BERT_INDEX_DICT.get(mode, bert_index.bert_index(BASIC))
    # 文件宽度
    # seg_len = 4 if mode == "activity" else 2
    seg_len = 2

    if request.method == 'POST':
        f = request.FILES.get('data_file')
        file_type = f.name.split('.')[1]
        if file_type not in ['csv']:
            return render(request, 'upload_basic.html', {'info': '导入失败 文件格式错误'})

        # upload 数据存入文件
        with open(BERT_INDEX.corpus_file_name, 'wb+') as destF:
            for Fread in f.chunks():
                destF.write(Fread)

        # 删除数据库
        DB.objects.all().delete()

        # 导入到数据库中
        bulk_list = []
        with open(BERT_INDEX.corpus_file_name, 'r') as readf:
            count = 1
            for line in readf:
                segs = line.strip().split(",")
                if len(segs) != seg_len:
                    print(f"error line: {line}")
                    continue

                key = segs[0]
                value = segs[1]
                if key == '' or value == '':
                    print(f"error line: {line}")
                    continue

                # 拼音转换
                key_pinyin = "".join(lazy_pinyin(key))

                # # 删除所有key=x的数据
                # ret = models.SearchDB.objects.filter(key=key)
                # if ret :
                #     ret.delete()

                # 将数据新增到数据库中
                # ret = models.SearchDB.objects.create(key=key, value=value)
                # bulk input
                temp_DB = DB(key=key, value=value, key_pinyin=key_pinyin)
                #                # 活动四个字段
                #                if mode == 'activity':
                #                    temp_DB = DB(key=key, value=value, key_pinyin=key_pinyin, st_dt=segs[2], ed_dt=segs[3])

                bulk_list.append(temp_DB)
                count += 1

            DB.objects.bulk_create(bulk_list)

        # show some cases data
        result = DB.objects.aggregate(Min('id'))
        max_id = result.get('id__min', 100)
        cases = DB.objects.filter(id__lte=max_id + 50)

        # bert 索引
        BERT_INDEX.bertBuild()

        return render(request, f'upload_{mode}.html', {'info': 'success', 'in_num': count, 'cases': cases})

    return render(request, f'upload_{mode}.html')


def db_list(request):
    # 逻辑
    # 获取所有的出版社的信息
    all_publishers = models.SearchDB.objects.all().order_by('id')  # 对象列表
    # for i in all_publishers:
    #     print(i)
    #     print(i.id)
    #     print(i.name)
    # 返回一个页面，页面中包含出版社的信息
    return render(request, 'publisher_list.html', {'all_publishers': all_publishers})


def db_add(request):
    if request.method == 'POST':
        # post请求
        # 获取用户提交的数据
        key = request.POST.get('key')
        value = request.POST.get('value')
        if key != '' and value != '':

            if models.SearchDB.objects.filter(key=key, value=value):
                # 数据库中有重复的名字
                return render(request, 'publisher_add.html', {'error': '出版社名称已存在'})

            # 将数据新增到数据库中
            ret = models.SearchDB.objects.create(key=key, value=value)
            print(ret, type(ret))

            # 返回一个重定向到展示出版社的页面
            return redirect('/list/')

        else:
            return render(request, 'publisher_add.html', {'error': '输入为空'})

        # get请求返回一个页面，页面中包含form表单
    return render(request, 'publisher_add.html')


def search(request):
    '''
    # auto completue
    :param request:
    :return:
    '''
    print(f"in search autocomplete")
    max_len = 20
    if request.method == 'GET' and 's' in request.GET:
        quer = request.GET['s']
        if quer == '' or quer is None:
            return HttpResponse(json.dumps([], ensure_ascii=False))

        results = models.SearchDB.objects.filter(
            key__icontains=quer)  # key字段
        # 文字 有包含结果
        if len(results) != 0:

            json_list = []
            for re in results:
                if re.key not in json_list:
                    json_list.append(re.key)  # key字段

            # print(f"auto: {json_list}")
            value = json_list[:min(max_len, len(json_list))]
            print(f"auto complete1: {value}")
            return HttpResponse(json.dumps(value, ensure_ascii=False))
        # 文字 无包含结果
        else:
            results = models.SearchDB.objects.filter(
                key_pinyin__icontains="".join(lazy_pinyin(quer)))  # key字段
            json_list = []
            for re in results:
                if re.key not in json_list:
                    json_list.append(re.key)  # key字段

            # print(f"auto: {json_list}")
            value = json_list[:min(max_len, len(json_list))]
            print(f"auto complete2: {value}")
            return HttpResponse(json.dumps(value, ensure_ascii=False))


# cxbc 主搜索
def search_cxbc(request):
    if request.method == 'GET' and 's' in request.GET:  # 没有haystack wooshs时候进入的是这里
        return search(request)

    if request.method == 'GET' and 'q' in request.GET:
        quer = request.GET['q']
        if quer is None or quer == '':
            return render(request, 'search_cxbc.html')

        res_dict_basic = searchStrategy._search(request,
                                                DB_DICT.get(BASIC),
                                                BERT_INDEX_DICT.get(BASIC),
                                                BASIC)

        res_dict_activity = searchStrategy._search(request,
                                                   DB_DICT.get(ACTIVITY),
                                                   BERT_INDEX_DICT.get(ACTIVITY),
                                                   ACTIVITY)

        res_dict_blackbox = searchStrategy._search(request,
                                                   DB_DICT.get(BLACKBOX),
                                                   BERT_INDEX_DICT.get(BLACKBOX),
                                                   BLACKBOX)

        res_dict_search = searchStrategy._search(request,
                                                   DB_DICT.get(SEARCH),
                                                   BERT_INDEX_DICT.get(SEARCH),
                                                   SEARCH)

        res_dict_basic.update(res_dict_activity)
        res_dict_basic.update(res_dict_blackbox)
        res_dict_basic.update(res_dict_search)

        # 策略合并
        res_dict_basic = searchStrategy._merge_strategy(res_dict_basic)

        return render(request, 'search_cxbc.html', res_dict_basic)

    # get
    ret = models.SearchDB.objects.first()

    return render(request, 'search_cxbc.html', {'default_value': ret.key})
