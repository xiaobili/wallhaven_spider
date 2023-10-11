#!/usr/bin/env bash
#!/bin/bash

function env_check() {
  # 检查是否安装 python3
  if ! command -v python3 &> /dev/null
  then
      echo "python3 未安装"
      # 获取系统类型
      os_type=$(uname)
      if [ "$os_type" == "Darwin" ]
      then
        echo "正在安装 python3"
        brew install python3
      elif [ "$os_type" == "Linux" ]
      then
        echo "正在安装 python3"
        if [ -f "/etc/redhat-release" ]
        then
          yum install python3
        elif [ -f "/etc/lsb-release" ]
        then
          apt-get install python3
        fi
      else
        echo "暂不支持该系统"
        exit 1
      fi



  # 检查是否安装 pyppeteer
  elif ! pip list | grep pyppeteer &> /dev/null
  then
      echo "pyppeteer 未安装 正在安装中"
      pip3 install pyppeteer


  # 检查是否安装 bs4
  elif ! pip list | grep bs4 &> /dev/null
  then
      echo "bs4 未安装 正在安装中"
      pip3 install bs4
  fi
}

function main() {
  env_check
  python3 main.py
}

main