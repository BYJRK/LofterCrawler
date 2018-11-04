from multiprocessing import Pool
from utils import *
import utils
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument('domain', help='domain name or post link')
parser.add_argument('-max', '--max_page', default=160, type=int,
                    help='maximum page amount (default = 160)')
parser.add_argument('-start', '--start_page', default=1, type=int,
                    help='start searching from this page')
parser.add_argument('-dir', '--directory',
                    help='save the downloaded images to this local folder')
parser.add_argument('--max_threads', default=8, type=int)
parser.add_argument('-r', '--replace', default=False, type=bool,
                    help='replace the existing files with the same name (default = False)')
parser.add_argument('--timeout', default=8, type=float,
                    help='request timeout (second, default = 8)')


def post_links_in_page_range():
    """get all post links in a given page range"""
    # post links to find image links inside
    post_links = []
    start_page = args.start_page
    end_page = get_end_page_number(args.domain, start_page, args.max_page)
    print(f'Searching from page {start_page} to {end_page}')

    pool = Pool(processes=args.max_threads)
    results = pool.map_async(get_posts_in_page,
                             [get_page_url(args.domain, page) for page in range(start_page, end_page + 1)])
    for result in results.get():
        post_links.extend(result)
    pool.close()
    pool.join()
    print(f'Found {len(post_links)} posts.')
    return post_links
    

def image_links_in_post_links(post_links):
    """find all image links from a list of post links"""
    # image links to be downloaded later
    image_links = []
    start = time.time()
    pool = Pool(processes=args.max_threads)
    results = pool.map_async(get_image_links_in_post, post_links)
    for result in results.get():
        image_links.extend(result)
    pool.close()
    pool.join()
    stop = time.time()
    print(f'Found {len(image_links)} images. Elapsed time: {stop - start:.4f} seconds.')
    return image_links


def download_images_from_links(image_links):
    """download all images in image links"""
    print('Start downloading...')
    start = time.time()
    failed_links = []
    results = []
    pool = Pool(processes=args.max_threads)
    for link in image_links:
        pool.apply_async(download, args=(link, args.directory / get_filename(link), args.replace),
                         callback=results.append)
    pool.close()
    pool.join()
    for link in (link for link in results if link):
        failed_links.append(link)
    stop = time.time()
    print(f'Downloaded {len(image_links) - len(failed_links)} images. Elapsed time is {stop - start:.4f} seconds.')
    if failed_links:
        print(f'{len(failed_links)} image(s) failed. Retrying...')
        pool = Pool(processes=args.max_threads)
        results = []
        for link in failed_links:
            # 3 times the original timeout, force replace
            pool.apply_async(download, args=(link, args.directory / get_filename(link), True, args.timeout * 3),
                             callback=results.append)
        pool.close()
        pool.join()
        unavailable_links = []
        for link in (link for link in results if link):
            unavailable_links.append(link)
        if unavailable_links:
            print(f'{len(unavailable_links)} not available. Please download them later.')
            for link in unavailable_links:
                print(link)


def crawl_domain():
    """find all images in a specific page range and download them"""
    print(f'Start crawling {args.domain}.lofter.com')
    # check folder
    if not args.directory:
        args.directory = get_domain_title(args.domain)
    args.directory = Path(args.directory)
    check_folder(args.directory)
    # find all posts
    post_links = post_links_in_page_range()
    # find all image links to download
    image_links = image_links_in_post_links(post_links)
    # download all images from image links
    download_images_from_links(image_links)


def crawl_post(post_link):
    """find all images in a given post and download them"""
    if not args.directory:
        args.directory = args.domain.split('/')[-1]
    args.directory = Path(args.directory)
    check_folder(args.directory)
    print(f'folder: #{args.directory}#')
    
    image_links = get_image_links_in_post(args.domain)
    print(f"Found {len(image_links)} images.")
    download_images_from_links(image_links)

if __name__ == '__main__':
    args = parser.parse_args()

    # set default timeout
    utils.TIMEOUT = args.timeout

    # domain name looks like [a-zA-Z0-9]+
    # post link looks like domain.lofter.com/post/...
    if re.search(r'\.lofter\.com/post/', args.domain):
        crawl_post(args.domain)
    else:
        crawl_domain()
    print('Downloading finished. Goodbye!')
