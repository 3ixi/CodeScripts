#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
途虎养车小程序签到脚本
脚本作者：3iXi
创建时间：2025/07/18
！！此脚本需要配合iPad协议服务使用！！
小程序：途虎养车
"""

import time
import json
from typing import Optional, Tuple

try:
    import httpx
except ImportError:
    print("错误: 需要安装 httpx[http2] 依赖")
    exit(1)

import getCode


class TuhuSignin:
    """途虎养车小程序签到类"""

    def __init__(self):
        """初始化签到客户端"""
        self.base_url = "https://gateway.tuhu.cn"
        self.login_url = "https://cl-gateway.tuhu.cn"
        
        self.client = httpx.Client(http2=True, timeout=30.0)#verify=False
        
        self.headers = {
            "host": "gateway.tuhu.cn",
            "authtype": "oauth",
            "user-agent": "Tuhu/7.29.0 (iPhone; iOS 18.3; Scale/3.0)",
            "accept-language": "zh-CN,zh-Hans;q=0.9",
            "accept": "*/*",
            "content-type": "application/json",
            "neederrorcode": "true",
            "accept-encoding": "gzip, deflate, br"
        }
        
        self.login_headers = {
            "Host": "cl-gateway.tuhu.cn",
            "Content-Type": "application/json",
            "Connection": "keep-alive",
            "channel": "wechat-miniprogram",
            "content-type": "application/json",
            "platformSource": "uni-app",
            "authType": "oauth",
            "currentPage": "pages/home/home",
            "api_level": "2",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.61(0x18003d2c) NetType/4G Language/zh_CN",
            "Referer": "https://servicewechat.com/wx27d20205249c56a3/1130/page-frame.html"
        }

    def _check_response(self, data: dict, operation: str) -> bool:
        """
        检查响应是否成功
        
        Args:
            data (dict): 响应数据
            operation (str): 操作名称
            
        Returns:
            bool: 是否成功
        """
        code = data.get("code")
        if code == 10000:
            return True
        else:
            message = data.get("message", "未知错误")
            print(f"{operation}失败：{message}")
            return False

    def login(self, code: str) -> Tuple[Optional[str], Optional[str]]:
        """
        登录获取用户会话
        
        Args:
            code (str): 微信小程序登录code
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (userSession, nickName)
        """
        url = f"{self.login_url}/cl-user-auth-login/login/authSilentSign"
        
        payload = {
            "channel":"WXAPP",
            "code":code
        }

        payload_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        content_length = len(payload_str.encode('utf-8'))

        headers = self.login_headers.copy()
        headers["Content-Length"] = str(content_length)

        try:
            response = self.client.post(url, content=payload_str, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if self._check_response(data, "登录"):
                result_data = data.get("data", {})
                user_session = result_data.get("userSession")
                nick_name = result_data.get("nickName", "微信用户")
                
                if user_session:
                    print(f"账号{nick_name}登录成功")
                    return user_session, nick_name
                else:
                    print("登录失败：未获取到userSession")
                    return None, None
            else:
                return None, None
                
        except Exception as e:
            print(f"登录请求失败: {e}")
            return None, None

    def check_signin_status(self, user_session: str) -> Optional[bool]:
        """
        检查今日签到状态
        
        Args:
            user_session (str): 用户会话
            
        Returns:
            Optional[bool]: True表示已签到，False表示未签到，None表示请求失败
        """
        url = f"{self.base_url}/cl/cl-common-api/api/member/getSignInInfo"
        
        payload = {"channel": "app"}

        payload_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        content_length = len(payload_str.encode('utf-8'))

        headers = self.headers.copy()
        headers["content-length"] = str(content_length)
        headers["authorization"] = f"Bearer {user_session}"

        try:
            response = self.client.post(url, content=payload_str, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if self._check_response(data, "检查签到状态"):
                result_data = data.get("data", {})
                sign_in_status = result_data.get("signInStatus", False)
                
                if sign_in_status:
                    print("今日已签到")
                else:
                    print("今日未签到")
                    
                return sign_in_status
            else:
                return None
                
        except Exception as e:
            print(f"检查签到状态请求失败: {e}")
            return None

    def submit_signin(self, user_session: str) -> Optional[dict]:
        """
        提交签到
        
        Args:
            user_session (str): 用户会话
            
        Returns:
            Optional[dict]: 签到结果数据，None表示签到失败
        """
        url = f"{self.base_url}/cl/cl-common-api/api/dailyCheckIn/userCheckIn"
        
        payload = {"channel": "app"}

        payload_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        content_length = len(payload_str.encode('utf-8'))

        headers = self.headers.copy()
        headers["content-length"] = str(content_length)
        headers["authorization"] = f"Bearer {user_session}"

        try:
            response = self.client.post(url, content=payload_str, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if self._check_response(data, "签到"):
                result_data = data.get("data", {})
                reward_integral = result_data.get("rewardIntegral", 0)
                continuous_days = result_data.get("continuousDays", 0)
                
                print(f"签到成功，获得{reward_integral}积分，已连续签到{continuous_days}天")
                return result_data
            else:
                return None
                
        except Exception as e:
            print(f"签到请求失败: {e}")
            return None

    def get_current_integral(self, user_session: str) -> Optional[int]:
        """
        获取当前剩余积分
        
        Args:
            user_session (str): 用户会话
            
        Returns:
            Optional[int]: 当前积分，None表示获取失败
        """
        url = f"{self.base_url}/cl/cl-common-api/api/member/getSignInInfo"
        
        payload = {"channel": "app"}

        payload_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        content_length = len(payload_str.encode('utf-8'))

        headers = self.headers.copy()
        headers["content-length"] = str(content_length)
        headers["authorization"] = f"Bearer {user_session}"

        try:
            response = self.client.post(url, content=payload_str, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if self._check_response(data, "获取积分"):
                result_data = data.get("data", {})
                user_integral = result_data.get("userIntegral", 0)
                
                print(f"当前积分{user_integral}")
                return user_integral
            else:
                return None
                
        except Exception as e:
            print(f"获取积分请求失败: {e}")
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
        user_session, _ = self.login(code)
        if not user_session:
            print(f"账号 {nick_name} 登录失败")
            return False
        
        # 2. 检查签到状态
        sign_status = self.check_signin_status(user_session)
        if sign_status is None:
            print(f"账号 {nick_name} 检查签到状态失败")
            return False
        
        if sign_status:
            # 已签到，直接获取积分
            self.get_current_integral(user_session)
        else:
            # 3. 提交签到
            signin_result = self.submit_signin(user_session)
            if signin_result is None:
                print(f"账号 {nick_name} 签到失败")
                return False
            
            # 4. 获取当前积分
            self.get_current_integral(user_session)
        
        return True

    def close(self):
        """关闭HTTP客户端"""
        self.client.close()


def main():
    """主函数"""
    try:
        print("正在获取登录Code...")
        app_id = "wx27d20205249c56a3"
        codes = getCode.get_wechat_codes(app_id)
        
        if not codes:
            print("未获取到任何在线账号的Code")
            return
        
        print(f"获取到 {len(codes)} 个账号的Code")
        
        signin = TuhuSignin()
        
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
