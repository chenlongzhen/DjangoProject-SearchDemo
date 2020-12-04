from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, HttpResponse, redirect
from app01 import models
import json,csv

# Create your views here.
# https://www.cnblogs.com/petrolero/p/9909985.html
# https://www.cnblogs.com/lelezuimei/p/12199041.html
def upload(request):

    if request.method == 'POST':
        f = request.FILES.get('data_file')
        file_type = f.name.split('.')[1]
        if file_type not in ['csv']:
            return render(request, 'upload.html', {'info': '导入失败 文件格式错误'})

        with open('./tmp.csv', 'wb+') as destF:
            for Fread in f.chunks():
                destF.write(Fread)

        models.SearchDB.objects.all().delete()
        with open('./tmp.csv', 'r') as readf:
            count = 1
            for line in readf:
                print(f"line: {line}")
                segs = line.split(",")
                if len(segs) != 2:
                    continue
                key  = segs[0].strip()
                value = segs[1].strip()
               # # 删除所有key=x的数据
               # ret = models.SearchDB.objects.filter(key=key)
               # if ret :
               #     ret.delete()

                # 将数据新增到数据库中
                ret = models.SearchDB.objects.create(key=key, value=value)
                print(ret, type(ret))
                count += 1

        ret = models.SearchDB.objects.all()
        cases = ret[:min(30,len(ret))]

        return render(request, 'upload.html', {'info': 'success', 'in_num': count, 'cases':cases})

    return render(request, 'upload.html')


def publisher_list(request):
    # 逻辑
    # 获取所有的出版社的信息
    all_publishers = models.SearchDB.objects.all().order_by('id')  # 对象列表
    # for i in all_publishers:
    #     print(i)
    #     print(i.id)
    #     print(i.name)
    # 返回一个页面，页面中包含出版社的信息
    return render(request, 'publisher_list.html', {'all_publishers': all_publishers})


def publisher_add(request):
    if request.method == 'POST':
        # post请求
        # 获取用户提交的数据
        pub_name = request.POST.get('pub_name')
        if not pub_name:
            # 输入为空
            return render(request, 'publisher_add.html', {'error': '出版社名称不能为空'})

        if models.SearchDB.objects.filter(name=pub_name):
            # 数据库中有重复的名字
            return render(request, 'publisher_add.html', {'error': '出版社名称已存在'})

        # 将数据新增到数据库中
        ret = models.SearchDB.objects.create(name=pub_name)
        print(ret, type(ret))
        # 返回一个重定向到展示出版社的页面
        return redirect('/publisher_list/')

        # get请求返回一个页面，页面中包含form表单
    return render(request, 'publisher_add.html')

# search autocomplete
def index(request):
    return render(request, "searchresult.html")

# auto complete
def search(request):
    #print(f"in search auto")
    if request.method == 'GET' and 's' in request.GET:
        quer = request.GET['s']
        if quer is not None:
            results = models.SearchDB.objects.filter(key__icontains=quer) # key字段
            json_list = []
            for re in results:
                if re.key not in json_list:
                    json_list.append(re.key) # key字段
            #print(f"auto: {json_list}")
            return HttpResponse(json.dumps(json_list,ensure_ascii=False))

# cxbc 主搜索
def search_cxbc(request):

    if request.method == 'GET' and 's' in request.GET: # 这没搞明白，和haystack 的search页面不同他不能通过url指向到search函数
        return search(request)

    if request.method == 'GET' and 'q' in request.GET:
        quer = request.GET['q']
        res_values = []
        if quer is None:
            return render(request, 'search_cxbc.html')

        ret = models.SearchDB.objects.filter(key=quer)  # key字段

        #  完全匹配
        if ret:
            for res in ret:
                res_values.append(res)
            return render(request, 'search_cxbc.html', {'res_values': res_values, 'default_value': quer})

        else:
            # 无完全匹配时 使用contains
            results = models.SearchDB.objects.filter(key__icontains=quer)  # key字段
            json_list = []
            results = list(set(results))

            # contains 匹配每个只取前3个
            key_temp = [] # 去重
            for res in results:
                if res.key in key_temp:
                    continue
                key_temp.append(res.key)
                values = models.SearchDB.objects.filter(key__icontains=res.key)  # key字段
                res_values.extend(values[:3]) # 取前3个value

            return render(request, 'search_cxbc.html', {'res_values': res_values, 'default_value': quer})
    # get
    ret = models.SearchDB.objects.first()

    return render(request, 'search_cxbc.html', {'default_value': ret.key})
