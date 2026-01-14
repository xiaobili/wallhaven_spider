# Wallhaven 爬虫

一个用于从 Wallhaven.cc 网站爬取壁纸的 Python 程序。

## 功能特性

- 按照 tag、toplist、random、latest 分类爬取数据
- 支持自定义爬取页码范围
- 自动识别壁纸扩展名
- 使用 rich 库美化输出界面
- 支持批量下载壁纸

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python wallhaven_spider.py
```

程序启动后会提示您选择爬取类别：
1. Tag (标签) - 按特定标签搜索壁纸
2. Toplist (排行榜) - 获取排行榜壁纸
3. Random (随机) - 获取随机壁纸
4. Latest (最新) - 获取最新上传的壁纸

选择类别后，程序会询问您要爬取的页面范围：
- 单页：爬取指定页码的所有壁纸
- 多页：爬取指定页码范围内的壁纸
- 所有页：爬取从起始页到结束页的所有壁纸

## 配置文件

程序使用 `config.json` 文件存储配置项，您可以根据需要修改：

- `download_dir`: 下载目录
- `delay_between_requests`: 请求间隔时间（秒）
- `max_pages_per_session`: 单次最大爬取页数
- `image_formats`: 支持的图片格式
- `max_retries`: 最大重试次数
- `timeout`: 请求超时时间（秒）

## 注意事项

- 请合理使用本程序，避免对目标网站造成过大压力
- 遵守 Wallhaven.cc 的使用条款和机器人协议
- 爬取的数据仅供个人学习使用，请遵守相关版权法规