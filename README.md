# LofterCrawler
A multi-threading Lofter crawler based on Python 3.6

## Usage
```
python loftercrawler.py -h
usage: loftercrawler.py [-h] [-max MAX_PAGE] [-start START_PAGE]
                        [-dir DIRECTORY] [--max_threads MAX_THREADS]
                        [-r REPLACE] [--timeout TIMEOUT]
                        domain

positional arguments:
  domain

optional arguments:
  -h, --help            show this help message and exit
  -max MAX_PAGE, --max_page MAX_PAGE
                        maximum page amount (default = 160)
  -start START_PAGE, --start_page START_PAGE
                        start searching from this page
  -dir DIRECTORY, --directory DIRECTORY
                        save the downloaded images to this local folder
  --max_threads MAX_THREADS
  -r REPLACE, --replace REPLACE
                        replace the existing files with the same name
  --timeout TIMEOUT     request timeout (second, default = 8)
```
  
# Examples

- If you want to **download all images from yurisa123.lofter.com** (Yurisa's Lofter Homepage), you can type:
```shell
python loftercrawler.py yurisa123
```
Then the crawler will start working and the images will be saved to a folder named *yurisa* (acquired from the webpage head.title) in the same directory with the program itself by default. The program will start searching posts from page 1 to maximally page 160 (max page amount is 160 by default)

- If you want to **start from page 5**, and the **total page amount is 10** (page 5 ~ 14), then:
```shell
python loftercrawler.py yurisa123 -start 5 -max 10
```

- If you want to **save the images to another folder**, you can type:
```shell
python loftercrawler.py yurisa123 -dir my_favorite_images
```

- `--max_threads 8` means the number of worker processes ([for more details](https://docs.python.org/3.6/library/multiprocessing.html#using-a-pool-of-workers))

- `--timeout 8` is the read timeout of HTTP requests ([for more details](http://docs.python-requests.org/en/master/user/advanced/#timeouts))

- `--replace` will force the download process to replace the existing files in the folder. Otherwise, the program will ignore the file which (seems to) have been downloaded.

## Enjoy Your Photo Collection

This program still needs improvements.

Looking forward to your comments!
