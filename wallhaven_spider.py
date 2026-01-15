"""
Wallhaven 爬虫程序
根据需求文档实现以下功能：
1. 按照 tag，toplist，random，latest 分类爬取数据
2. 爬取数据前询问要爬取第几页或前几页的内容或页面区间
3. 根据页面缩略图构建下载链接，识别壁纸扩展名
4. 使用rich库美化输出
"""

import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import os
import time
import json
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.prompt import Prompt, IntPrompt
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal


class WallhavenSpider:
    def __init__(self, config_file='config.json'):
        self.base_url = "https://wallhaven.cc"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.console = Console()
        self.load_config(config_file)
        # 初始化中断标志
        self.interrupted = False
        # 注册信号处理器
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """信号处理器，用于处理 Ctrl+C 中断"""
        self.interrupted = True
        raise KeyboardInterrupt("程序被用户中断")

    def load_config(self, config_file):
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.console.print(f"[yellow]配置文件 {config_file} 未找到，使用默认配置[/yellow]")
            self.config = {
                "download_dir": "downloads",
                "delay_between_requests": 1,
                "max_pages_per_session": 10,
                "image_formats": ["jpg", "jpeg", "png", "gif", "webp"],
                "max_retries": 3,
                "timeout": 30
            }
        except json.JSONDecodeError:
            self.console.print(f"[red]配置文件 {config_file} 格式错误，使用默认配置[/red]")
            self.config = {
                "download_dir": "downloads",
                "delay_between_requests": 1,
                "max_pages_per_session": 10,
                "image_formats": ["jpg", "jpeg", "png", "gif", "webp"],
                "max_retries": 3,
                "timeout": 30
            }

    def get_time_range_filter(self):
        """获取时间范围筛选参数"""
        print("\n请选择时间范围筛选:")
        print("1. 全部时间 (all time)")
        print("2. 最近一天 (1 day)")
        print("3. 最近三天 (3 days)")
        print("4. 最近一周 (1 week)")
        print("5. 最近一个月 (1 month)")
        print("6. 最近三个月 (3 months)")
        print("7. 最近半年 (6 months)")
        print("8. 最近一年 (1 year)")

        choice_str = Prompt.ask("请输入选择 (1-8)", choices=["1", "2", "3", "4", "5", "6", "7", "8"], default="1")
        choice = int(choice_str)

        time_ranges = {
            1: "all",
            2: "1d",
            3: "3d",
            4: "1w",
            5: "1M",
            6: "3M",
            7: "6M",
            8: "1y"
        }

        return time_ranges[choice]

    def get_resolution_filter(self):
        """获取分辨率筛选参数"""
        print("\n请选择分辨率筛选:")
        print("1. 自定义分辨率 (custom)")
        print("2. 1920x1080 (1080p)")
        print("3. 2560x1440 (1440p)")
        print("4. 3840x2160 (4K)")
        print("5. 5120x2880 (5K)")
        print("6. 7680x4320 (8K)")
        print("7. 不筛选 (no filter)")

        choice_str = Prompt.ask("请输入选择 (1-7)", choices=["1", "2", "3", "4", "5", "6", "7"], default="7")
        choice = int(choice_str)

        if choice == 1:
            # 自定义分辨率
            width = Prompt.ask("请输入宽度 (如: 1920)")
            height = Prompt.ask("请输入高度 (如: 1080)")
            return f"{width}x{height}"
        elif choice == 2:
            return "1920x1080"
        elif choice == 3:
            return "2560x1440"
        elif choice == 4:
            return "3840x2160"
        elif choice == 5:
            return "5120x2880"
        elif choice == 6:
            return "7680x4320"
        else:  # choice == 7
            return None

    def get_page_range(self):
        """询问用户要爬取的页面范围"""
        print("\n请选择页面范围:")
        print("1. 单页 (例如: 第1页)")
        print("2. 多页 (例如: 第1-5页)")

        choice_str = Prompt.ask("请输入选择 (1/2)", choices=["1", "2"], default="1")
        choice = int(choice_str)

        if choice == 1:
            while True:
                page_num_str = Prompt.ask("请输入要爬取的页码", default="1")
                try:
                    page_num = int(page_num_str)
                    if page_num > 0:
                        return [page_num]
                    else:
                        self.console.print("[red]页码必须是正整数，请重新输入[/red]")
                except ValueError:
                    self.console.print("[red]请输入有效的页码数字[/red]")
        elif choice == 2:
            while True:
                start_page_str = Prompt.ask("请输入起始页码", default="1")
                try:
                    start_page = int(start_page_str)
                    if start_page > 0:
                        break
                    else:
                        self.console.print("[red]页码必须是正整数，请重新输入[/red]")
                except ValueError:
                    self.console.print("[red]请输入有效的页码数字[/red]")

            while True:
                end_page_str = Prompt.ask("请输入结束页码", default="5")
                try:
                    end_page = int(end_page_str)
                    if end_page >= start_page:
                        break
                    else:
                        self.console.print("[red]结束页码不能小于起始页码，请重新输入[/red]")
                except ValueError:
                    self.console.print("[red]请输入有效的页码数字[/red]")

            return list(range(start_page, end_page + 1))

    def parse_wallpaper_extension(self, thumb_url):
        """从缩略图URL解析壁纸扩展名"""
        # 通常缩略图URL会包含扩展名信息，我们可以从中推断原始图片的格式
        # 在实际页面中，可以通过分析thumb元素附近的span标签来获取扩展名
        # 这里我们尝试从URL中提取或使用通用方法

        # 从缩略图URL解析扩展名
        parsed = urlparse(thumb_url)
        path_parts = parsed.path.split('.')
        if len(path_parts) > 1:
            ext = path_parts[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                return ext

        # 如果无法直接从URL获取，尝试访问缩略图页面获取更多信息
        # 这里简化处理，返回常见格式之一
        return 'jpg'

    def get_wallpapers_from_page(self, category, page_num, params=None):
        """从指定页面获取壁纸列表"""
        if params is None:
            params = {}

        if category == 'tag':
            url = f"{self.base_url}/search"
            params['q'] = params.get('tag', '')
            params['page'] = page_num
        elif category == 'toplist':
            url = f"{self.base_url}/toplist"
            params['page'] = page_num
        elif category == 'random':
            url = f"{self.base_url}/random"
            params['page'] = page_num
        elif category == 'latest':
            url = f"{self.base_url}/latest"
            params['page'] = page_num
        else:
            # 对于自定义搜索，使用search接口
            url = f"{self.base_url}/search"
            params['page'] = page_num

        try:
            # 使用配置中的超时值
            response = self.session.get(url, params=params, timeout=self.config['timeout'])
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            wallpapers = []
            # 根据实际HTML结构，壁纸缩略图在ul.thumb-listing-page下的li元素中
            list_items = soup.select('ul.thumb-listing-page li')

            # 如果上面的选择器没找到，尝试其他可能的选择器
            if not list_items:
                list_items = soup.select('ul.thumb-listing li')
            if not list_items:
                list_items = soup.select('li')

            for item in list_items:
                # 从缩略图中提取信息
                link_element = item.find('a')
                if link_element and link_element.get('href'):
                    wallpaper_url = link_element['href']

                    # 确保壁纸URL是完整URL
                    if wallpaper_url.startswith('/'):
                        wallpaper_url = urljoin(self.base_url, wallpaper_url)

                    # 重要：只处理wallhaven的壁纸链接，过滤掉其他链接
                    if '/w/' not in wallpaper_url or not wallpaper_url.startswith(('http://', 'https://')):
                        continue

                    # 从缩略图中获取图片URL
                    img_element = item.find('img')
                    thumb_url = ''
                    if img_element and img_element.get('data-src'):
                        thumb_url = img_element['data-src']
                    elif img_element and img_element.get('src'):
                        thumb_url = img_element['src']

                    # 从壁纸URL提取ID
                    wallpaper_id = self.extract_wallpaper_id_from_url(wallpaper_url)

                    # 尝试从缩略图的figure元素中查找扩展名信息
                    # 根据提供的信息，扩展名在 span 标签中，如 <span class="png">PNG</span>
                    figure_element = item.find('figure')
                    extension = 'jpg'  # 默认扩展名

                    if figure_element:
                        # 查找包含扩展名的span标签，如 <span class="png">PNG</span>
                        ext_spans = figure_element.find_all('span')
                        for span in ext_spans:
                            span_class = span.get('class', [])
                            span_text = span.get_text(strip=True).lower()

                            # 检查class属性是否包含常见的图片扩展名
                            for cls in span_class:
                                if cls.lower() in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                                    extension = cls.lower()
                                    break

                            # 如果class中没有找到，也可以检查文本内容
                            if extension == 'jpg':  # 如果还没找到扩展名
                                if span_text in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                                    extension = span_text

                    # 根据Wallhaven的URL模式构建下载链接
                    id_prefix = wallpaper_id[:2] if len(wallpaper_id) >= 2 else 'xx'
                    download_url = f"https://w.wallhaven.cc/full/{id_prefix}/wallhaven-{wallpaper_id}.{extension}"

                    # 尝试从缩略图旁边的信息中获取分辨率
                    resolution = 'Unknown'
                    # 查找可能包含分辨率信息的文本
                    for text_node in item.find_all(string=True):
                        res_match = re.search(r'(\d+)\s*x\s*(\d+)', str(text_node))
                        if res_match:
                            resolution = f"{res_match.group(1)} x {res_match.group(2)}"
                            break

                    wallpapers.append({
                        'id': wallpaper_id,
                        'url': wallpaper_url,
                        'thumb_url': thumb_url,
                        'download_url': download_url,
                        'extension': extension,
                        'resolution': resolution,
                        'size': 'Unknown'
                    })

            return wallpapers
        except Exception as e:
            self.console.print(f"[red]获取页面 {page_num} 的壁纸时出错: {str(e)}[/red]")
            return []

    def get_wallpaper_details(self, wallpaper_url):
        """获取壁纸详细信息，包括真实下载链接和扩展名"""
        try:
            # 添加延时以避免请求过于频繁
            time.sleep(max(1, self.config['delay_between_requests']))  # 使用配置中的延迟时间，至少1秒
            response = self.session.get(wallpaper_url, timeout=self.config['timeout'])
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 根据页面结构，查找壁纸图片的真实URL
            # 壁纸图片通常在<main>标签内的<img>标签中
            img_element = soup.select_one('main img[src*="wallhaven.cc"]')
            if not img_element:
                # 尝试其他可能的选择器
                img_element = soup.select_one('img#wallpaper')

            if img_element:
                # 获取图片的真实URL
                img_src = img_element.get('src') or img_element.get('data-src')
                if img_src:
                    # 确保URL是完整的
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    elif img_src.startswith('/'):
                        img_src = urljoin(self.base_url, img_src)

                    parsed = urlparse(img_src)
                    filename = os.path.basename(parsed.path)
                    wallpaper_id = filename.split('.')[0] if '.' in filename else self.extract_wallpaper_id_from_url(
                        wallpaper_url)

                    extension = self.parse_wallpaper_extension_from_filename(filename)

                    # 查找分辨率信息
                    resolution_elem = soup.select_one('h3')  # 分辨率通常在h3标签中
                    resolution = resolution_elem.get_text().strip() if resolution_elem else 'Unknown'

                    return {
                        'id': wallpaper_id,
                        'download_url': img_src,
                        'extension': extension,
                        'resolution': resolution
                    }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                self.console.print(f"[yellow]请求过于频繁，暂停一段时间: {wallpaper_url}[/yellow]")
                time.sleep(10)  # 如果被限制，则等待更长时间
            elif e.response.status_code in [403, 404]:
                self.console.print(f"[red]访问被拒绝或页面不存在: {wallpaper_url}[/red]")
            else:
                self.console.print(f"[red]获取壁纸详情时出错 {wallpaper_url}: {str(e)}[/red]")
        except requests.exceptions.RequestException as e:
            self.console.print(f"[red]网络请求错误 {wallpaper_url}: {str(e)}[/red]")
        except Exception as e:
            self.console.print(f"[red]获取壁纸详情时出错 {wallpaper_url}: {str(e)}[/red]")

        return None

    def parse_wallpaper_extension_from_filename(self, filename):
        """从文件名解析扩展名"""
        if '.' in filename:
            # 获取最后一个点之后的部分作为扩展名
            ext = filename.split('.')[-1].lower()
            # 检查扩展名是否为有效的图片格式
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']
            if ext in valid_extensions:
                return ext
            else:
                # 如果不是有效扩展名，尝试从URL中解析
                # 有时候URL路径中也包含扩展名信息
                return 'jpg'  # 默认返回jpg
        return 'jpg'  # 默认返回jpg

    def extract_wallpaper_id_from_url(self, url):
        """从壁纸URL中提取壁纸ID"""
        # 例如，从 https://wallhaven.cc/w/abc123 提取 abc123
        parts = url.rstrip('/').split('/')
        if len(parts) >= 2 and parts[-2] == 'w':
            return parts[-1]
        return 'unknown'

    def download_wallpaper(self, download_url, wallpaper_id, extension, category='misc', download_dir='downloads'):
        """下载单个壁纸"""
        try:
            # 创建分类子目录
            category_dir = os.path.join(download_dir, category)
            os.makedirs(category_dir, exist_ok=True)

            # 构建保存路径
            filepath = os.path.join(category_dir, f"wallhaven-{wallpaper_id}.{extension}")

            # 检查文件是否已存在
            if os.path.exists(filepath):
                self.console.print(f"[yellow]文件已存在，跳过: {filepath}[/yellow]")
                return True

            # 下载文件，使用配置的超时值
            response = self.session.get(download_url, stream=True, timeout=self.config['timeout'])
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    # 检查是否被中断
                    if hasattr(self, 'interrupted') and self.interrupted:
                        raise KeyboardInterrupt("下载被用户中断")

            self.console.print(f"[green]下载完成: {filepath}[/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]下载失败 {download_url}: {str(e)}[/red]")
            return False

    def crawl_by_category(self, category, tag=None):
        """按类别爬取壁纸"""
        self.console.print(f"[bold blue]开始爬取 {category} 类别壁纸...[/bold blue]")

        # 获取筛选参数
        time_range = self.get_time_range_filter()
        resolution = self.get_resolution_filter()

        # 准备参数
        params = {'tag': tag} if tag else {}
        
        # 添加时间范围和分辨率筛选参数
        if time_range != 'all':
            params['topRange'] = time_range
        if resolution:
            params['resolutions'] = resolution
            params['atleast'] = resolution  # 至少指定分辨率

        # 获取页面范围
        page_numbers = self.get_page_range()

        all_wallpapers = []

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:

            overall_task = progress.add_task(description="[cyan]总体进度...", total=len(page_numbers))

            for i, page_num in enumerate(page_numbers):
                progress.update(overall_task, description=f"[cyan]正在爬取第 {page_num} 页...")

                wallpapers = self.get_wallpapers_from_page(category, page_num, params)
                all_wallpapers.extend(wallpapers)

                progress.update(overall_task, advance=1)
                # 仅在页面请求之间延时，解析HTML不需要延时
                time.sleep(self.config['delay_between_requests'])  # 使用配置中的延迟时间

        # 显示结果
        self.display_results(all_wallpapers, category)

        # 询问是否下载
        if all_wallpapers:
            should_download = Prompt.ask("是否下载这些壁纸? (y/n)", default="n").lower()
            if should_download == 'y':
                self.download_wallpapers(all_wallpapers, category=category)

    def display_results(self, wallpapers, category):
        """使用Rich库显示结果表格"""
        table = Table(title=f"{category.upper()} 类别壁纸列表")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("分辨率", style="magenta")
        table.add_column("大小", style="green")
        table.add_column("扩展名", style="yellow")
        table.add_column("下载链接", style="blue", overflow="fold")

        for wp in wallpapers:
            table.add_row(
                wp['id'],
                wp['resolution'],
                wp['size'],
                wp['extension'],
                wp['download_url']
            )

        self.console.print(table)
        self.console.print(f"[bold green]共找到 {len(wallpapers)} 个壁纸[/bold green]")

    def download_wallpapers(self, wallpapers, category='misc'):
        """批量下载壁纸，使用多线程"""
        total = len(wallpapers)
        if total == 0:
            self.console.print("[yellow]没有壁纸需要下载[/yellow]")
            return
        
        # 从配置中获取最大线程数
        max_threads = min(self.config.get('max_threads', 5), total)
        
        # 统计成功和失败的数量
        success_count = 0
        failed_count = 0
        
        # 用于线程安全的锁
        counter_lock = threading.Lock()
        
        def download_single_wallpaper(wallpaper):
            nonlocal success_count, failed_count
            result = self.download_wallpaper(wallpaper['download_url'], wallpaper['id'], wallpaper['extension'], category=category, download_dir=self.config['download_dir'])
            
            with counter_lock:
                if result:
                    success_count += 1
                else:
                    failed_count += 1
            
            return result

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:

            download_task = progress.add_task(description="[cyan]开始下载...", total=total)
            
            # 使用线程池执行器进行多线程下载
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                # 提交所有下载任务
                future_to_wallpaper = {executor.submit(download_single_wallpaper, wp): wp for wp in wallpapers}
                
                # 监控下载进度
                for future in as_completed(future_to_wallpaper):
                    wallpaper = future_to_wallpaper[future]
                    progress.update(download_task, advance=1)
                    # 检查是否被中断
                    if self.interrupted:
                        executor.shutdown(wait=False, cancel_futures=True)
                        raise KeyboardInterrupt("下载被用户中断")
                    
        self.console.print(f"[bold green]下载完成! 成功: {success_count}, 失败: {failed_count}, 总计: {total}[/bold green]")

    def run(self):
        """运行爬虫"""
        self.console.print("[bold green]Wallhaven 爬虫程序启动![/bold green]")

        while True:
            try:
                print("\n请选择爬取类别:")
                print("1. Tag (标签)")
                print("2. Toplist (排行榜)")
                print("3. Random (随机)")
                print("4. Latest (最新)")
                print("5. 退出")

                choice = Prompt.ask("请输入选择 (1-5)", choices=['1', '2', '3', '4', '5'], default='5')

                if choice == '1':
                    tag = Prompt.ask("请输入标签名称")
                    self.crawl_by_category('tag', tag=tag)
                elif choice == '2':
                    self.crawl_by_category('toplist')
                elif choice == '3':
                    self.crawl_by_category('random')
                elif choice == '4':
                    self.crawl_by_category('latest')
                elif choice == '5':
                    self.console.print("[bold blue]感谢使用 Wallhaven 爬虫程序![/bold blue]")
                    break
                else:
                    self.console.print("[red]无效选择，请重新输入[/red]")
            except KeyboardInterrupt:
                self.console.print("\n[yellow]检测到中断信号，正在退出程序...[/yellow]")
                break


if __name__ == "__main__":
    try:
        # 配置文件位置在$WALLHAVEN_PATH/config.json
        config_file = os.environ.get('WALLHAVEN_PATH', '.') + '/config.json'
        spider = WallhavenSpider(config_file)
        spider.run()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序出现异常: {e}")