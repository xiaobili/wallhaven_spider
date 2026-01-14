# Wallhaven 爬虫需求文档


## 需求
1. 按照 tag，toplist，random，latest 分类爬取数据
2. 要求爬取数据前询问要爬取第几页或前几页的内容或页面区间
3. 根据页面缩略图构建下载链接，要求识别壁纸扩展名（扩展名在#thumbs > section:nth-child(1) > ul > li:nth-child(17) > figure > div > span.png > span 位置附近可找到）
4. 使用rich库美化输出（ps： loading 动画，表格，色彩区分....)