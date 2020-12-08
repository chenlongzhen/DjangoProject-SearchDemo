#!/bin/env bash

ps -a | grep  "bert-serving-start"
echo "如果已经有相同服务启动请手动kill再重新启动"
sleep 3s
# bert server
echo "启动bertservice..."
nohup bert-serving-start -model_dir ./bert/chinese_L-12_H-768_A-12/ -num_worker=1 -port=4000 -port_out=4001 > bert_server.log &
tail  -f bert_server.log

