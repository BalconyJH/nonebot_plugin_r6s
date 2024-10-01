from arclet.alconna import Alconna, Subcommand, Args, CommandMeta
from nonebot_plugin_alconna import on_alconna

r6s = on_alconna(
    Alconna(
        "r6s",
        Subcommand(
            "-b|--bind",
            Args["email", str]["password", str]["group", str],
            help_text="绑定登录信息到指定群组",
        ),
        Subcommand("-u|--unbind", Args["group", str], help_text="解绑登录信息"),
        Subcommand(
            "-s|--search",
            Args["username", str]["platform?", str],
            help_text="搜索玩家信息, 注意这里的用户名是育碧账号用户名而不是游戏内昵称",
        ),
        Subcommand(
            "-p|--protocol",
            help_text="显示用户协议",
        ),
        meta=CommandMeta(
            description="Rainbow Six Siege 玩家数据查询",
            usage=(
                "/r6s -b|--bind <email> <password> <group>\n"
                "/r6s -u|--unbind <group>\n"
                "/r6s -s|--search <username> [platform]"
            ),
            example=(
                "/r6s -b 123@gmail.com 123456 group1\n"
                "/r6s -u group1\n"
                "/r6s -s Juefdsfvcdvbd uplay"
            ),
        ),
    ),
    use_cmd_start=True,
    priority=5,
    block=True,
)
