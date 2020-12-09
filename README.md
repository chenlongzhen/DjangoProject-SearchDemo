# django search basic demo 

## usage 

### evironment
python 3.6 tensorflow=1.10.0

```python
conda create -n py3 python=3.6
pip install -r requirements.txt
conda install annoy
conda install -c aaronzs tensorflow
pip install bert-serving-server  # server
pip install bert-serving-client  # client, independent of `bert-serving-server`
```

### start bert service
```python
conda activate py3
# bert server
echo "启动bertservice..."
nohup bert-serving-start -model_dir ./bert/chinese_L-12_H-768_A-12/ -num_worker=1 -port=4000 -port_out=4001 > bert_server.log &
tail  -f bert_server.log
```

### start web
```
conda activate py3
python manage.py makemigrations 
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```


##  upload search data
- data file should be in csv type, has two rows, key and value
- key is used to autocomplete
- value is used to get result by search key 

like this:

<img width="250" height="150" src="https://github.com/chenlongzhen/DjangoProject-SearchDemo/blob/master/readmepic/3.png"/>
upload website:
http://127.0.0.1:8000/upload/

---

## main page：

http://127.0.0.1:8000/search_cxbc

<img width="300" height="200" src="https://github.com/chenlongzhen/DjangoProject-SearchDemo/blob/master/readmepic/1.png"/>

<img width="300" height="200" src="https://github.com/chenlongzhen/DjangoProject-SearchDemo/blob/master/readmepic/2.png"/>
