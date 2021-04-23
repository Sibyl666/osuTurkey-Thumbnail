import os
import sys
import textwrap
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from oppai import *

from utils.crop import cropped_thumbnail
from utils.replay_parser import ReplayParser

load_dotenv()
apiKey = os.getenv("apiKey")


def getBeatmapFile(beatmap_id: str):
    response = requests.get("https://osu.ppy.sh/osu/" + beatmap_id)
    return response.content


def getBeatmapFromMd5(Md5: str) -> dict:
    response = requests.get("https://osu.ppy.sh/api/get_beatmaps", {
        "k": apiKey,
        "h": Md5,
    })

    return response.json()[0]


def getUserFromUsername(username: str) -> dict:
    response = requests.get("https://osu.ppy.sh/api/get_user", {
        "k": apiKey,
        "u": username,
        "type": "string",
    })

    return response.json()[0]


def getScore(user: str, mods: str, beatmapId) -> dict:
    response = requests.get("https://osu.ppy.sh/api/get_scores", {
        "k": apiKey,
        "u": user,
        "mods": mods,
        "b": beatmapId
    })

    return response.json()[0]


def getCover(beatmapsetId: int) -> Image:
    response = requests.get(f"https://assets.ppy.sh/beatmaps/{beatmapsetId}/covers/cover@2x.jpg?")

    return Image.open(BytesIO(response.content))


def getAvatar(userId: int, size: tuple = (222, 222)) -> Image:
    response = requests.get(f"https://a.ppy.sh/{userId}")
    avatarImage = Image.open(BytesIO(response.content)).convert("RGBA")

    return cropped_thumbnail(avatarImage, size)


def writeText(image: Image, fontSize: int, text: str, xy: tuple = (0, 0), anchor: str = "lm", fill: tuple = (0, 0, 0),
              center: bool = False, align: str = "center"):
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("Stuff/Gothic.ttf", fontSize)

    if center:
        width, height = image.size

        xy = (width / 2, height / 2)
        anchor = "mm"

    draw.multiline_text(xy, text, font=font, anchor=anchor, fill=fill, align="center")

    return image


def getTextSize(text: str, fontSize: int) -> tuple:
    font = ImageFont.truetype("Stuff/Gothic.ttf", fontSize)
    return font.getsize(text)


def main():
    replayInfo = ReplayParser(sys.argv[1])

    beatmapInfo = getBeatmapFromMd5(replayInfo.beatmap_md5)
    cover = cropped_thumbnail(getCover(beatmapInfo["beatmapset_id"]), (3200, 1800))

    template = Image.new("RGBA", (3200, 1800), color=("#ffffff"))
    templateMask = Image.open("Stuff/Masks/vsMask.png").convert("RGBA")
    avatarMask = Image.open("Stuff/Masks/AvatarMask.png").convert("L")

    template.paste(cover)
    template.paste(templateMask, (0, 0), templateMask)

    ######################################## First Player

    userInfo = getUserFromUsername(input("First username (Change spaces with '_'): "))
    userInfoSecond = getUserFromUsername(input("Second username (Change spaces with '_'): "))

    # Avatar
    avatar = getAvatar(userInfo["user_id"], (240, 240))
    template.paste(avatar, (300, 980), avatarMask.resize((240, 240)))

    # Username
    template = writeText(template, 140, userInfo["username"], (580, 1100))

    # Global
    template = writeText(template, 70, "Global", (300, 1280))
    template = writeText(template, 145, f"#{int(userInfo['pp_rank']):,}", (300, 1400))

    # Country
    template = writeText(template, 70, "Country", (300, 1520))
    template = writeText(template, 145, f"#{int(userInfo['pp_country_rank']):,}", (300, 1640))

    ########################################


    ######################################## Second Player
    avatar = getAvatar(userInfoSecond["user_id"], (240, 240))
    template.paste(avatar, (1850, 980), avatarMask.resize((240, 240)))

    # Username
    template = writeText(template, 140, userInfoSecond["username"], (2140, 1100))

    # Global
    template = writeText(template, 70, "Global", (1850, 1280))
    template = writeText(template, 145, f"#{int(userInfoSecond['pp_rank']):,}", (1850, 1400))

    # Country
    template = writeText(template, 70, "Country", (1850, 1520))
    template = writeText(template, 145, f"#{int(userInfoSecond['pp_country_rank']):,}", (1850, 1640))
    ########################################

    # Beatmap Title
    beatmapInfo["titleWrapped"] = "\n".join(textwrap.wrap(beatmapInfo["title"], 25))
    template = writeText(template, 200, beatmapInfo["titleWrapped"], (1600, 500), "mm", fill=(255, 255, 255))


    template.save("thumbnail.png")

    with open("text.txt", "w", encoding="utf-8") as file:
        file.write(f"""
# Title
{userInfo["username"]} & {userInfoSecond["username"]} - {beatmapInfo["title"]} [{beatmapInfo["version"]}]

# Description

Oyuncu: https://osu.ppy.sh/users/{userInfo["user_id"]}
Skin:

Oyuncu 2: https://osu.ppy.sh/users/{userInfoSecond["user_id"]}
Skin 2: 

Beatmap: https://osu.ppy.sh/beatmapsets/{beatmapInfo["beatmapset_id"]}#osu/{beatmapInfo["beatmap_id"]}
""")


if "__main__" == __name__:
    main()
