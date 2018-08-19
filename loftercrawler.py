from multiprocessing import Pool
from utils import *
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument('domain')
parser.add_argument('-max', '--max_page', default=160, type=int,
                    help='maximum page amount (default = 160)')
parser.add_argument('-start', '--start_page', default=1, type=int,
                    help='start searching from this page')
parser.add_argument('-dir', '--directory',
                    help='save the downloaded images to this local folder')
parser.add_argument('--max_threads', default=8, type=int)
parser.add_argument('-r', '--replace', default=False, type=bool,
                    help='replace the existing files with the same name')
parser.add_argument('--timeout', default=8, type=float,
                    help='request timeout (second, default = 8)')


def multi_threading():
    print(f'Start crawling {args.domain}.lofter.com')
    # image links to be downloaded later
    image_links = []
    # post links to find image links inside
    post_links = []

    # find all posts
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

    # find all image links in post_links
    start = time.time()
    pool = Pool(processes=args.max_threads)
    results = pool.map_async(get_image_links_in_post, post_links)
    for result in results.get():
        image_links.extend(result)
    pool.close()
    pool.join()
    stop = time.time()
    print(f'Found {len(image_links)} images. Elapsed time: {stop - start:.4f} seconds.')

    # download all images in image_links
    while True:  # loop until all finished or user abandon further downloading
        start = time.time()
        failed_links = []
        results = []
        pool = Pool(processes=args.max_threads)
        for link in image_links:
            pool.apply_async(download, args=(link, args.directory / get_filename(link), args.replace),
                             callback=results.append)
        pool.close()
        pool.join()
        if results:
            for result in (result for result in results if result):
                failed_links.append(result)
        stop = time.time()
        print(f'Downloaded {len(image_links) - len(failed_links)} images. Elapsed time is {stop - start:.4f} seconds.')
        while failed_links:
            choice = input(f'{len(failed_links)} image(s) failed. Try again? (y/n) > ')
            if choice == 'n':
                failed_links.clear()
                break
            if choice != 'y':
                continue
            image_links = failed_links.copy()
        else:
            break
        # stop retrying
        if choice == 'n':
            break

    print('Downloading finished. Goodbye!')


if __name__ == '__main__':
    args = parser.parse_args(['ssf91'])
    # check if folder name is given
    if not args.directory:
        args.directory = get_domain_title(args.domain)
        args.directory = Path(args.directory)
    check_folder(args.directory)
    # set default timeout
    TIMEOUT = args.timeout

    multi_threading()
