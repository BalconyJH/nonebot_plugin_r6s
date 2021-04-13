<div align="center">

# NoneBot Plugin R6s

Rainbow Six Siege Players Searcher For Nonebot2

</div>

</div>

<p align="center">
  <a href="https://raw.githubusercontent.com/abrahum/nonebot-plugin-r6s/master/LICENSE">
    <img src="https://img.shields.io/github/license/abrahum/nonebot_plugin_r6s.svg" alt="license">
  </a>
  <a href="https://pypi.python.org/pypi/nonebot-plugin-r6s">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-r6s.svg" alt="pypi">
  </a>
  <img src="https://img.shields.io/badge/python-3.7+-blue.svg" alt="python">
</p>

## 使用方法

``` zsh
nb plugin install nonebot-plugin-r6s // or
pip install --upgrade nonebot-plugin-r6s
```
在 Nonebot2 入口文件（例如 bot.py ）增加：
``` python
nonebot.load_plugin("nonebot_plugin_r6s")
```

## 指令详解

|指令|别名|可接受参数|功能|
|:-:|:-:|--|---|
|r6s|彩六，彩虹六号，r6，R6|昵称|查询玩家基本信息|
|r6spro|r6pro，R6pro|昵称|查询玩家进阶信息|
|r6sops|r6ops，R6ops|昵称|查询玩家干员信息|
|r6sp|r6p，R6p|昵称|查询玩家近期对战信息|
|r6sset|r6set，R6set|昵称|设置玩家昵称，设置后其余指令可以不带昵称即查询已设置昵称信息|

## 更新日志

### 0.2.0-alpha.1

- 更换优先使用 ground 数据源，cn 数据源存在排位休闲数据错位，改名后数据长期未更新问题。
- ground 数据源乱码严重，目前无法识别干员数据和近期对战数据
- 已知 ground 数据源第一次使用会返回未更新数据，待研究解决（咕咕咕）

### 0.2.0-alpha.2

- 针对有 Ubi 账号未游玩 R6s 账号返回 Not Found

## 特别鸣谢

[nonebot/nonebot2](https://github.com/nonebot/nonebot2/)：简单好用，扩展性极强的 Bot 框架

[Mrs4s/go-cqhttp](https://github.com/Mrs4s/go-cqhttp)：更新迭代快如疯狗的 [OneBot](https://github.com/howmanybots/onebot/blob/master/README.md) Golang 原生实现

