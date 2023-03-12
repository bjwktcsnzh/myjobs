# -*- coding: UTF-8 -*-
import time
from collections.abc import Callable
from datetime import datetime

import os
import subprocess
import schedule as schedule
import requests
from notifypy import Notify
import bilibili_api.live
from bilibili_api import sync
import urllib.request


def _log(msg, level="INFO"):
    m = '[' + level + "][" + str(datetime.today().strftime('%Y-%m-%d %H:%M:%S')) + "] " + msg
    print(m)
    with open(
            ".logs/" + str(datetime.today().strftime('%Y-%m-%d')) + ".txt",
            mode="a",
            encoding="utf-8"
    ) as f:
        f.write(m + "\n")
        f.flush()


def _notify(**kwargs):
    _log("notify : " + str(kwargs))
    n = Notify()
    n.application_name = "myjobs.py"
    if kwargs.get("title") is not None:
        n.title = kwargs["title"]
    if kwargs.get("icon") is not None:
        n.icon = kwargs["icon"]
    if kwargs.get("message") is not None:
        n.message = kwargs["message"]
    else:
        n.message = ""
    n.send()


def _download(url: str) -> str:
    with open(".download/" + url.split("/")[-1], mode="bw", ) as f:
        _log("download : " + f.name)
        f.write(urllib.request.urlopen(url).read())
        f.flush()
        return f.name


_network_status = False


def job_check_network_status():
    """
    检查网络状态的任务
    """
    global _network_status
    with open(os.devnull) as FNULL:
        res = subprocess.run("ping baidu.com -n 1 -w 4000", stdout=FNULL)
    new_network_status = True if res.returncode == 0 else False
    if _network_status != new_network_status:
        _log("Network status changed : " + str(_network_status) + " -> " + str(new_network_status))
    _network_status = new_network_status


_bilibili_live_room_status = {}


async def job_check_bilibili_live():
    """
    bilibili开播提醒任务。
    """

    async def checkRoom(_id):
        """
        检查房间是否开播，并在开播时提醒
        :param _id: 房间号
        """
        old_status = _bilibili_live_room_status.get(_id)
        if old_status is None:
            old_status = 0
        room = bilibili_api.live.LiveRoom(_id)
        try:
            play_info = await room.get_room_play_info()
            # _log("play_info of " + str(_id) + " : " + str(play_info))
        except:
            _log("failed on get_room_play_info : id=" + str(_id), level="ERROR")
            return
        new_status = play_info["live_status"]
        _bilibili_live_room_status[_id] = new_status
        if old_status != 1 and new_status == 1:
            info = await room.get_room_info()
            _notify(
                title="开播提醒: " + info["anchor_info"]["base_info"]["uname"],
                message=info["room_info"]["title"],
                icon=_download(info["room_info"]["cover"])
            )
        elif old_status == 1 and new_status != 1:
            info = await room.get_room_info()
            _log(info["anchor_info"]["base_info"]["uname"] + " 停播了")

    for r in [
        7531557,  # 未明子
        11178526,  # 张正午
        26671817,  # 主义主义工益_Official
        8554748,  # 五年四班劳动委员
        27339552,  # 星杭工益
        # 650, #一米八的坤儿
        # 26998291,  # 鼠鼠文学
    ]:
        if _network_status:
            await checkRoom(r)
    # _log("Check bilibili live complete . bilibili_live_room_status=" + str(bilibili_live_room_status))
    pass


if __name__ == "__main__":
    _log("Start working...")
    # schedule.every(10).minutes.do(log)
    schedule.every(4).hours.do(lambda: _log("I'm working..."))
    schedule.every().day.at("20:30").do(lambda: _notify(title="写日志"))

    schedule.every(5).seconds.do(lambda: job_check_network_status())
    schedule.every(60).seconds.do(lambda: sync(job_check_bilibili_live()))


    def workday_job(at, func: Callable):
        schedule.every().monday.at(at).do(func)
        schedule.every().tuesday.at(at).do(func)
        schedule.every().wednesday.at(at).do(func)
        schedule.every().thursday.at(at).do(func)
        schedule.every().friday.at(at).do(func)


    workday_job("11:25", lambda: _notify(title="吃饭"))

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except BaseException as err:
        _notify(
            title="出错了！！！！"
        )
        raise err
