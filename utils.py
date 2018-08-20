from pathlib import Path
import requests
import re
from bs4 import BeautifulSoup


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/68.0.3440.106 Safari/537.36 '
}
TIMEOUT = 8


def get_html(url):
    """Get the html doc from the given url"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        return r.text
    except Exception as e:
        print(f'Cannot access {url}. Reason: {e}')
        return ''


def get_page_url(domain, page_number):
    """Get the url of a specific page within a lofter domain"""
    assert type(page_number) is int and page_number >= 1

    if page_number == 1:
        return f'http://{domain}.lofter.com/'
    return f'http://{domain}.lofter.com/?page={page_number}'


def get_posts_in_page(url):
    """
    Get the links of posts on a page
    :param url: the url of the page
    :return: list of links
    """
    # input url is like: http://xxx.lofter.com/
    #                    http://xxx.lofter.com/?page=2
    # the pattern should be: ................./post
    pattern = url[:url.index('.com/') + 5] + 'post'
    links = []
    html = get_html(url)
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    # the link need to be limited to the given domain
    # because the author may repost others' posts
    posts = soup.find_all('a', href=re.compile(pattern))
    for post in posts:
        href = post.get('href')
        # ignore the repeated posts which may caused by different
        # kinds of homepage template used by the author
        if href in links:
            continue
        links.append(href)
    return links


def get_image_links_in_post(url):
    """Get the image (original size) links from the given post link"""
    html = get_html(url)
    links = []
    soup = BeautifulSoup(html, 'html.parser')
    for link in soup.find_all(lambda tag: tag.has_attr('bigimgsrc')):
        links.append(link.get('bigimgsrc'))
    return links


def get_filename(url):
    """Generate the image filename from its url"""
    # two examples
    # zJtTDg2RGdJREZ3PT0.jpg
    # 5982469947077.jpg
    # http://xxx/xxx.jpg?imageView&amp;thumbnail=1680x0&amp;quality=96&amp;stripmeta=0&amp;type=jpg
    return re.search(r'[a-zA-Z0-9]+\.\w+(?=\?|$)', url).group()


def check_folder(path):
    """Check if the given folder path exists. If not, create it"""
    if not path.exists() or not path.is_dir():
        path.mkdir()


def download(url, filename, replace=False, timeout=None):
    """
    Download the file (typically image) from the url to the local path
    :param url: link of the file
    :param filename: save to the path
    :param replace: replace the existing file with the same name
    :return: None if downloaded successfully (or already exists). Otherwise, return the failed url
    """
    file = Path(filename)
    if not replace and file.exists():
        return
    try:
        if timeout:
            timeout = TIMEOUT
        img = requests.get(url, stream=True, timeout=timeout)
        if img.status_code == 200:
            with file.open('wb') as f:
                for chunk in img:
                    f.write(chunk)
        return
    except:
        print(f'Downloading timeout: {url}')
        if file.exists():
            file.unlink()
        return url


def is_valid_page(url):
    """Check if the page is valid (contains posts)"""
    posts = get_posts_in_page(url)
    if posts:
        return True
    else:
        return False


def get_end_page_number(domain, start_page=1, max_page=0):
    """Find the max page number according to the given max page number"""
    assert type(start_page) is int and start_page > 0
    assert type(max_page) is int and max_page >= 0
    # if max_page is given
    if max_page:
        end_page = start_page + max_page - 1
        if is_valid_page(get_page_url(domain, end_page)):
            return end_page
        right = end_page - 1
    else:
        # if max_page is not given
        right = 32
    # if the given start page is already invalid
    if not is_valid_page(get_page_url(domain, start_page)):
        raise Exception('the given start page is invalid')
    # find the smallest invalid page number by multiplying 2
    left = 1
    while is_valid_page(get_page_url(domain, right)):
        left = right
        right *= 2
        # print(f'{left}, {right}')
    # bisection method
    while right - left > 1:
        middle = (right - left) // 2 + left
        # print(f'{left}, {middle}, {right}')
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


def get_domain_title(domain):
    """Find the domain title in its html doc"""
    try:
        html = get_html(get_page_url(domain, 1))
        soup = BeautifulSoup(html, 'html.parser')
        return soup.head.title.string
    except:
        # for some reason, the title cannot be reached
        return domain


if __name__ == '__main__':
    print(get_end_page_number('yurisa123'))
