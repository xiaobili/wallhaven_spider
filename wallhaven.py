import os
from bs4 import BeautifulSoup
from requests import get


class Wallhaven:
    def __init__(self, page):
        self.page = page
        self.images = []
        self.html = None

    async def get_images(self, exist_path):
        await self.page.waitForSelector('.thumb-listing-page ul li figure img')
        html = await self.page.content()
        self.html = html
        soup = BeautifulSoup(html, 'html.parser')
        images = soup.select('.thumb-listing-page ul li figure')
        thumb_info = soup.select('.thumb-listing-page ul li figure .thumb-info')
        final_images = []
        wall_paper = os.listdir(exist_path)
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
            if ('wallhaven-' + split_url[-1]) not in wall_paper:
                final_images.append(pre_split_url[0] + '/full' + image_name)
        print('共有' + str(len(final_images)) + '张图片')
        self.images = final_images

    async def download_images(self):
        # 检测 images 文件夹是否存在
        if not os.path.exists('./images'):
            os.mkdir('./images')
        if len(self.images) == 0:
            print('没有图片可以下载!')
        else:
            for image in self.images:
                filename = image.split('/')[-1]
                r = get(image).content
                with open('./images/' + filename, 'wb') as f:
                    f.write(r)
                print('Downloaded: ' + filename)

    async def next_page(self, url):
        await self.page.goto(url)
