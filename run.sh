#!/usr/bin/env bash
#!/bin/bash

function env_check() {
  # 检查是否安装 python3
  if ! command -v python3 &> /dev/null
  then
      echo "python3 未安装"
      exit
  fi

  # 检查是否安装 pip
 if ! command -v pip &> /dev/null
  then
      echo "pip 未安装"
      exit
  fi

  # 检查是否安装 pyppeteer
  if ! pip list | grep pyppeteer &> /dev/null
  then
      echo "pyppeteer 未安装 请使用 pip install pyppeteer 安装"
      exit
  fi

  # 检查是否安装 bs4
  if ! pip list | grep bs4 &> /dev/null
  then
      echo "bs4 未安装 请使用 pip install bs4 安装"
      exit
  fi
}

function main() {
  env_check
  python main.py
}

main