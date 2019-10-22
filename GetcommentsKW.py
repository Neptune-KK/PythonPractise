import requests, json, jieba, re, matplotlib
from urllib.parse import unquote
import matplotlib.pyplot as plt

abandonedwords = ["em", r"e\d{6}"]
send_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763",
    "Connection": "keep-alive",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-Hans-CN, zh-Hans; q=0.5"}

search_url = "http://www.kuwo.cn/api/www/search/searchMusicBykeyWord?key={}&pn=1&rn={}&reqId=8817c210-f273-11e9-ad41-231c120be14a"
comment_url = "http://www.kuwo.cn/comment?type=get_comment&f=web&page={}&rows=20&digest=15&sid={}&uid=0&prod=newWeb&reqId=c9ad6430-f275-11e9-ad41-231c120be14a"
hot_comment_url = "http://www.kuwo.cn/comment?type=get_rec_comment&f=web&page={}&rows=20&digest=15&sid={}&uid=0&prod=newWeb&reqId=c9825c90-f275-11e9-ad41-231c120be14a"
lrc_url = "http://m.kuwo.cn/newh5/singles/songinfoandlrc?musicId={}&reqId=c97f2840-f275-11e9-ad41-231c120be14a"

def requestdata(url=""):
    '''
    获取指定URL的内容
    :param url: URL
    :return: 相应字符串
    '''
    res = requests.get(url=url, headers=send_headers)
    res.encoding = "utf-8"
    return res.text

def search(kw, n=30):
    '''
    按关键字搜索歌曲
    :param kw: 关键字
    :param n: 搜索数量
    :return: 选定的歌曲信息
    '''
    txt = requestdata(search_url.format(kw, n))
    data = dict(json.loads(txt))
    print("=" * 300)
    print("{:5}\t{:50}\t{:50}\t{:50}\t{}".format("序号", "歌曲", "歌手", "专辑", "时长"))
    print("=" * 300)
    num = 0
    for i in data["data"]["list"]:
        print("{:<5}\t{:50}\t{:50}\t{:50}\t{}".format(str(num).zfill(2), i["name"], i["artist"], i["album"], i["songTimeMinutes"]))
        num += 1
    print("=" * 300)
    order = int(input("请输入序号："))
    while order < 0 or order > num - 1:
        order = int(input("请重新输入序号："))
    d = data["data"]["list"][order]
    return (d["rid"], d["name"], d["artist"], d["album"], d["songTimeMinutes"])

def getcommentsnum(songinfo, ishot=True):
    '''
    获取指定歌曲的评论数量
    :param songinfo:要获取评论数量的歌曲
    :param ishot: 值为True则获取热门评论数量，否则获取最新评论数量
    :return: 指定歌曲的评论总数和评论总页数
    '''
    url = comment_url
    if ishot:
        url = hot_comment_url
    dic = dict(json.loads(requestdata(url.format(1, songinfo[0]))))
    dic["total"] = dic.get("total", 0)
    dic["totalPage"] = dic.get("totalPage", 0)
    return (dic["total"], dic["totalPage"])

def getcomments(songinfo, ishot = True):
    '''
    获取指定歌曲的评论
    :param songinfo: 要获取评论的歌曲
    :param ishot: 值为True则获取热门评论，否则获取最新评论
    :return: 所获取的所有评论字符串和评论数量
    '''
    url = comment_url
    if ishot:
        url = hot_comment_url
    commentinfo = getcommentsnum(songinfo, ishot)
    if int(commentinfo[0]) <= 0:
        print("该歌曲还没有评论哦")
        return None
    if ishot:
        print("【歌曲 《{}》 的热门评论一共有 {} 条，{} 页】".format(songinfo[1], commentinfo[0], commentinfo[1]))
    else:
        print("【歌曲 《{}》 的最新评论一共有 {} 条，{} 页】".format(songinfo[1], commentinfo[0], commentinfo[1]))
    s = input("请输入要爬取评论页数：")
    pagesize = int(commentinfo[1])
    if s != "":
        while not s.isdigit():
            s = input("请重新输入要爬取评论的页数：")
        if int(s) < int(commentinfo[1]):
            pagesize = int(s)
        if int(s) < 1:
            pagesize = 1
    print("=" * 300)
    print("{:5}\t{:20}\t{:10}\t{:30}\t{}".format("序号", "评论时间", "赞", "用户", "评论内容"))
    print("=" * 300)
    num = 1
    commentstr = ""
    for j in range(1, pagesize+1):
        try:
            data = dict(json.loads(requestdata(url.format(j, songinfo[0]))))
            for i in data["rows"]:
                print("{:5}\t{:20}\t{:10}\t{:30}\t{}".format(str(num).zfill(2), i["time"], i["like_num"], unquote(i["u_name"], encoding="utf-8"), str(i["msg"])).replace("\n", ""))
                commentstr += i["msg"]
                num += 1
        except:
            pass
    print("=" * 300)
    return (commentstr, num - 1)

def getlrc(songinfo):
    '''
    获取指定歌曲的歌词
    :param songinfo: 要获取歌词的歌曲
    :return: 歌词字符串
    '''
    txt = requestdata(lrc_url.format(songinfo[0]))
    txt = txt.replace("null", '"Null"')
    data = dict(json.loads(txt))
    if data["data"]["lrclist"] == "Null":
        return ""
    print("=" * 300)
    print("{:5}\t{:15}\t{}".format("序号", "时间", "歌词"))
    print("=" * 300)
    num = 0
    lrc = ""
    for i in data["data"]["lrclist"]:
        print("{:5}\t{:15}\t{}".format(str(num).zfill(2), i["time"], i["lineLyric"]))
        lrc += i["lineLyric"]
        num += 1
    print("=" * 300)
    return lrc

def splitwords(txt):
    '''
    分词
    :param txt:要进行分词的字符串
    :return: 已分词完毕且排序的词列表
    '''
    words = jieba.lcut(txt)
    data = dict()
    for i in words:
        if len(i) >= 2:
            data[i] = data.get(i, 0) + 1
    for i in abandonedwords:
        if data.get(i, 0) > 0:
            del data[i]
        for j in list(data.keys()):
            if re.search(i, j) != None:
                del data[j]
    items = list(data.items())
    items.sort(key=lambda b: b[1], reverse=True)
    return items

def paint(songinfo, hotcommentstr, commentstr, lrc):
    '''
    绘制词频图
    :param songinfo:要绘制图像的歌曲
    :param hotcommentstr: 热门评论
    :param commentstr: 最近评论
    :param lrc: 歌词
    :return:
    '''
    comlist = splitwords(commentstr[0])
    hotcomlist = splitwords(hotcommentstr[0])
    lrclist = splitwords(lrc)
    print("【歌曲《{}-{}》的词频统计】".format(songinfo[1], songinfo[2]))
    print("=" * 300)
    print("{:5}\t{:>14}\t{:20}\t{:>10}\t{:20}\t{:>13}\t{}".format("排名", "热门评论词数量", "热门评论词", "最新评论词数量", "最新评论词", "歌词分词数量", "歌词分词"))
    print("=" * 300)
    num = 1
    for i in range(20):
        print("{:5}\t{:20}\t{:20}\t{:20}\t{:20}\t{:20}\t{}".format(str(num).zfill(2), hotcomlist[i][1], hotcomlist[i][0], comlist[i][1], comlist[i][0], lrclist[i][1], lrclist[i][0]))
        num += 1
    print("=" * 300)
    matplotlib.rcParams['font.family'] = 'SimHei'
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    plt.figure()

    '''
    plt.subplot(a, b, c)
    a:行数
    b:列数
    c:第几个绘图区域
    例如plt.subplot(2, 2, 1)表示把绘图面板划分为2X2的四份，取第1份绘图
    
    plt.bar()
    绘制条形图
    
    plt.pie()
    绘制饼图
    
    '''
    #最新评论词频统计
    plt.subplot(2, 2, 1)
    x1 = [i[0] for i in comlist[:20]]
    y1 = [i[1] for i in comlist[:20]]
    plt.bar(x1[::-1], y1[::-1], 0.5, color="#ff7f7f")
    plt.title("《{}-{}》 的 {} 条最新评论词频前20统计".format(songinfo[1], songinfo[2], commentstr[1]))

    #热门评论词频统计
    plt.subplot(2, 2, 2)
    x2 = [i[0] for i in hotcomlist[:20]]
    y2 = [i[1] for i in hotcomlist[:20]]
    plt.bar(x2, y2, 0.5, color="#66CCFF")
    plt.title("《{}-{}》 的 {} 条热门评论词频前20统计".format(songinfo[1], songinfo[2], hotcommentstr[1]))

    #歌词词频统计
    plt.subplot(2, 2, 3)
    if len(lrclist) > 0:
        x3 = [i[0] for i in lrclist[:20]]
        y3 = [i[1] for i in lrclist[:20]]
        plt.bar(x3[::-1], y3[::-1], 0.5, color="#4ECC00")
        plt.title("《{}-{}》 的歌词词频前20统计".format(songinfo[1], songinfo[2]))
    else:
        plt.title("该歌曲没有歌词")

    #热门评论词频饼图统计
    plt.subplot(2, 2, 4)
    x4 = [i[0] for i in hotcomlist[:10]]
    y4 = [i[1] / sum(y1[:10]) for i in hotcomlist[:10]]
    y4 = [i[1] for i in hotcomlist[:10]]
    plt.pie(y4, labels=x4, autopct="%1.1f%%", shadow=False)
    plt.legend(labels=x4, loc='upper right')
    plt.title("《{}-{}》 的 {} 条热门评论词频前10统计".format(songinfo[1], songinfo[2], hotcommentstr[1]))
    plt.show()


while True:
    kw = input("请输入要搜索的关键字：")
    if kw.replace(" ", "") != "":
        songinfo = search(kw)
        hotcomments = getcomments(songinfo, ishot=True)
        comments = getcomments(songinfo, ishot=False)
        lrc = getlrc(songinfo)
        if hotcomments == None:
            continue
        paint(songinfo, hotcomments, comments, lrc)
    print()