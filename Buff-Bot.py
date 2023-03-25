import logging
import os
import shutil
import sys
import json

from steampy.client import SteamClient
from requests.exceptions import SSLError, ConnectTimeout
import requests
import time
from libs import FileUtils
import pickle

# format参考：E:/python27/Lib/logging/__init__.py
_LOG_NAME = '{script_name}_{date}.log'.format(
    script_name=os.path.basename(__file__),
    date=time.strftime('%Y%m%d', time.localtime()))
CUR_DIR = os.path.dirname(os.path.realpath(__file__))
_LOG_FILE = os.path.join(CUR_DIR, _LOG_NAME)
logging.basicConfig(filename=_LOG_FILE,
                    format='%(asctime)s:%(process)d:%(lineno)d:%(levelname)s:%(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.27',
}


def checkaccountstate(dev=False):
    if dev and os.path.exists('dev/buff_account.json'):
        logger.info('开发模式，使用本地账号')
        return json.loads(FileUtils.readfile('dev/buff_account.json'))['data']['nickname']
    else:
        response_json = requests.get('https://buff.163.com/account/api/user/info', headers=headers).json()
        if response_json['code'] == 'OK':
            if 'data' in response_json:
                if 'nickname' in response_json['data']:
                    return response_json['data']['nickname']
        logger.error('BUFF账户登录状态失效，请检查cookies.txt！')
        sys.exit()


def format_str(text: str, trade):
    for good in trade['goods_infos']:
        good_item = trade['goods_infos'][good]
        created_at_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(trade['created_at']))
        text = text.format(item_name=good_item['name'], steam_price=good_item['steam_price'],
                           steam_price_cny=good_item['steam_price_cny'], buyer_name=trade['bot_name'],
                           buyer_avatar=trade['bot_avatar'], order_time=created_at_time_str, game=good_item['game'],
                           good_icon=good_item['original_icon_url'])
    return text


def main():
    client = None
    development_mode = False
    os.system("title Buff-Bot https://github.com/jiajiaxd/Buff-Bot")
    first_run = False
    try:
        if not os.path.exists("config/config.json"):
            first_run = True
            shutil.copy("config/config.example.json", "config/config.json")
    except FileNotFoundError:
        logger.error("未检测到config.example.json，请前往GitHub进行下载，并保证文件和程序在同一目录下。")
        sys.exit()
    if not os.path.exists("config/cookies.txt"):
        first_run = True
        FileUtils.writefile("config/cookies.txt", "session=")
    if not os.path.exists("config/steamaccount.json"):
        first_run = True
        FileUtils.writefile("config/steamaccount.json", json.dumps({"steamid": "", "shared_secret": "",
                                                                    "identity_secret": "", "api_key": "",
                                                                    "steam_username": "", "steam_password": ""}))
    if first_run:
        logger.info("检测到首次运行，已为您生成配置文件，请按照README提示填写配置文件！")
        # logger.info('点击回车键继续...')
        # input()
    config = json.loads(FileUtils.readfile("config/config.json"))
    ignoredoffer = []
    if 'dev' in config and config['dev']:
        development_mode = True
    if development_mode:
        logger.info("开发者模式已开启")
    logger.info("正在准备登录至BUFF...")
    headers['Cookie'] = FileUtils.readfile('config/cookies.txt')
    logger.info("已检测到cookies，尝试登录")
    logger.info("已经登录至BUFF 用户名：" + checkaccountstate(dev=development_mode))

    if development_mode:
        logger.info("开发者模式已开启，跳过Steam登录")
    else:
        relog = False
        if not os.path.exists('steam_session.pkl'):
            logger.info("未检测到steam_session.pkl文件存在")
            relog = True
        else:
            logger.info("检测到缓存的steam_session.pkl文件存在，正在尝试登录")
            with open('steam_session.pkl', 'rb') as f:
                client = pickle.load(f)
                if json.loads(FileUtils.readfile('config/config.json'))['ignoreSSLError']:
                    logger.warning("警告：已经关闭SSL验证，账号可能存在安全问题")
                    client._session.verify = False
                    requests.packages.urllib3.disable_warnings()
                if client.is_session_alive():
                    logger.info("登录成功\n")
                else:
                    relog = True
        if relog:
            try:
                logger.info("正在登录Steam...")
                acc = json.loads(FileUtils.readfile('config/steamaccount.json'))
                client = SteamClient(acc.get('api_key'))
                if json.loads(FileUtils.readfile('config/config.json'))['ignoreSSLError']:
                    logger.warning("\n警告：已经关闭SSL验证，账号可能存在安全问题\n")
                    client._session.verify = False
                    requests.packages.urllib3.disable_warnings()
                SteamClient.login(client, acc.get('steam_username'), acc.get('steam_password'),
                                  'config/steamaccount.json')
                with open('steam_session.pkl', 'wb') as f:
                    pickle.dump(client, f)
                logger.info("登录完成！已经自动缓存session.\n")
            except FileNotFoundError:
                logger.error('未检测到steamaccount.json，请添加到steamaccount.json后再进行操作！')
                sys.exit()
            except (ConnectTimeout, TimeoutError):
                logger.error('\n网络错误！请通过修改hosts/使用代理等方法代理Python解决问题。\n'
                             '注意：使用游戏加速器并不能解决问题。请尝试使用Proxifier及其类似软件代理Python.exe解决。')
                sys.exit()
            except SSLError:
                logger.error('登录失败。SSL证书验证错误！'
                             '若您确定网络环境安全，可尝试将config.json中的ignoreSSLError设置为false\n')
                sys.exit()

    while True:
        try:
            logger.info("正在检查Steam账户登录状态...")
            if not development_mode:
                if not client.is_session_alive():
                    logger.error("Steam登录状态失效！程序退出...")
                    sys.exit()
            logger.info("Steam账户状态正常")
            logger.info("正在进行待发货/待收货饰品检查...")
            checkaccountstate(dev=development_mode)
            if development_mode and os.path.exists("dev/message_notification.json"):
                logger.info("开发者模式已开启，使用本地消息通知文件")
                to_deliver_order = json.loads(FileUtils.readfile("dev/message_notification.json")).get('data', {}).get(
                    'to_deliver_order', {})
            else:
                response = requests.get("https://buff.163.com/api/message/notification", headers=headers)
                to_deliver_order = json.loads(response.text).get('data', {}).get('to_deliver_order', {})
            if int(to_deliver_order.get('csgo', 0)) != 0:
                logger.info("CSGO待发货：" + str(int(to_deliver_order.get('csgo', 0))) + "个")
            if development_mode and os.path.exists("dev/steam_trade.json"):
                logger.info("开发者模式已开启，使用本地待发货文件")
                trade = json.loads(FileUtils.readfile("dev/steam_trade.json")).get('data', [])
            else:
                response = requests.get("https://buff.163.com/api/market/steam_trade", headers=headers)
                trade = json.loads(response.text).get('data', [])
            logger.info("查找到" + str(len(trade)) + "个待处理的交易报价请求！")
            try:
                if len(trade) != 0:
                    i = 0
                    for go in trade:
                        i += 1
                        offerid = go.get('tradeofferid', "")
                        logger.info("正在处理第" + str(i) + "个交易报价 报价ID" + str(offerid))
                        if not offerid:
                            continue
                        if offerid not in ignoredoffer:
                            try:
                                logger.info("正在接受报价...")
                                if development_mode:
                                    logger.info("开发者模式已开启，跳过接受报价")
                                else:
                                    client.accept_trade_offer(offerid)
                                ignoredoffer.append(offerid)
                                logger.info("接受完成！已经将此交易报价加入忽略名单！\n")
                                if 'sell_notification' in config:
                                    logger.info("{title}:{body}".format(
                                        title=format_str(config['sell_notification']['title'], go),
                                        body=format_str(config['sell_notification']['body'], go),
                                    ))
                            except Exception as e:
                                logger.error(e, exc_info=True)
                                logger.info("出现错误，稍后再试！")
                        else:
                            logger.info("该报价已经被处理过，跳过.\n")
                    logger.info("暂无BUFF报价请求.将在180秒后再次检查BUFF交易信息！\n")
                else:
                    logger.info("暂无BUFF报价请求.将在180秒后再次检查BUFF交易信息！\n")
            except KeyboardInterrupt:
                logger.info("用户停止，程序退出...")
                sys.exit()
            except Exception as e:
                logger.error(e, exc_info=True)
                logger.info("出现错误，稍后再试！")
            time.sleep(180)
        except KeyboardInterrupt:
            logger.info("用户停止，程序退出...")
            sys.exit()


if __name__ == '__main__':
    main()
