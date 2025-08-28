#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
康师傅畅饮社小程序签到脚本
脚本作者：3iXi
创建时间：2025/08/28
！！此脚本需要配合iPad协议服务使用！！
小程序：康师傅畅饮社
"""

import time
import json
from typing import Optional

try:
    import httpx
except ImportError:
    print("错误: 需要安装 httpx[http2] 依赖")
    exit(1)

import getCode


class BiqrSignin:
    """康师傅畅饮社小程序签到类"""

    def __init__(self):
        """初始化签到客户端"""
        self.base_url = "https://club.biqr.cn"
        self.login_url = "https://nclub.gdshcm.com"
        self.app_id = "wx54f3e6a00f7973a7"

        self.client = httpx.Client(http2=True, timeout=30.0, verify=False)

        self.headers = {
            "Host": "club.biqr.cn",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254061a) XWEB/16203",
            "Accept": "application/json, text/plain, */*",
            "xweb_xhr": "1",
            "Content-Type": "application/x-www-form-urlencoded;",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://servicewechat.com/wx54f3e6a00f7973a7/720/page-frame.html",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }

        self.login_headers = {
            "Host": "nclub.gdshcm.com",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254061a) XWEB/16203",
            "Accept": "application/json, text/plain, */*",
            "xweb_xhr": "1",
            "Content-Type": "application/json; charset=UTF-8",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://servicewechat.com/wx54f3e6a00f7973a7/720/page-frame.html",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }

        self.token = None
        self.nickname = None
        self.initial_integral = None

    def login(self, code: str) -> bool:
        """
        用户登录

        Args:
            code (str): 微信小程序登录code

        Returns:
            bool: 登录是否成功
        """
        payload = {
            "code": code,
            "inviterId": "",
            "inviterType": "",
            "inviterMatchUserId": "",
            "spUrl": None
        }

        url = f"{self.login_url}/pro/whale-member/api/login/login"

        try:
            response = self.client.post(url, json=payload, headers=self.login_headers)
            response.raise_for_status()

            data = response.json()
            if data.get("code") == 0:
                self.token = data.get("data", {}).get("token")
                member_info = data.get("data", {}).get("member", {})
                self.nickname = member_info.get("nickname", "未知用户")
                self.initial_integral = member_info.get("totalIntegral", 0)
                
                if self.token:
                    self.headers["Token"] = self.token
                    print(f"{self.nickname}登录成功，开始准备签到...")
                    return True
                else:
                    print("登录失败：当前账号未授权小程序，请手动进入小程序登录一次")
                    return False
            else:
                print(f"登录失败：{data.get('msg', '未知错误')}")
                return False

        except Exception as e:
            print(f"登录请求失败: {e}")
            return False

    def check_signin_status(self) -> Optional[dict]:
        """
        检查签到状态

        Returns:
            Optional[dict]: 签到状态信息，None表示检查失败
        """
        if not self.token:
            print("未获取到token，无法检查签到状态")
            return None

        url = f"{self.base_url}/api/signIn/integralSignInList"
        payload = f"token={self.token}"

        try:
            headers = self.headers.copy()
            headers["Content-Length"] = str(len(payload))
            
            response = self.client.post(url, data=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data.get('code') == 0:
                sign_data = data.get('data', {})
                sign_is = sign_data.get('signIs', False)
                continuous = sign_data.get('continuous', 0)
                
                status_text = "已签到" if sign_is else "未签到"
                print(f"今日{status_text}，已连续签到{continuous}天")
                return sign_data
            else:
                print(f"检查签到状态失败：{data.get('msg', '未知错误')}")
                return None

        except Exception as e:
            print(f"检查签到状态请求失败: {e}")
            return None

    def submit_signin(self) -> bool:
        """
        提交签到

        Returns:
            bool: 签到是否成功
        """
        if not self.token:
            print("未获取到token，无法签到")
            return False

        url = f"{self.base_url}/api/signIn/integralSignIn"
        payload = "{}"

        try:
            headers = self.headers.copy()
            headers["Content-Length"] = str(len(payload))
            
            response = self.client.post(url, data=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data.get('code') == 0:
                msg = data.get('msg', '签到成功')
                print(msg)
                return True
            else:
                print(f"签到失败：{data.get('msg', '未知错误')}")
                return False

        except Exception as e:
            print(f"签到请求失败: {e}")
            return False

    def check_subscribe_status(self) -> Optional[bool]:
        """
        检查订阅状态

        Returns:
            Optional[bool]: True=已订阅, False=未订阅, None=检查失败
        """
        if not self.token:
            print("未获取到token，无法检查订阅状态")
            return None

        url = f"{self.base_url}/api/integral/subscribeStatus"
        payload = f"token={self.token}"

        try:
            headers = self.headers.copy()
            headers["Content-Length"] = str(len(payload))
            
            response = self.client.post(url, data=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data.get('code') == 0:
                is_subscribed = data.get('data', True)
                return is_subscribed
            else:
                print(f"检查订阅状态失败：{data.get('msg', '未知错误')}")
                return None

        except Exception as e:
            print(f"检查订阅状态请求失败: {e}")
            return None

    def submit_subscribe(self) -> bool:
        """
        提交订阅任务

        Returns:
            bool: 订阅是否成功
        """
        if not self.token:
            print("未获取到token，无法提交订阅")
            return False

        url = f"{self.base_url}/api/integral/subscribeMessage"
        payload = "page=%2F25teaAlliance%2Fpages%2Findex&lat=0.00&lng=0.00&miniprogramState=formal"

        try:
            headers = self.headers.copy()
            headers["Content-Length"] = str(len(payload))
            
            response = self.client.post(url, data=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data.get('code') == 0:
                print('"首次订阅小程序"任务完成')
                return True
            else:
                print(f"订阅任务失败：{data.get('msg', '未知错误')}")
                return False

        except Exception as e:
            print(f"订阅任务请求失败: {e}")
            return False

    def get_member_info(self) -> Optional[dict]:
        """
        获取会员信息

        Returns:
            Optional[dict]: 会员信息，None表示获取失败
        """
        if not self.token:
            print("未获取到token，无法获取会员信息")
            return None

        url = f"{self.login_url}/pro/whale-member/api/member/getMemberInfo?token={self.token}"

        headers = {
            "Host": "nclub.gdshcm.com",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254061a) XWEB/16203",
            "Accept": "application/json, text/plain, */*",
            "xweb_xhr": "1",
            "Content-Type": "application/json",
            "Token": self.token,
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://servicewechat.com/wx54f3e6a00f7973a7/720/page-frame.html",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }

        try:
            response = self.client.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data.get('code') == 0:
                return data.get('data', {})
            else:
                print(f"获取会员信息失败：{data.get('msg', '未知错误')}")
                return None

        except Exception as e:
            print(f"获取会员信息请求失败: {e}")
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

        # 2. 检查签到状态
        sign_status = self.check_signin_status()
        if sign_status is None:
            print(f"账号 {nick_name} 检查签到状态失败")
            return False

        # 3. 如果未签到则提交签到
        if not sign_status.get('signIs', False):
            if not self.submit_signin():
                print(f"账号 {nick_name} 签到失败")
                return False

        # 4. 检查订阅状态
        subscribe_status = self.check_subscribe_status()
        if subscribe_status is None:
            print(f"账号 {nick_name} 检查订阅状态失败")
            return False

        # 5. 如果未订阅则提交订阅
        if not subscribe_status:
            if not self.submit_subscribe():
                print(f"账号 {nick_name} 订阅小程序失败")
                return False

        # 6. 获取最新积分信息
        member_info = self.get_member_info()
        if member_info:
            current_integral = member_info.get('totalIntegral', 0)
            today_integral = current_integral - self.initial_integral
            print(f"今日获得{today_integral}积分，当前有{current_integral}积分")

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

        self.token = None
        self.nickname = None
        self.initial_integral = None

        if "Token" in self.headers:
            try:
                del self.headers["Token"]
            except KeyError:
                pass

        print("已清理会话数据，准备下一个账号...")


def main():
    """主函数"""
    try:
        print("正在获取登录Code...")
        app_id = "wx54f3e6a00f7973a7"
        codes = getCode.get_wechat_codes(app_id)

        if not codes:
            print("未获取到任何在线账号的Code")
            return

        print(f"获取到 {len(codes)} 个账号的Code")

        signin = BiqrSignin()

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
