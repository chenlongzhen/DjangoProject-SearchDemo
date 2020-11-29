from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, HttpResponse, redirect
from app01 import models
import json

# Create your views here.
def publisher_list(request):
    # 逻辑
    # 获取所有的出版社的信息
    all_publishers = models.Publisher.objects.all().order_by('id')  # 对象列表
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

        if models.Publisher.objects.filter(name=pub_name):
            # 数据库中有重复的名字
            return render(request, 'publisher_add.html', {'error': '出版社名称已存在'})

        # 将数据新增到数据库中
        ret = models.Publisher.objects.create(name=pub_name)
        print(ret, type(ret))
        # 返回一个重定向到展示出版社的页面
        return redirect('/publisher_list/')

        # get请求返回一个页面，页面中包含form表单
    return render(request, 'publisher_add.html')

# search autocomplete
def index(request):
    return render(request, "searchresult.html")

def search(request):
    if request.method == 'GET' and 's' in request.GET:
        quer = request.GET['s']
        if quer is not None:
            results = models.Publisher.objects.filter(name__icontains=quer) #修
            json_list = []
            for re in results:
                json_list.append(re.name) # 字段
            print(f"auto: {json_list}")
            return HttpResponse(json.dumps(json_list,ensure_ascii=False))


