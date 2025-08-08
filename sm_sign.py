#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SM广场小程序签到脚本
脚本作者：3iXi
创建时间：2025/07/28
！！此脚本需要配合iPad协议服务使用！！
小程序：成都SM广场、SM晋江国际广场、SM扬州、厦门SM商业城、重庆SM城市广场
"""

import time
import json
from typing import Optional, Dict

MALL_CONFIG: Dict[str, int] = {
    "成都": 11544,
    "晋江": 12135,
    "扬州": 12540,
    "厦门": 11086,
    "重庆": 12305
}

SELECTED_MALL = "成都"  # 在这里修改商场名称，必须是上面字典中的城市名

try:
    import httpx
except ImportError:
    print("错误: 需要安装 httpx[http2] 依赖")
    exit(1)

import getCode


class SmSignin:
    """成都SM广场小程序签到类"""

    def __init__(self):
        """初始化签到客户端"""
        self.base_url = "https://m.mallcoo.cn"
        self.app_id = "wx383a677b99e64655"
        
        if SELECTED_MALL not in MALL_CONFIG:
            raise ValueError(f"错误：选择的商场 '{SELECTED_MALL}' 无效。请在脚本开头的 SELECTED_MALL 变量中设置正确的商场名称。")
        self.mall_id = MALL_CONFIG[SELECTED_MALL]
        print(f"当前选择的商场：{SELECTED_MALL}SM广场（ID: {self.mall_id}）")

        self.client = httpx.Client(http2=True, timeout=30.0, verify=False)

        self.headers = {
            "host": "m.mallcoo.cn",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2540615) XWEB/16133",
            "xweb_xhr": "1",
            "content-type": "application/json",
            "accept": "*/*",
            "referer": "https://servicewechat.com/wx383a677b99e64655/15/page-frame.html",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9"
        }

        self.project_id = None
        self.token = None

    def get_project_config_id(self) -> bool:
        """
        获取小程序的接口项目ID

        Returns:
            bool: 是否获取成功
        """
        payload = {
            "MallID": self.mall_id,
            "Header": {
                "Token": None,
                "systemInfo": {
                    "model": "microsoft",
                    "SDKVersion": "3.8.10",
                    "system": "Windows 10 x64",
                    "version": "4.0.6.21",
                    "miniVersion": "DZ.2.5.64.1.SM.24"
                }
            }
        }

        url = f"{self.base_url}/api/home/Mall/GetProjectConfigIDStandard"
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))

        try:
            response = self.client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("m") == 1:
                self.project_id = data.get("d")
                return True
            else:
                print(f"获取项目ID失败：{data.get('e', '未知错误')}")
                return False

        except Exception as e:
            print(f"获取项目ID请求失败: {e}")
            return False

    def login(self, code: str) -> bool:
        """
        用户登录

        Args:
            code (str): 微信小程序登录code

        Returns:
            bool: 登录是否成功
        """
        if not self.project_id:
            print("未获取到项目ID，无法登录")
            return False

        payload = {
            "MallID": self.mall_id,
            "Code": code,
            "AppID": self.app_id,
            "OpenID": "",
            "NotVCodeAndGraphicVCode": True,
            "SNSType": 8,
            "Header": {
                "Token": None,
                "systemInfo": {
                    "model": "microsoft",
                    "SDKVersion": "3.8.10",
                    "system": "Windows 10 x64",
                    "version": "4.0.6.21",
                    "miniVersion": "DZ.2.5.64.1.SM.24"
                }
            }
        }

        url = f"{self.base_url}/a/liteapp/api/identitys/LoginForThirdV2"
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))

        try:
            response = self.client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("m") == 1:
                user_data = data.get("d", {})
                self.token = user_data.get("Token")
                nick_name = user_data.get("NickName", "未知用户")
                if self.token:
                    print(f"{nick_name}登录成功。")
                    return True
                else:
                    print("登录失败：未获取到Token")
                    return False
            else:
                print(f"登录失败：{data.get('e', '未知错误')}")
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
        if not self.token or not self.project_id:
            print("未获取到Token或项目ID，无法检查签到状态")
            return None

        payload = {
            "MallId": self.mall_id,
            "Header": {
                "Token": f"{self.token},{self.project_id}",
                "systemInfo": {
                    "model": "microsoft",
                    "SDKVersion": "3.8.10",
                    "system": "Windows 10 x64",
                    "version": "4.0.6.21",
                    "miniVersion": "DZ.2.5.64.1.SM.24"
                }
            }
        }

        url = f"{self.base_url}/api/user/user/GetNoticeFavoriteAndCheckinCount"
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))

        try:
            response = self.client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("m") == 1:
                checkin_data = data.get("d", {})
                is_checkin_today = checkin_data.get("IsCheckInToday", False)
                is_open_checkin = checkin_data.get("IsOpenCheckin", False)
                
                if is_open_checkin:
                    if is_checkin_today:
                        print("签到活动开放，今日已签到")
                    else:
                        print("签到活动开放，今日未签到")
                else:
                    print("签到活动未开放")
                
                return checkin_data
            else:
                print(f"检查签到状态失败：{data.get('e', '未知错误')}")
                return None

        except Exception as e:
            print(f"检查签到状态请求失败: {e}")
            return None

    def submit_signin(self) -> Optional[dict]:
        """
        提交签到

        Returns:
            Optional[dict]: 签到结果数据，None表示签到失败
        """
        if not self.token or not self.project_id:
            print("未获取到Token或项目ID，无法签到")
            return None

        payload = {
            "MallID": self.mall_id,
            "Header": {
                "Token": f"{self.token},{self.project_id}",
                "systemInfo": {
                    "model": "microsoft",
                    "SDKVersion": "3.8.10",
                    "system": "Windows 10 x64",
                    "version": "4.0.6.21",
                    "miniVersion": "DZ.2.5.64.1.SM.24"
                }
            }
        }

        url = f"{self.base_url}/api/user/User/CheckinV2"
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))

        try:
            response = self.client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("m") == 1:
                signin_data = data.get("d", {})
                msg = signin_data.get("Msg", "签到成功")
                print(msg)
                return signin_data
            else:
                print(f"签到失败：{data.get('e', '未知错误')}")
                return None

        except Exception as e:
            print(f"签到请求失败: {e}")
            return None

    def get_account_info(self) -> Optional[dict]:
        """
        获取账号积分余额

        Returns:
            Optional[dict]: 账号信息，None表示获取失败
        """
        if not self.token or not self.project_id:
            print("未获取到Token或项目ID，无法获取账号信息")
            return None

        payload = {
            "MallId": self.mall_id,
            "Header": {
                "Token": f"{self.token},{self.project_id}",
                "systemInfo": {
                    "model": "microsoft",
                    "SDKVersion": "3.8.10",
                    "system": "Windows 10 x64",
                    "version": "4.0.6.21",
                    "miniVersion": "DZ.2.5.64.1.SM.24"
                }
            }
        }

        url = f"{self.base_url}/api/user/user/GetUserAndMallCard"
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))

        try:
            response = self.client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("m") == 1:
                account_data = data.get("d", {})
                bonus = account_data.get("Bonus", 0)
                print(f"账号当前积分{bonus}")
                return account_data
            else:
                print(f"获取账号信息失败：{data.get('e', '未知错误')}")
                return None

        except Exception as e:
            print(f"获取账号信息请求失败: {e}")
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

        # 1. 获取项目ID
        if not self.get_project_config_id():
            print(f"账号 {nick_name} 获取项目ID失败")
            return False

        # 2. 登录
        if not self.login(code):
            print(f"账号 {nick_name} 登录失败")
            return False

        # 3. 检查签到状态
        signin_status = self.check_signin_status()
        if signin_status is None:
            print(f"账号 {nick_name} 检查签到状态失败")
            return False

        is_checkin_today = signin_status.get("IsCheckInToday", False)
        is_open_checkin = signin_status.get("IsOpenCheckin", False)

        if not is_open_checkin:
            print("签到活动未开放，跳过签到")
        elif is_checkin_today:
            print("今日已签到，跳过签到")
        else:
            # 4. 提交签到
            signin_result = self.submit_signin()
            if signin_result is None:
                print(f"账号 {nick_name} 签到失败")
                return False

        # 5. 获取账号积分信息
        self.get_account_info()

        return True

    def close(self):
        """关闭HTTP客户端"""
        self.client.close()


def main():
    """主函数"""
    try:
        print("正在获取登录Code...")
        app_id = "wx383a677b99e64655"
        codes = getCode.get_wechat_codes(app_id)

        if not codes:
            print("未获取到任何在线账号的Code")
            return

        print(f"获取到 {len(codes)} 个账号的Code")

        signin = SmSignin()

        try:
            for i, (nick_name, code) in enumerate(codes.items(), 1):
                print(f"\n{'='*50}")
                print(f"处理第 {i}/{len(codes)} 个账号")
                print(f"{'='*50}")

                try:
                    signin.process_account(nick_name, code)
                except Exception as e:
                    print(f"处理账号 {nick_name} 时发生错误: {e}")

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
