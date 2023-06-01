<div align="center">

# NoneBot Plugin R6s
## 本项目暂停开发，仓库将会归档直至下一次更新
## The development of this project is suspended, and the warehouse will be archived until the next update

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
  <img src="https://img.shields.io/badge/python-3.7.3+-blue.svg" alt="python">
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

|  指令  |          别名          | 可接受参数 | 功能                                                         |
| :----: | :--------------------: | ---------- | ------------------------------------------------------------ |
|  r6s   | 彩六，彩虹六号，r6，R6 | 昵称       | 查询玩家基本信息                                             |
| r6spro |      r6pro，R6pro      | 昵称       | 查询玩家进阶信息                                             |
| r6sops |      r6ops，R6ops      | 昵称       | 查询玩家干员信息                                             |
|  r6sp  |        r6p，R6p        | 昵称       | 查询玩家 ~~近期对战~~ 历史段位信息                           |
| r6sset |      r6set，R6set      | 昵称       | 设置玩家昵称，设置后其余指令可以不带昵称即查询已设置昵称信息 |

## 更新日志

### 0.4.2

- 增加玩家基本信息以及进阶信息数据:
  > 玩家基本信息: 更新玩家当前赛季非排以及当前赛季排位MMR分数  
  玩家进阶信息:   
  1.将非排和排位数据中MMR更新为当前赛季MMR  
  2.新增最高段位赛季数据 最高MMR和结束赛季时最终MMR 胜场以及负场
- 修复已知BUG:
  > 修复因玩家头像获取不到导致的出错  
  修复因干员头像获取不到导致的出错

> Thanks for [#6](https://github.com/abrahum/nonebot_plugin_r6s/pull/6)

### 0.4.1

- fix dependencies [#4](https://github.com/abrahum/nonebot_plugin_r6s/pull/4)

### 0.4.0

- 适配 Nonebot2-beta.1
- python3.7.3+ 与 nonebot2 保持一致

### 0.3.0

- 变更为使用图片回复，旧文字消息暂时停用（未来看情况作为可选）
- 添加 oop 中间件，为未来可能的其他数据来源提供便利
- 要求版本上升为 Python3.8 （还有人在用 3.7 以下? 不会吧? 不会吧? )

### 0.2.2

- ground 数据源失效，暂时完全切换回 r6scn ，部分无法查询问题会重现。*2021.05.24*

### 0.2.1

- 更换优先使用 ground 数据源，cn 数据源存在排位休闲数据错位，改名后数据长期未更新问题。
- ground 数据源乱码严重，目前无法识别干员数据和近期对战数据
- 已知 ground 数据源第一次使用会返回未更新数据，待研究解决（咕咕咕）
- 针对有 Ubi 账号未游玩 R6s 账号返回 Not Found

## 已知问题

- r6scn 不再更新数据

## 特别鸣谢

[nonebot/nonebot2](https://github.com/nonebot/nonebot2/)：简单好用，扩展性极强的 Bot 框架

[Mrs4s/go-cqhttp](https://github.com/Mrs4s/go-cqhttp)：更新迭代快如疯狗的 [OneBot](https://github.com/howmanybots/onebot/blob/master/README.md) Golang 原生实现

