#!/bin/bash

# 检查是否提供了访问令牌
if [ -z "$1" ]
then
    echo "请提供访问令牌作为参数"
    echo "用法: ./access_protected_route.sh YOUR_ACCESS_TOKEN"
    exit 1
fi

# 使用提供的访问令牌发送请求
curl -X GET "http://localhost:8000/protected-route" \
     -H "Authorization: Bearer $1"