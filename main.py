from asyncio import get_event_loop

from wallhaven import Wallhaven


async def main():
    base_url = 'https://wallhaven.cc/'
    print('选择要下载的类别: ')
    print('1. TopList')
    print('2. Latest')
    print('3. Random')
    i = int(input('请输入: '))
    url = None
    if i == 1:
        url = base_url + 'toplist'
    elif i == 2:
        url = base_url + 'latest'
    elif i == 3:
        url = base_url + 'random'
    else:
        print('无效的输入!【1，2，3】')
        exit(0)
    page_start = int(input('从第几页开始下载: '))
    page_end = int(input('下载到第几页(最大只能下载10页): '))
    if page_end > 10 or page_end < page_start or page_start < 1:
        print('输入参数错误!')
        exit(0)
    for i in range(page_start, page_end + 1):
        print('正在下载第' + str(i) + '页')
        final_url = url + '?page=' + str(i)
        wall = Wallhaven(final_url)
        await wall.get_images()
        await wall.download_images()


if __name__ == '__main__':
    try:
        get_event_loop().run_until_complete(main())
    finally:
        print('欢迎再次使用!')
