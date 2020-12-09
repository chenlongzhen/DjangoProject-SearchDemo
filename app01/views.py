from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, HttpResponse, redirect
from django.db.models import Max,Min
from app01 import models
import json, csv, os

from app01 import bert_index

os.makedirs('./data', exist_ok=True)
corpus_file_name = './data/corpus.txt'
bert_index_ = bert_index.bert_index(corpus_file_name)


# Create your views here.
# https://www.cnblogs.com/petrolero/p/9909985.html
# https://www.cnblogs.com/lelezuimei/p/12199041.html
def upload(request):
    if request.method == 'POST':
        f = request.FILES.get('data_file')
        file_type = f.name.split('.')[1]
        if file_type not in ['csv']:
            return render(request, 'upload.html', {'info': '导入失败 文件格式错误'})

        # upload 数据存入文件
        with open(corpus_file_name, 'wb+') as destF:
            for Fread in f.chunks():
                destF.write(Fread)

        # 删除数据库
        models.SearchDB.objects.all().delete()

        # 导入到数据库中
        bulk_list = []
        with open(corpus_file_name, 'r') as readf:
            count = 1
            for line in readf:
                segs = line.strip().split(",")
                if len(segs) != 2:
                    print(f"error line: {line}")
                    continue

                key = segs[0]
                value = segs[1]
                if key == '' or value == '':
                    print(f"error line: {line}")
                    continue

                # # 删除所有key=x的数据
                # ret = models.SearchDB.objects.filter(key=key)
                # if ret :
                #     ret.delete()

                # 将数据新增到数据库中
                # ret = models.SearchDB.objects.create(key=key, value=value)
                # bulk input
                bulk_list.append(models.SearchDB(key=key,value=value))
                count += 1

            models.SearchDB.objects.bulk_create(bulk_list)

        # show some cases data
        result = models.SearchDB.objects.aggregate(Min('id'))
        max_id = result.get('id__min', 100)
        cases = models.SearchDB.objects.filter(id__lte=max_id+50)

        # bert 索引
        bert_index_.bertBuild()

        return render(request, 'upload.html', {'info': 'success', 'in_num': count, 'cases': cases})

    return render(request, 'upload.html')


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


# search autocomplete
def index(request):
    return render(request, "searchresult.html")


# auto completue
def search(request):
    print(f"in search autocomplete")
    max_len = 20
    if request.method == 'GET' and 's' in request.GET:
        quer = request.GET['s']
        if quer is not None:
            results = models.SearchDB.objects.filter(key__icontains=quer)  # key字段
            json_list = []
            for re in results:
                if re.key not in json_list:
                    json_list.append(re.key)  # key字段
            # print(f"auto: {json_list}")
            value = json_list[:min(max_len, len(json_list))]
            return HttpResponse(json.dumps(value, ensure_ascii=False))


# cxbc 主搜索
def search_cxbc(request):
    max_len = 50
    if request.method == 'GET' and 's' in request.GET:  # 这没搞明白， 没有haystack wooshs时候进入的是这里
        return search(request)

    if request.method == 'GET' and 'q' in request.GET:
        error_content = ''
        quer = request.GET['q']
        if quer is None:
            return render(request, 'search_cxbc.html')

        ret = models.SearchDB.objects.filter(key=quer)  # key字段
        #   1.完全匹配
        key_temp = []  # 去重
        exact_values = []  # 精确结果
        if ret:
            for res in ret:
                exact_values.append(res)
            key_temp.append(quer)
            # return render(request, 'search_cxbc.html', {'res_values': value, 'default_value': quer})

        # 2. 模糊匹配 使用contains
        results = models.SearchDB.objects.filter(key__icontains=quer)  # key字段
        results = list(set(results))

        ## 2.1 匹配每个只取前5个
        fuzzy_values = []  # 模糊结果
        for res in results:
            if res.key in key_temp:
                continue
            key_temp.append(res.key)
            values = models.SearchDB.objects.filter(key__icontains=res.key)  # key字段
            fuzzy_values.extend(values[:5])  # 取前5个value

        # 3 bert
        bert_values = []  # bert 结果
        sim_keys = bert_index_.bertQuery(quer)
        if sim_keys is not None:
            for sim_key in sim_keys:
                ret = models.SearchDB.objects.filter(key=sim_key)  # key字段
                bert_values.extend(ret[:5])
        else:
            error_content = 'bert模型数据未进行索引，请在upload页面上传相应类型数据！'

        # 合并结果
        # 截断
        return render(request, 'search_cxbc.html',
                      {'default_value': quer,
                       'exact_result': exact_values[:max_len],
                       'fuzzy_result': fuzzy_values[:max_len],
                       'merge_e_f_result': (exact_values + fuzzy_values)[:max_len],
                       'bert_result': bert_values[:max_len],
                       'error_content': error_content
                       })
    # get
    ret = models.SearchDB.objects.first()

    return render(request, 'search_cxbc.html', {'default_value': ret.key})
