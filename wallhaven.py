import os

import pyppeteer
from bs4 import BeautifulSoup
from requests import get


class Wallhaven:
    def __init__(self, url):
        self.url = url
        self.browser = None
        self.page = None
        self.images = []

    async def init(self):
        self.browser = await pyppeteer.launch()
        self.page = await self.browser.newPage()
        await self.page.goto(self.url)

    async def get_images(self):
        await self.init()
        await self.page.waitForSelector('.thumb-listing-page ul li figure img')
        for i in range(1, 10):
            await self.page.evaluate(pageFunction='window.scrollTo(0, 1000)')
        html = await self.page.content()
        soup = BeautifulSoup(html, 'html.parser')
        images = soup.select('.thumb-listing-page ul li figure')
        thumb_info = soup.select('.thumb-listing-page ul li figure .thumb-info')
        final_images = []
        for image in images:
            is_png = image.select('.thumb-info .png')
            if is_png:
                img_url = image.select_one('img')['data-src'].replace('//th', '//w').replace('/small/',
                                                                                             '/full/').replace(
                    '.jpg', '.png')
            else:
                img_url = image.select_one('img')['data-src'].replace('//th', '//w').replace('/small/', '/full/')
            split_url = img_url.split('/')
            pre_split_url = img_url.split('/full/')
            image_name = '/' + split_url[-2] + '/wallhaven-' + split_url[-1]
            final_images.append(pre_split_url[0] + '/full' + image_name)
        await self.page.close()
        print('共有' + str(len(final_images)) + '张图片')
        self.images = final_images

    async def download_images(self):
        # 检测 images 文件夹是否存在
        if not os.path.exists('./images'):
            os.mkdir('./images')

        for image in self.images:
            filename = image.split('/')[-1]
            r = get(image).content
            with open('./images/' + filename, 'wb') as f:
                f.write(r)
            print('Downloaded: ' + filename)
        await self.browser.close()
