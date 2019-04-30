# LofterCrawler

一个基于 Python 3.6 的多线程 [Lofter](http://www.lofter.com/) 爬虫

## 用法
```
python loftercrawler.py -h
usage: loftercrawler.py [-h] [--max MAX] [--start START] [--end END]
                        [--dir DIR] [--max_threads MAX_THREADS]
                        [--replace REPLACE] [--timeout TIMEOUT]
                        [--cache_count CACHE_COUNT] [--retry RETRY]
                        [--save_failed]
                        domain

爬取 Lofter 上面指定博客或贴子的图片

positional arguments:
  domain                要爬取的博客域名或贴子链接

optional arguments:
  -h, --help            show this help message and exit
  --max MAX             最大爬取页数（默认为 160）
  --start START         起始页（默认为 1）
  --end END             终止页（默认为 -1，表示忽略）
  --dir DIR             图片存放路径（默认会从 domain 获取合适的文件名）
  --max_threads MAX_THREADS
                        最大线程数（默认为 8）
  --replace REPLACE     是否覆盖已存在的文件（默认为否）
  --timeout TIMEOUT     超时时间（默认为 8 秒）
  --cache_count CACHE_COUNT
                        缓存网页的数量（默认为 10）
  --retry RETRY         尝试下载失败图片的次数（默认为 1）
  --save_failed         是否将下载失败的图片链接保存到本地
```

## Examples

我们拿 [yurisa 的 Lofter 主页](http://yurisa123.lofter.com/)作为例子。

首先我们简单解释一下 Lofter 上的网址的特点：

1. http://yurisa123.lofter.com/ 是主页的链接，其中`yurisa123`就是域名。域名只可以是大小写字母、数字以及短横线

现在正式开始简单的使用教程：

- 假如你想下载所有图片，那么可以输入以下任意一种指令，它们都是等价的：

```shell
python loftercrawler.py yurisa123
python loftercrawler.py yurisa123.lofter.com
python loftercrawler.py http://yurisa123.lofter.com/
```

然后程序就会开始寻找这些页中的图片，随后开始下载。

- 如果你想下载从第 5 页到第 10 页（共 6 页）的图片，可以这样：

```shell
python loftercrawler.py yurisa123 --start 5 --max 6
python loftercrawler.py yurisa123 --start 5 --stop 10
```

- 如果你希望将图片下载到指定目录，可以这样（目录会自动创建）：

```shell
python loftercrawler.py yurisa123 --dir my_favorite_images
```

- 如果你想下载某个贴子下面的所有图片，可以：

```shell
python loftercrawler.py http://yurisa123.lofter.com/post/1cf5f941_12bd7e63c
```

- 其他常用参数的解释：

- `--max_threads 8` 最大线程数 ([详细解释](https://docs.python.org/3.6/library/multiprocessing.html#using-a-pool-of-workers))

- `--timeout 8` HTTP 请求的超时时间（秒） ([for more details](http://docs.python-requests.org/en/master/user/advanced/#timeouts))

- `--cache_count 10` 缓存的网址数量（默认为 10，已经够用。更多也不会有什么速度提升）

- `--replace` 是否覆盖已存在的同名文件（如果否，即便已存在的文件损坏，也会直接跳过对应图片的下载）

- `--retry 1` 最大重试次数（默认为 1）

- `--save_failed` 是否将失败的图片链接列表保存到本地


## 算法

1. 确定页数的范围（程序默认从第 1 页开始，最大页数为 160 页，即页码范围是 `[1, 160]`）
1. 搜索每一页上的贴子
1. 搜索所有贴子中的图片链接
1. 开始下载所有图片
1. 如果下载过程中出现下载失败的情况，程序会记录这些失败的图片链接，并在结束之后进行多次尝试（具体看重试次数的设置，默认为重试 1 次）

## 近期计划

1. 将图片按照贴子分开存放到不同的文件夹中
1. 试图从网页中嗅探更加合适的文件夹或图片名称
1. 添加更多的参数，比如是否删掉边长过小的图片
1. 自动删除被和谐的图片
1. 从文本文件读取图片链接列表并进行下载

## 未来计划

1. 设计一个用户界面，更便于操作
1. 引入卷积神经网络，对图片中人物的颜值等进行打分，从而筛选下载的图片
