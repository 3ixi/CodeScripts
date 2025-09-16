#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
瓜瓜粉丝俱乐部小程序签到脚本
脚本作者：3iXi
创建时间：2025/09/16
！！此脚本需要配合iPad协议服务使用！！
小程序：瓜瓜粉丝俱乐部
搜不到就在微信点这个链接：#小程序://瓜瓜粉丝俱乐部/elCKovIOnboDMDu
"""

import time
import json
from datetime import datetime
from urllib.parse import quote
from typing import Optional

try:
    import httpx
except ImportError:
    print("错误: 需要安装 httpx[http2] 依赖")
    exit(1)

import getCode


class YoukeSignin:
    """瓜瓜粉丝俱乐部小程序签到类"""

    def __init__(self):
        """初始化签到客户端"""
        self.base_url = "https://smp-api.iyouke.com"
        self.app_id = "wx05b4bfe1edf7efe5"

        self.client = httpx.Client(http2=True, timeout=30.0, verify=False)

        self.headers = {
            "host": "smp-api.iyouke.com",
            "xy-extra-data": "appid=wx05b4bfe1edf7efe5;version=2.13.18;envVersion=release;senceId=1256",
            "appid": "wx05b4bfe1edf7efe5",
            "envversion": "release",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2541022) XWEB/16467",
            "xweb_xhr": "1",
            "content-type": "application/json",
            "version": "2.13.18",
            "accept": "*/*",
            "sec-fetch-site": "cross-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://servicewechat.com/wx05b4bfe1edf7efe5/13/page-frame.html",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9",
            "priority": "u=1, i"
        }

        self.access_token = None
        self.user_id = None

    def login(self, code: str) -> bool:
        """
        用户登录

        Args:
            code (str): 微信小程序登录code

        Returns:
            bool: 登录是否成功
        """
        payload = {
            "appType": 1,
            "principal": code
        }

        url = f"{self.base_url}/dtapi/appLogin"
        payload_str = json.dumps(payload, separators=(',', ':'))

        try:
            headers = self.headers.copy()
            headers["content-length"] = str(len(payload_str))
            
            response = self.client.post(url, content=payload_str, headers=headers)
            response.raise_for_status()

            content_length = response.headers.get('content-length')
            if content_length == '0':
                print("登录失败：请检查值是否正确")
                return False

            data = response.json()
            self.access_token = data.get("access_token")
            self.user_id = data.get("userId")
            
            if self.access_token and self.user_id:
                self.headers["authorization"] = f"bearer{self.access_token}"
                print(f"登录成功，用户ID{self.user_id}")
                return True
            else:
                print("登录失败：未获取到access_token或userId")
                return False

        except Exception as e:
            print(f"登录请求失败: {e}")
            return False

    def sign_in(self) -> bool:
        """
        提交签到

        Returns:
            bool: 签到是否成功
        """
        if not self.access_token:
            print("未获取到access_token，无法签到")
            return False

        today = datetime.now().strftime("%Y/%m/%d")
        encoded_date = quote(today)
        
        url = f"{self.base_url}/dtapi/pointsSign/user/sign?date={encoded_date}"

        try:
            response = self.client.get(url, headers=self.headers)
            response.raise_for_status()

            content_length = response.headers.get('content-length')
            if content_length == '0':
                print("签到失败：服务器返回空响应")
                return False

            data = response.json()
            if data.get('error') == 0:
                sign_reward = data.get('data', {}).get('signReward', 0)
                extra_sign_reward = data.get('data', {}).get('extraSignReward', 0)
                
                print(f"签到成功，获得积分+{sign_reward}")
                if extra_sign_reward > 0:
                    print(f"获得额外积分+{extra_sign_reward}")
                return True
            else:
                error_msg = data.get('errorMsg', '未知错误')
                print(f"签到失败：{error_msg}")
                return False

        except Exception as e:
            print(f"签到请求失败: {e}")
            return False

    def get_points_info(self) -> Optional[dict]:
        """
        查询用户积分

        Returns:
            Optional[dict]: 积分信息，None表示查询失败
        """
        if not self.access_token:
            print("未获取到access_token，无法查询积分")
            return None

        url = f"{self.base_url}/dtapi/pointsSign/user/pointsInfo/query"

        try:
            response = self.client.get(url, headers=self.headers)
            response.raise_for_status()

            content_length = response.headers.get('content-length')
            if content_length == '0':
                print("查询积分失败：服务器返回空响应")
                return None

            data = response.json()
            if data.get('error') == 0:
                points_data = data.get('data', {})
                points_nums = points_data.get('pointsNums', 0)
                series_days = points_data.get('seriesDays', 0)
                
                print(f"已连续签到{series_days}天，当前有{points_nums}积分")
                return points_data
            else:
                error_msg = data.get('errorMsg', '未知错误')
                print(f"查询积分失败：{error_msg}")
                return None

        except Exception as e:
            print(f"查询积分请求失败: {e}")
            return None

    def process_account(self, nick_name: str, code: str) -> bool:
        """
        处理单个账号的签到流程

        Args:
            nick_name (str): 账号昵称
            code (str): 微信小程序登录code

        Returns:
            bool: 是否处理成功
        """
        print(f"\n开始处理账号: {nick_name}")

        # 1. 登录
        if not self.login(code):
            print(f"账号 {nick_name} 登录失败")
            return False

        # 2. 提交签到
        if not self.sign_in():
            print(f"账号 {nick_name} 签到失败")
            return False

        # 3. 查询积分信息
        points_info = self.get_points_info()
        if points_info is None:
            print(f"账号 {nick_name} 查询积分失败")
            return False

        return True

    def close(self):
        """关闭HTTP客户端"""
        self.client.close()

    def reset_session(self):
        """
        重置/清理会话数据
        """
        try:
            self.client.close()
        except Exception:
            pass

        self.client = httpx.Client(http2=True, timeout=30.0, verify=False)

        self.access_token = None
        self.user_id = None

        if "authorization" in self.headers:
            try:
                del self.headers["authorization"]
            except KeyError:
                pass

        print("已清理会话数据，准备下一个账号...")


def main():
    """主函数"""
    try:
        print("正在获取登录Code...")
        app_id = "wx05b4bfe1edf7efe5"
        codes = getCode.get_wechat_codes(app_id)

        if not codes:
            print("未获取到任何在线账号的Code")
            return

        print(f"获取到 {len(codes)} 个账号的Code")

        signin = YoukeSignin()

        try:
            for i, (nick_name, code) in enumerate(codes.items(), 1):
                print(f"\n{'='*50}")
                print(f"处理第 {i}/{len(codes)} 个账号")
                print(f"{'='*50}")

                try:
                    signin.process_account(nick_name, code)
                except Exception as e:
                    print(f"处理账号 {nick_name} 时发生错误: {e}")

                signin.reset_session()

                if i < len(codes):
                    print(f"等待2秒后处理下一个账号...")
                    time.sleep(2)

        finally:
            signin.close()

        print("\n所有账号处理完成")

    except Exception as e:
        print(f"脚本执行失败: {e}")


if __name__ == "__main__":
    main()