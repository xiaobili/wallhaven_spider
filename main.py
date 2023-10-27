from asyncio import get_event_loop
import pyppeteer
from wallhaven import Wallhaven


async def main():
    base_url = 'https://wallhaven.cc/search?topRange=1y&order=desc&sorting='
    browser = await pyppeteer.launch()
    page = await browser.newPage()
    await page.setViewport({'width': 1920, 'height': 1080})
    print('选择要下载的类别: ')
    print('1. TopList')
    print('2. Latest')
    print('3. Random')
    i = int(input('请输入: '))
    if i == 1:
        base_url = base_url + 'toplist'
        await page.goto(base_url)
    elif i == 2:
        base_url = base_url + 'latest'
        await page.goto(base_url)
    elif i == 3:
        base_url = base_url + 'random'
        await page.goto(base_url)
    else:
        print('无效的输入!【1，2，3】')
        exit(0)
    wall = Wallhaven(page)
    page_start = int(input('从第几页开始下载: '))
    page_end = int(input('下载到第几页(最大只能下载10页): '))
    wall_paper_path = '/Users/billy/Library/Mobile Documents/com~apple~CloudDocs/图片/壁纸'
    if page_end > 10 or page_end < page_start or page_start < 1:
        print('输入参数错误!')
        exit(0)
    for i in range(page_start, page_end + 1):
        print('正在下载第' + str(i) + '页')
        await wall.get_images(wall_paper_path)
        await wall.download_images()
        await wall.next_page(base_url + '&page=' + str(i + 1))
    await page.close()
    await browser.close()


if __name__ == '__main__':
    try:
        get_event_loop().run_until_complete(main())
    finally:
        print('欢迎再次使用!')
