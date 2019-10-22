import requests, json, jieba, matplotlib
import matplotlib.pyplot as mp

# 请求头信息(字典键值对)集合是元素，列表[] 每次发送请求获取的具体信息。伪装成浏览器
#大部分的网站（各类中小型网站）都会需要你的代码有headers的信息，如果没有，会直接拒绝
# 你的访问！大型网站反而很少，尤其是门户网站，比如新浪新闻、头条图集、百度图片的爬虫，基本没有什么反爬措施
send_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763",
    "Connection": "keep-alive",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-Hans-CN, zh-Hans; q=0.5"}

search_url="https://c.y.qq.com/soso/fcgi-bin/client_search_cp?ct=24&qqmusic_ver=1298&new_json=1&remoteplace=txt.yqq.center&searchid=40760622670982158&t=0&aggr=1&cr=1&catZhida=1&lossless=0&flag_qc=0&p=1&n=10&w={}&g_tk=5381&loginUin=0&hostUin=0&format=json&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq.json&needNewCode=0"
comment_count_url = "https://c.y.qq.com/base/fcgi-bin/fcg_global_comment_h5.fcg?g_tk=5381&loginUin=0&hostUin=0&format=json&inCharset=utf8&outCharset=GB2312&notice=0&platform=yqq.json&needNewCode=0&cid=205360772&reqtype=1&biztype=1&topid={}&cmd=4&needmusiccrit=0&pagenum=0&pagesize=0&lasthotcommentid=&domain=qq.com"
comment_url = "https://c.y.qq.com/base/fcgi-bin/fcg_global_comment_h5.fcg?g_tk=5381&loginUin=0&hostUin=0&format=json&inCharset=utf8&outCharset=GB2312&notice=0&platform=yqq.json&needNewCode=0&cid=205360772&reqtype=2&biztype=1&topid={}&cmd=8&needmusiccrit=0&pagenum={}&pagesize=25&lasthotcommentid=&domain=qq.com&ct=24&cv=10101010"


delwords = ["em"]

def requestData(url):
    '''

    :param url: 请求数据的地址
    :return: 响应内容
    '''
    #Request方法把url和headers组合在一起就可以构造一个比较简单的请求了。Request有三个参数（url,data,headers）
    # 如果有使用data就是post请求了，没有就是get请求。
    # 这里我没有data，所以我就指定headers=header，不然header就会被当成data了。
    txt = requests.get(url, headers=send_headers)
    txt.encoding="utf-8"
    return  txt.text

def search_song(keyword):
    '''

    :param keyword: 用户输入歌曲名
    :return: 歌曲信息列表：歌曲名，歌手，专辑名，歌曲id
    '''
    data = requestData(search_url.format(keyword))
    js = dict(json.loads(data))
    #print(data)
    #print(js["data"]["song"]["list"])
    order = 1
    print("=" * 200)
    print("{:5}\t{:40}\t{:40}\t{}".format("序号", "歌曲名", "歌手", "专辑"))
    print("=" * 200)
    for i in js["data"]["song"]["list"]:
        singer = i["singer"][0]["name"]
        if len(i["singer"]) > 1:
            for j in i["singer"][1:]:
                singer += "&" + j["name"]
        i["singers"] = singer
        print("{:<5}\t{:40}\t{:40}\t{}".format(str(order).zfill(2), i["title"], singer, i["album"]["name"]))
        order += 1
    print("=" * 200)
    s = input("请输入序号：")
    while not s.isdigit() or int(s) < 1 or int(s) > order - 1:
        s = input("请重新输入序号：")
    songinfo = js["data"]["song"]["list"][int(s) - 1]
    return (songinfo["title"], songinfo["singers"], songinfo["album"]["name"], songinfo["id"])

def getComments_num(id):
    '''

    :param id: 区别每一首歌的id
    :return: 歌曲评论总数量
    '''
    data = requestData(comment_count_url.format(id))
    js = json.loads(data)
    return js["commenttotal"]

def getComments(songinfo):
    '''

    :param songinfo: 歌曲信息
    :return: 评论列表：序号，用户名，点赞数量，评论内容
    '''
    commentscount = getComments_num(songinfo[3])
    print("歌曲《{}》一共有 {} 条评论".format(songinfo[0], commentscount))
    s = input("请输入要爬取评论的数量：")
    while not s.isdigit():
        s = input("请重新输入要爬取评论的数量：")
    n = int(s)
    if int(s) < 100:
        n = 100
    if int(s) > commentscount:
        n = commentscount
    print("=" * 200)
    print("{:5}\t{:20}\t{:5}\t{}".format("序号", "用户名", "赞", "评论"))
    print("=" * 200)
    order = 1
    commentstext = ""
    for j in range(int(n / 25)):
        data = json.loads(requestData(comment_url.format(songinfo[3], j)))
        for i in data["comment"]["commentlist"]:
            print("{:<5}\t{:20}\t{:<5}\t{}".format(order, i["nick"], i["praisenum"], i["rootcommentcontent"][:200]))
            commentstext += i["rootcommentcontent"]
            order += 1
    print("=" * 200)
    print("成功爬取评论{}条".format(order - 1))
    return commentstext

def splitWords(conmments):
    '''

    :param conmments: 获取的全部评论
    :return: 分词完毕后的列表
    '''
    print("正在分词中...")
    words = jieba.cut(conmments)#返回一个可迭代的数据类型
    data = {}#通过键值对的形式存储词语及出现的次数
    for i in words:
        if len(i) == 1:#单个词语不计算在内
            continue
        data[i] = data.get(i, 0) + 1 #遍历所有词语，每出现一次其对应的值加 1。如果有i这个键就返回这个键的值，没有的话就返回0（默认值）.
    for i in delwords:
        if data.get(i, 0) > 0:#判断是否有键，不然直接删除的话会出错。
            del data[i]
    li = list(data.items())#将键值（元组）对转换为列表
    li.sort(key=lambda i: i[1], reverse=True)#根据词语出现的次数进行从大到小的排序
    print("=" * 200)
    print("{:5}\t{:5}\t{}".format("排名", "出现次数", "词"))
    print("=" * 200)
    order = 1
    for i in li[:20]:
        print("{:<5}\t{:<5}\t{}".format(order, i[1], i[0]))
        order += 1
    print("=" * 200)
    return li[:20]

def paint(data, songinfo):
    x = [i[0] for i in data]#快速生成列表
    y = [i[1] for i in data]
    '''
    X = []
    for i in data:
    x.append(i[0])
    '''
    matplotlib.rcParams['font.family'] = 'SimHei'
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    mp.figure()#创建画板对象
    mp.bar(x, y, color="#66ccff")
    mp.title("《{}-{}》的评论词频统计 ".format(songinfo[0], songinfo[1]))
    mp.show()


#状态200请求成功
#print(requestData(search_url))


songinfo = search_song(input("请输入关键字："))
commentstr = getComments(songinfo)
wordsdata = splitWords(commentstr)
paint(wordsdata, songinfo)
