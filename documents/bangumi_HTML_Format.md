### 1.番剧网页
番剧网页包括动漫番剧以及电影.

url为 `https://www.bilibili.com/bangumi/play/epxxxxx`

#### 网页格式
没用的用省略号代替,只写有用的

```html
<!DOCTYPE html>
<html>
  
  <head>
    ...
    <title>番剧标题+视频标题</title>
    <meta name="description" content="是简介">
    <meta name="keywords" content="是标题">
    <meta name="author" content="是up主名字">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta property="og:title" content="是标题">
    <meta property="og:type" content="video.anime或者video.movie">
    <meta property="og:url" content="https://www.bilibili.com/bangumi/play/ss0000/">
    ...
<script>!
    ...
    <script type="application/ld+json">{
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": [{
          "@type": "VideoObject",
          "position": 1,
          "name": "番剧名字",
          "url": "https://www.bilibili.com/bangumi/play/ss0000/",
          "description": "",
          "thumbnailUrl": ["https://i0.hdslb.com/bfs/archive/xxx.jpg"],
          "uploadDate": "2020-01-08T14:30:00.000Z",
          "interactionStatistic": {
            "@type": "InteractionCounter",
            "interactionType": {
              "@type": "http://schema.org/WatchAction"
            },
            "userInteractionCount": "1234"
          }
        }]
      }</script>
  </head>
...
<script>window.__INITIAL_STATE__ = {
        "loaded": true,
        "ver": {},
        "ssr": {},
        "loginInfo": {},
        "h1Title": "系列名+标题",  // 如果是ss链接则标题不存在
        "mediaInfo": {
          "stat": {
            "coins": 123,
            "danmakus": 123,
            "favorites": 123,
            "reply": 123,
            "share": 123,
            "views": 123
          },
          "id": 123, //番剧题目id,是数字,网址一般是https://www.bilibili.com/bangumi/media/mdxxxx
          "ssId": 456, //番剧id,网址一般是https://www.bilibili.com/bangumi/play/ssyyyyy
          "title": "某一季的题目",
          "jpTitle": "",
          "series": "系列名",
          "alias": "",
          "evaluate": "简介",
          "ssType": 1,
          "ssTypeFormat": {
            "name": "番剧",
            "homeLink": "\u002F\u002Fwww.bilibili.com\u002Fanime\u002F"
          },
...
//正片列表
"epList": [{
          "loaded": false,
          "id": 788, //ep号,一部剧下面ep号不同.网址一般为 https://www.bilibili.com/bangumi/play/ep788
          "badge": "",
          "badgeType": 0,
          "epStatus": 2,
          "aid": 345,
          "bvid": "",
          "cid": 111, //oid号,是需要的
          "from": "bangumi",
          "cover": "\u002F\u002Fi0.hdslb.com\u002Fbfs\u002Farchive\u002Fffff.jpg",
          "title": "x",
          "titleFormat": "第x话",
          "vid": "",
          "longTitle": "长标题", // 剧集的名称
          "hasNext": true,
          "i": 0,
          "sectionType": 0,
          "releaseDate": "",
          "skip": {},
          "hasSkip": false
        },
{//可以有多个同上的信息,是正片的一集
}],
// 当前正在播放的剧集,格式同上
"epInfo": {
          "loaded": true, //表示正在播放的剧集
        },
"sections": [{
          "id": 38051,
          "title": "预告花絮",
          "type": 2,
          "epList": [{
              // 信息内容同上
          }]
...
```
### 2. 新番时间表
新番时间表请求url为`https://bangumi.bilibili.com/web_api/timeline_global`

返回json格式的信息,包含当前周到下周共14天的番剧详情.

```json
{
    "code": 0,
    "message": "success",
    "result": [{
        "date": "3-21",
        "date_ts": 1584720000,
        "day_of_week": 6,
        "is_today": 0,
        "seasons": [{
            "cover": "http://i0.hdslb.com/bfs/bangumi/image/94552aaa95b2785df3dbbbad2bb664d53d38a58f.png",
            "delay": 0,
            "ep_id": 307254,
            "favorites": 1543235,
            "follow": 0,
            "is_published": 1,
            "pub_index": "第8话",
            "pub_time": "00:05",
            "pub_ts": 1584720300,
            "season_id": 29325,
            "season_status": 13,
            "square_cover": "http://i0.hdslb.com/bfs/bangumi/image/d6b96118a865be0a88eb69f4ee7c455c82d4276e.jpg",
            "title": "某科学的超电磁炮T",
            "url": "https://www.bilibili.com/bangumi/play/ss29325"
        },
        {
            "cover": "下面略"
        }]
    },
    {
        "date": "4-2",
        "date_ts": 1584806400,
        "day_of_week": 7,
        "is_today": 0,
        "sessions": "后面就不写了......"
    }]
}
```

* 注意日期首位没有零.