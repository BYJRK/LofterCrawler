from multiprocessing import Pool
from utils import *
import utils
import argparse
import time
from tqdm import tqdm

parser = argparse.ArgumentParser(description='爬取 Lofter 上面指定博客或贴子的图片')
parser.add_argument('domain', help='要爬取的博客域名或贴子链接')
parser.add_argument('--max', default=160,
                    type=int, help='最大爬取页数（默认为 160）')
parser.add_argument('--start', default=1, type=int, help='起始页（默认为 1）')
parser.add_argument('--end', default=-1, type=int, help='终止页（默认为 -1，表示忽略）')
parser.add_argument('--dir', help='图片存放路径（默认会从 domain 获取合适的文件名）')
parser.add_argument('--max_threads', default=8, type=int, help='最大线程数（默认为 8）')
parser.add_argument('--replace', default=False, type=bool,
                    help='是否覆盖已存在的文件（默认为否）')
parser.add_argument('--timeout', default=8, type=float,
                    help='超时时间（默认为 8 秒）')
parser.add_argument('--cache-count', default=10,
                    type=int, help='缓存网页的数量（默认为 10）')


def post_links_in_page_range():
    """get all post links in a given page range"""
    # post links to find image links inside
    post_links = []
    start_page = args.start
    if args.end != -1:
        assert args.end > args.start
        end_page = args.end
    else:
        end_page = get_end_page_number(args.domain, start_page, args.max)
    print(f'开始搜索从 {start_page} 页到 {end_page} 页的所有贴子链接')

    pool = Pool(processes=args.max_threads)
    results = pool.map_async(get_posts_in_page,
                             [get_page_url(args.domain, page) for page in range(start_page, end_page + 1)])
    for result in results.get():
        post_links.extend(result)
    pool.close()
    pool.join()
    print(f'共找到 {len(post_links)} 个贴子')
    return post_links


def image_links_in_post_links(post_links):
    """find all image links from a list of post links"""
    # image links to be downloaded later
    print('开始搜索所有贴子中的图片链接')
    image_links = []
    start = time.time()
    pool = Pool(processes=args.max_threads)
    results = pool.map_async(get_image_links_in_post, post_links)
    for result in results.get():
        image_links.extend(result)
    pool.close()
    pool.join()
    stop = time.time()
    print(
        f'共找到 {len(image_links)} 张图片，耗时 {stop - start:.4f} 秒')
    return image_links


def download_images_from_links(image_links):
    """download all images in image links"""
    print('开始下载图片')
    pbar = tqdm(total=len(image_links), ascii=True)
    start = time.time()
    failed_links = []
    results = []

    def download_callback(link):
        results.append(link)
        pbar.update()

    pool = Pool(processes=args.max_threads)
    for link in image_links:
        pool.apply_async(download, args=(link, args.dir / get_filename(link), args.replace),
                         callback=download_callback)
    pool.close()
    pool.join()
    pbar.close()
    failed_links.extend([link for link in results if link])
    stop = time.time()
    print(
        f'共下载 {len(image_links) - len(failed_links)} 张图片，耗时 {stop - start:.4f} 秒')
    if failed_links:
        print(f'其中 {len(failed_links)} 张图片下载失败，尝试重新下载')
        pool = Pool(processes=args.max_threads)
        results = []
        for link in failed_links:
            # 3 times the original timeout, force replace
            pool.apply_async(download, args=(link, args.dir / get_filename(link), True, args.timeout * 3),
                             callback=results.append)
        pool.close()
        pool.join()
        unavailable_links = []
        for link in (link for link in results if link):
            unavailable_links.append(link)
        if unavailable_links:
            print(
                f'无法下载 {len(unavailable_links)}，请稍后重试')
            for link in unavailable_links:
                print(link)


def crawl_domain():
    """find all images in a specific page range and download them"""
    print(f'开始爬取 {args.domain}.lofter.com')
    # check folder
    if not args.dir:
        args.dir = get_domain_title(args.domain)
    args.dir = Path(args.dir)
    check_folder(args.dir)
    # find all posts
    post_links = post_links_in_page_range()
    # find all image links to download
    image_links = image_links_in_post_links(post_links)
    # download all images from image links
    download_images_from_links(image_links)


def crawl_post(post_link):
    """find all images in a given post and download them"""
    if not args.dir:
        args.dir = args.domain.split('/')[-1]
    args.dir = Path(args.dir)
    check_folder(args.dir)
    print(f'存放位置：{args.dir}')

    image_links = get_image_links_in_post(args.domain)
    print(f"找到 {len(image_links)} 张图片，准备开始下载")
    download_images_from_links(image_links)


if __name__ == '__main__':
    args = parser.parse_args()

    # 设置初始参数
    utils.TIMEOUT = args.timeout
    utils.MAX_CACHE_COUNT = args.cache_count

    # domain name looks like [a-zA-Z0-9-]+
    # post link looks like domain.lofter.com/post/...
    # 先检查是否为单个 post
    if re.search(r'\.lofter\.com/post/', args.domain):
        crawl_post(args.domain)
    # 然后提取 domain 名称
    re_domain = re.search(
        r'(?:http://)?([a-zA-Z0-9-]+)(?:\.\w+\.com.*)?', args.domain)
    if re_domain:
        args.domain = re_domain.group(1)
        crawl_domain()
    else:
        raise Exception("输入的域名有误。")
    print('下载完毕。')
