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

## 特别鸣谢

[nonebot/nonebot2](https://github.com/nonebot/nonebot2/)：简单好用，扩展性极强的 Bot 框架

[Mrs4s/go-cqhttp](https://github.com/Mrs4s/go-cqhttp)：更新迭代快如疯狗的 [OneBot](https://github.com/howmanybots/onebot/blob/master/README.md) Golang 原生实现

