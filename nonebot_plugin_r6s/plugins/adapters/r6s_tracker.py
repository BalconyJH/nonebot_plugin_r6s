import asyncio
from io import BytesIO

import PIL
import aiohttp
from PIL import Image as IMG
from PIL.Image import Image
from lxml import etree
from tqdm import tqdm

proxy = 'http://127.0.0.1:10809'


async def download_image_async(url: str, proxy=proxy) -> Image:
    """异步下载图片。

    Args:
        url (str): 图片的 URL。
        proxy (str): HTTP 代理地址。

    Returns:
        PIL.Image.Image: 表示下载的图片。
    """
    try:
        # 使用 aiohttp 发起 HTTP 请求
        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy) as response:
                total_size = int(response.headers.get('content-length', 0))
                block_size = 1024

                progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True,
                                    desc=url)
                img_bytes = BytesIO()
                while True:
                    chunk = await response.content.read(block_size)
                    if not chunk:
                        break
                    progress_bar.update(len(chunk))
                    img_bytes.write(chunk)
                # 将 BytesIO 对象的读取位置移到开头
                img_bytes.seek(0)
                img = IMG.open(img_bytes)
                progress_bar.close()

                return img
    except (aiohttp.ClientError, PIL.UnidentifiedImageError) as e:
        pass

async def fetch(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/110.0.0.0"
                      "Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            return await resp.text()


async def get_user_basic_info(processed_data):
    html_data = etree.HTML(processed_data)
    profile_div = html_data.xpath('//*[@id="profile"]')[0]

    avatar_image = await download_image_async(profile_div.xpath(
        '//div[contains(@class, "trn-profile-header__avatar")]/img/@src'
    )[0])
    nickname = profile_div.xpath(
        '//*[@class="trn-profile-header__title"]/span[@class="trn-profile-header__name"]/text()'
    )[0].strip()


async def get_user_info(default_data):
    html_data = etree.HTML(default_data)
    profile_div = html_data.xpath('//*[@id="profile"]')[0]

    avatar_url = profile_div.xpath(
        '//div[contains(@class, "trn-profile-header__avatar")]/img/@src'
    )[0]
    user_id = profile_div.xpath(
        '//*[@class="trn-profile-header__title"]/span[@class="trn-profile-header__name"]/text()'
    )[0].strip()

    user_data = [
        {
            "avatar_url": await download_image_async(avatar_url)
        },
        {
            "user_id": user_id,
        }
    ]
    content_div = profile_div.xpath(
        'div[contains(@class, "trn-scont")]/div[contains(@class, "trn-scont__content")]'
    )[0]
    overall_div = content_div.xpath(
        'div[contains(@class, "trn-scont__content") and contains(@class, "trn-card")]'
    )[0]
    defstat_light_divs = overall_div.xpath(
        '//div[contains(@class, "trn-card--light")]/div[@class="trn-defstats-flex"]/div[contains(@class, '
        '"trn-defstat") and not(contains(@class, "top-operators"))]'
    )
    #
    user_data_array = [
        {
            defstat.xpath(
                '(./div//div[@class="trn-defstat__name"] | ./div[@class="trn-defstat__name"])/text()'
            )[0]
            .strip(): defstat.xpath(
                '(./div//div[@class="trn-defstat__value-stylized"] | ./div['
                '@class="trn-defstat__value-stylized"])/text()'
            )[0]
            .strip()
        }
        for defstat in defstat_light_divs
    ]
    print(user_data_array)
    defstat_dark_divs = overall_div.xpath(
        './/div[@class="trn-card__content"]/div[contains(@class, "trn-defstats")]/div[contains(@class, "trn-defstat")]'
    )

    # [{'avatar_url': 'https://ubisoft-avatars.akamaized.net/4f3faa88-568b-475c-a382-a986a2181cb7/default_256_256.png', 'user_id': 'Juelee.PIG'}]
    # [{'Best MMR': '4,159'}, {'Level': '258'}, {'Avg Seasonal MMR': '3,444'}]

    # playtime = defstat_dark_divs['playtime']
    user_data_array.extend(
        {
            "label": defstat.xpath('div[@class="trn-defstat__name"]/text()')[0].strip(),
            "value": defstat.xpath('div[@class="trn-defstat__value"]/text()')[0].strip()
        } for defstat in defstat_dark_divs
    )
    print(user_data_array)

    defstat_general_divs = overall_div.xpath(
        'following-sibling::div[1]//div[contains(@class, "trn-defstats")]/div[contains(@class, "trn-defstat") and '
        'not(contains(@class, "disabled"))]')
    user_data_array.extend(
        {
            "label": defstat.xpath('div[@class="trn-defstat__name"]/text()')[
                0
            ].strip(),
            "value": defstat.xpath('div[@class="trn-defstat__value"]/text()')[
                0
            ].strip(),
        }
        for defstat in defstat_general_divs
    )
    return user_data_array


#
#
# def get_season_data(season_data):
#     season_data_obj = {}
#     tspan_pattern = r'^([+-]?\d*)\s*([a-zA-Z\s]*)\s*([\d,]*)\s*([+-]?\d*)$'
#
#     html_data = etree.HTML(season_data)
#     profile_div = html_data.xpath('//*[@id="profile"]')[0]
#
#     season_card_divs = profile_div.xpath(
#         'div[contains(@class, "trn-scont")]/div[contains(@class, "trn-scont__content")]' +
#         '/div[@class="trn-card"]')
#     season_card_divs = season_card_divs[0:3]
#
#     for season_card_div in season_card_divs:
#         season_data = {}
#         season_name = \
#             season_card_div.xpath('div[@class="trn-card__header"]/h2[@class="trn-card__header-title"]/text()')[
#                 0].strip()
#
#         seasons = season_card_div.xpath('div[@class="r6-season-list"]/div[@class="r6-season"]')
#
#         for season in seasons:
#             if (
#                 season.xpath(
#                     'div[@class="r6-season__info"]/div[@class="r6-season__region"]/span/text()'
#                 )[0]
#                 .strip()
#                 .upper()
#                 != "RANKED"
#             ):
#                 continue
#             if matches := re.match(
#                 tspan_pattern,
#                 " ".join(
#                     season.xpath('div[@class="r6-season__info"]//tspan/text()')
#                 ),
#             ):
#                 season_data["sub_score"] = matches[1]
#                     # season_data["level"] = matches.group(2).strip()
#                     # season_data["current_score"] = matches.group(3).replace(",", "")
#                 season_data["add_score"] = matches[4]
#
#             season_defstats = season.xpath(
#                 'div[@class="r6-season__stats"]/div[contains(@class, "trn-defstats")]/div[@class="trn-defstat"]')
#             for defstat in season_defstats:
#                 defstat_name = defstat.xpath('div[@class="trn-defstat__name"]/text()')[0].strip()
#                 if defstat_name.upper() in ["K/D", "KILLS/MATCH", "WIN %"]:
#                     season_data[defstat_name] = defstat.xpath('div[@class="trn-defstat__value"]/text()')[0].strip()
#
#             # mmr
#             season_mmr_value = season_defstats[-2].xpath('div[@class="trn-defstat__value"]/text()')[0].strip()
#             season_data["MMR"] = season_mmr_value
#
#             # max mmr
#             season_max_mmr_value = season_defstats[-1].xpath('div[@class="trn-defstat__value"]/text()')[0].strip()
#             season_data["Max MMR"] = season_max_mmr_value
#         season_data_obj[season_name] = season_data
#
#     return season_data_obj


async def main():
    user_id = "Juelee.PIG"
    url_list = [
        f"https://r6.tracker.network/profile/pc/{user_id}",
        f"https://r6.tracker.network/profile/pc/{user_id}/seasons",
    ]
    tasks = [asyncio.create_task(fetch(url)) for url in url_list]
    results = await asyncio.gather(*tasks)

    await get_user_info(results[0])
    # default_data = get_default_data(results[0])
    # season_data = get_season_data(results[1])

    # print({
    #     "default": default_data,
    #     "season": season_data
    # })


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(main())
