from pathlib import Path
import requests
import re
from bs4 import BeautifulSoup
from typing import List


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/68.0.3440.106 Safari/537.36 '
}
TIMEOUT = 8
MAX_CACHE_COUNT = 10

cache_html = {}


def get_html(url: str) -> str:
    """
    获取指定的网址的 html 文档。
    会缓存最近的 10 个（默认），便于加速下次访问
    """
    # 虽然没有必要，但是为了避免歧义，还是引入全局变量
    global cache_html
    # 如果之前已经获取过对应的 html，则直接返回
    if url in cache_html and cache_html[url]:
        return cache_html[url]
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    # 成功获取 html
    if r.status_code == 200:
        html = r.text
        if len(cache_html) >= MAX_CACHE_COUNT:
            # Python 3 中 dict 中的键值对是按照加入的顺序排列的
            # 所以直接删除第一个
            old_key = list(cache_html.keys())[0]
            cache_html.pop(old_key)
        # 添加新获取的 html
        cache_html[url] = html
        return html
    else:
        print('cannot access', url)
        return None


def get_page_url(domain: str, page_number: int) -> str:
    """
    获取指定博客某一页的网址
    """
    assert type(page_number) is int and page_number >= 1, '输入的页数有误'
    # 虽然 ?page=1 也是可以正确获取首页内容的，但最好还是不这样写
    if page_number == 1:
        return f'http://{domain}.lofter.com/'
    return f'http://{domain}.lofter.com/?page={page_number}'


def get_posts_in_page(url: str) -> List[str]:
    """
    获取博客某一页的所有推文的链接
    """
    # 推文链接形如 xxx.lofter.com/post
    # 前面必须加博客的域名，因为推主可能会转发别人的
    pattern = url[:url.index('.com/') + 5] + 'post'
    links = []
    html = get_html(url)
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    posts = soup.find_all('a', href=re.compile(pattern))
    for post in posts:
        href = post.get('href')
        # 忽略已有的推文链接
        # 这可能是由于一些奇怪的网页模板导致的
        if href in links:
            continue
        links.append(href)
    return links


def get_image_links_in_post(url: str) -> List[str]:
    """
    获取指定推文下的所有图片（高清原图）的链接
    """
    html = get_html(url)
    links = []
    soup = BeautifulSoup(html, 'html.parser')
    for link in soup.find_all(lambda tag: tag.has_attr('bigimgsrc')):
        links.append(link.get('bigimgsrc'))
    return links


def get_post_title(url: str) -> str:
    """
    获取推文的标题（一般是拿去做文件或文件夹的名称）
    """
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    # 有时候莫名其妙地，推文标题中会包含换行符
    return soup.head.title.string.split('\n')[0]


def get_filename(url: str) -> str:
    """
    从图片的链接中获取图片的真实名称
    """
    # 图片的名称形如：
    # zJtTDg2RGdJREZ3PT0.jpg
    # 5982469947077.jpg
    # http://xxx/xxx.jpg?imageView&amp;thumbnail=1680x0&amp;quality=96&amp;stripmeta=0&amp;type=jpg
    return re.search(r'[a-zA-Z0-9]+\.\w+(?=\?|$)', url).group()


def check_folder(path: Path) -> None:
    """
    检查文件夹是否存在。如果不存在，则创建
    """
    if not path.exists() or not path.is_dir():
        path.mkdir()


def download(url, filename, replace=False, timeout=None):
    """
    从给定的链接下载图片到指定的位置

    :param url: 图片链接
    :param filename: 保存地址
    :param replace: 是否覆盖已有的文件
    :return: 如果下载成功，则返回 (True, filepath)；否则返回 (False, url)
    """
    file = Path(filename)
    if not replace and file.exists():
        return (True, file)
    try:
        if not timeout:
            timeout = TIMEOUT
        img = requests.get(url, stream=True, timeout=timeout)
        if img.status_code == 200:
            with file.open('wb') as f:
                for chunk in img:
                    f.write(chunk)
        return (True, file)
    except:
        print(f'Downloading timeout: {url}')
        # 即使本地已经有该文件，八成也是有问题的
        if file.exists():
            file.unlink()
        return (False, url)


def is_valid_page(url: str) -> bool:
    """
    检查博客的指定页面是否存在。
    除了常规检查，还可以用来查看博客页数的上限
    """
    posts = get_posts_in_page(url)
    if posts:
        return True
    else:
        return False


def get_end_page_number(domain, start_page=1, max_page=0):
    """
    查找需要爬取的博客的结束页码

    Args:
        domain: 博客的域名
        start_page: 起始页（默认为 1）
        max_page: 最大总页数（默认为 0，表示直到最后一页）

    Returns:
        int: 结束页码
    """
    assert type(start_page) is int and start_page > 0
    assert type(max_page) is int and max_page >= 0
    # 如果最大页数给定
    if max_page:
        end_page = start_page + max_page - 1
        if is_valid_page(get_page_url(domain, end_page)):
            return end_page
        right = end_page - 1
    else:
        # 如果没有给定最大页数
        right = 32
    # 如果给定的起始页数已经是无效的
    if not is_valid_page(get_page_url(domain, start_page)):
        raise Exception('the given start page is invalid')
    # 寻找最小的无效页码
    left = 1
    while is_valid_page(get_page_url(domain, right)):
        left = right
        right *= 2
    # 二分法
    while right - left > 1:
        middle = (right - left) // 2 + left
        result = is_valid_page(get_page_url(domain, int(middle)))
        if result:
            left = middle
        else:
            right = middle
        if right - left == 1:
            if result:
                return middle
            else:
                return left


def get_domain_title(domain: str) -> str:
    """
    获取域名的标题

    Args:
        domain: 域名，形如 yurisa123

    Returns:
        str: 域名的标题
    """
    try:
        html = get_html(get_page_url(domain, 1))
        soup = BeautifulSoup(html, 'html.parser')
        title = re.split(r'(?s)\s', soup.head.title.string)[0].strip()
        return soup.head.title.string
    except:
        # 如果无法获取标题，则返回域名
        return domain


if __name__ == '__main__':
    print(get_end_page_number('yurisa123'))
