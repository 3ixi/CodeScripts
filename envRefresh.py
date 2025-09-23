#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青龙面板环境变量更新脚本
用于自动获取并更新青龙面板中的指定环境变量值
脚本作者：3iXi
创建时间：2025/09/22
！！此脚本需要配合iPad协议服务使用！！
需要自定义依赖：
　　　　　　　　getCode.py（https://github.com/3ixi/CodeScripts）
　　　　　　　　cloud_auth.py（https://github.com/3ixi/CloudScripts）
　　　　　　　　SendNotify.py（https://github.com/3ixi/CloudScripts）
--------------------------
2025/09/22 更新支持：捷停车、老板电器、雀巢会员俱乐部
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

import getCode
import cloud_auth
import SendNotify

# 青龙面板API相关常量
API_ENDPOINTS = {
    'auth': '/open/auth/token',
    'envs': '/open/envs'
}
BASE_HEADERS = {
    'User-Agent': 'envRefresh_3iXi/1.0.1',
    'Accept': 'application/json'
}

ENV_UPDATE_CONFIG = {
    'quechao': {
        'appid': 'wxc5db704249c9bb31',
        'api_url': 'https://crm.nestlechinese.com/openapi/identityservice/connect/token',
        'api_host': 'crm.nestlechinese.com',
        'name': '雀巢会员俱乐部'
    },
    'laobandianqi': {
        'appid': 'wxba70fb8e3eb3aab9',
        'api_url': 'https://aio.myroki.com/api/v1/mini-app/user/login',
        'api_host': 'aio.myroki.com',
        'name': '老板电器'
    },
    'jtc': {
        'appid': 'wx24b70f0ad2a9a89a',
        'api_url': 'https://www.jslife.com.cn/wxhttp/weixin/xcx/get_openid_by_code',
        'api_host': 'www.jslife.com.cn',
        'name': '捷停车'
    }
}

class QinglongEnvUpdater:
    """青龙面板环境变量更新器"""
    
    def __init__(self):
        """初始化，获取必要的环境变量"""
        # 获取青龙面板认证信息
        env_refresh = os.getenv('envRefresh')
        if not env_refresh:
            raise ValueError("未找到环境变量'envRefresh'，请访问青龙面板的“系统设置”-“应用设置”创建包含“环境变量”权限的应用，按照client_id&client_secret格式创建envRefresh环境变量")
        
        parts = env_refresh.split('&')
        if len(parts) != 2:
            raise ValueError("环境变量'envRefresh'格式错误，应为client_id&client_secret")
        
        self.client_id = parts[0]
        self.client_secret = parts[1]
        
        # 获取青龙面板URL：优先使用环境变量，其次尝试本地默认地址
        env_qinglong = os.getenv('qinglongURL')

        if env_qinglong:
            self.qinglong_url = env_qinglong.rstrip('/')
        else:
            # 默认尝试本地青龙地址
            default_url = 'http://127.0.0.1:5700'
            # 测试默认地址是否可达
            try:
                test_resp = requests.get(default_url, headers=BASE_HEADERS, timeout=3)
                if 200 <= test_resp.status_code < 400:
                    self.qinglong_url = default_url
                else:
                    raise Exception('默认地址返回异常状态码')
            except Exception:
                # 默认地址不可达，提示用户需要创建环境变量
                raise ValueError("未检测到可用的青龙面板地址。请创建环境变量'qinglongURL'，值为青龙面板的Web访问地址（例如 http://192.168.110.102:5700）")
        
        self.token = None
        self.env_list = []
        
    def _make_request(self, method: str, url: str, **kwargs) -> Dict:
        """统一请求处理"""
        headers = BASE_HEADERS.copy()
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
            del kwargs['headers']
            
        try:
            response = requests.request(method, url, headers=headers, **kwargs, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # 统一错误处理
            if 'statusCode' in data:
                raise Exception(f"请求失败: {data.get('message', '未知错误')}")
                
            return data
        except requests.RequestException as e:
            raise Exception(f"网络请求失败: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"响应数据解析失败: {e}")
    
    def authenticate(self):
        """获取青龙面板认证token"""
        url = f"{self.qinglong_url}{API_ENDPOINTS['auth']}"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        data = self._make_request('GET', url, params=params)

        if 'data' in data and 'token' in data['data']:
            self.token = data['data']['token']
            print("✅ 青龙面板认证成功")
        else:
            raise Exception("认证失败，未找到token")
    def get_envs(self):
        """获取环境变量列表"""
        if not self.token:
            raise Exception("请先进行认证")

        url = f"{self.qinglong_url}{API_ENDPOINTS['envs']}"
        headers = {
            'Authorization': f'Bearer {self.token}'
        }

        data = self._make_request('GET', url, headers=headers)

        if 'data' in data:
            self.env_list = data['data']
            print(f"✅ 获取到{len(self.env_list)}个环境变量")
        else:
            raise Exception("获取环境变量列表失败")
    
    def _get_env_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取环境变量"""
        for env in self.env_list:
            if env.get('name') == name:
                return env
        return None
    
    def _update_env_value(self, env_id: int, name: str, value: str, remarks_prefix: str):
        """更新环境变量值"""
        if not self.token:
            raise Exception("请先进行认证")
            
        url = f"{self.qinglong_url}{API_ENDPOINTS['envs']}"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        today = datetime.now().strftime('%Y%m%d')
        remarks = f"{remarks_prefix}{today}更新"
        
        payload = {
            'id': env_id,
            'name': name,
            'value': value,
            'remarks': remarks
        }
        
        data = self._make_request('PUT', url, headers=headers, json=payload)
        
        if data.get('code') == 200:
            print(f"✅ 环境变量{name}更新成功")
            print("-" * 30)
        else:
            raise Exception(f"环境变量{name}更新失败: {data}")
    
    def _update_quechao_env(self, env_info: Dict):
        """更新雀巢环境变量"""
        print("🔄 开始更新雀巢会员俱乐部环境变量...")
        
        # 获取Code列表
        app_id = ENV_UPDATE_CONFIG['quechao']['appid']
        codes = getCode.get_wechat_codes(app_id)
        
        if not codes:
            raise Exception("未获取到任何Code")
        
        # 获取新Token
        access_tokens = []
        for nick_name, code in codes.items():
            print(f"🎫 正在获取{nick_name}的新Token...")
            
            headers = {
                'host': ENV_UPDATE_CONFIG['quechao']['api_host'],
                'content-type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2541022) XWEB/16467'
            }
            
            payload = {
                'client_id': 'wechatMini',
                'client_secret': 'secret',
                'grant_type': 'wechat_auth_code',
                'auth_code': code
            }
            
            try:
                response = requests.post(
                    ENV_UPDATE_CONFIG['quechao']['api_url'],
                    headers=headers,
                    data=payload,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                if 'access_token' in result:
                    access_tokens.append(result['access_token'])
                    print(f"✅ {nick_name}新Token获取成功")
                else:
                    error_msg = result.get('error', '未知错误')
                    print(f"❌ {nick_name}新Token获取失败: {error_msg}")
            except Exception as e:
                print(f"❌ {nick_name}新Token获取失败: {e}")
        
        if not access_tokens:
            raise Exception("未获取到任何有效的新Token")
        
        # 更新环境变量
        new_value = "#".join(access_tokens)
        self._update_env_value(
            env_info['id'],
            env_info['name'],
            new_value,
            ENV_UPDATE_CONFIG['quechao']['name']
        )
        
        return len(access_tokens)
    
    def _update_laobandianqi_env(self, env_info: Dict):
        """更新老板电器环境变量"""
        print("🔄 开始更新老板电器环境变量...")
        
        # 获取Code列表
        app_id = ENV_UPDATE_CONFIG['laobandianqi']['appid']
        codes = getCode.get_wechat_codes(app_id)
        
        if not codes:
            raise Exception("未获取到任何Code")
        
        # 获取新Token
        tokens = []
        for nick_name, code in codes.items():
            print(f"🎫 正在获取{nick_name}的新Token...")
            
            # 生成时间戳
            timestamp = int(time.time() * 1000)
            
            # 使用云函数认证模块生成签名相关参数，调用云服务获取secret和signature
            auth_client = cloud_auth.get_auth_client()
            try:
                auth_resp = auth_client.call_service('roki', timestamp=timestamp)
                if auth_resp.get('success'):
                    secret = auth_resp.get('secret', '')
                    signature = auth_resp.get('signature', '')
                    if not secret or not signature:
                        print(f"❌ {nick_name} 获取认证信息失败: secret或signature为空")
                        continue
                else:
                    error_msg = auth_resp.get('error', '未知错误')
                    print(f"❌ {nick_name} 获取认证信息失败: {error_msg}")
                    continue
            except Exception as e:
                print(f"❌ {nick_name} 获取认证信息失败: {e}")
                continue
            
            headers = {
                'host': ENV_UPDATE_CONFIG['laobandianqi']['api_host'],
                'content-type': 'application/json',
                'x-app-env': 'release',
                'timestamp': str(timestamp),
                'nonce': '1234567890123456',
                'app-version': '5000',
                'app-id': 'roki_app',
                'signature': signature,
                'secret': secret
            }
            
            payload = {
                "code": code,
                "param": {
                    "qr-code": ""
                }
            }
            
            try:
                response = requests.post(
                    ENV_UPDATE_CONFIG['laobandianqi']['api_url'],
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get('success', False) and 'data' in result and 'token' in result['data']:
                    tokens.append(result['data']['token'])
                    print(f"✅ {nick_name}新Token获取成功")
                else:
                    error_msg = result.get('message', '未知错误')
                    print(f"❌ {nick_name}新Token获取失败: {error_msg}")
            except Exception as e:
                print(f"❌ {nick_name}新Token获取失败: {e}")
        
        if not tokens:
            raise Exception("未获取到任何有效的新Token")
        
        # 更新环境变量
        new_value = "#".join(tokens)
        self._update_env_value(
            env_info['id'],
            env_info['name'],
            new_value,
            ENV_UPDATE_CONFIG['laobandianqi']['name']
        )
        
        return len(tokens)

    def _update_jtc_env(self, env_info: Dict):
        """更新捷停车环境变量（jtc）"""
        print("🔄 开始更新捷停车环境变量...")

        app_id = ENV_UPDATE_CONFIG['jtc']['appid']
        codes = getCode.get_wechat_codes(app_id)

        if not codes:
            raise Exception("未获取到任何Code")

        tokens = []
        for nick_name, code in codes.items():
            print(f"🎫 正在获取{nick_name}的新Token...")

            t = int(time.time() * 1000)

            url = f"{ENV_UPDATE_CONFIG['jtc']['api_url']}?t={t}"

            headers = {
                'Host': ENV_UPDATE_CONFIG['jtc']['api_host'],
                'Connection': 'keep-alive',
                'applicationVersion': '1.0.1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2541022) XWEB/16467',
                'Content-Type': 'application/json;charset=UTF-8',
                'Accept': '*/*',
                'Referer': f"https://servicewechat.com/{app_id}/285/page-frame.html",
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9'
            }

            payload = {
                'code': code,
                'userType': 'WX_XCX_JTC',
                'appId': app_id
            }

            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                result = response.json()

                if str(result.get('resultCode')) != '0':
                    message = result.get('message', '未知错误')
                    print(f"❌ {nick_name} 获取新Token失败: {message}")
                    continue

                obj = result.get('obj', {})
                token = obj.get('token')
                if token:
                    tokens.append(token)
                    print(f"✅ {nick_name}新Token获取成功")
                else:
                    print(f"❌ {nick_name} 响应中未包含token")

            except Exception as e:
                print(f"❌ {nick_name}新Token获取失败: {e}")

        if not tokens:
            raise Exception("未获取到任何有效的新Token")

        new_value = "#".join(tokens)
        self._update_env_value(
            env_info['id'],
            env_info['name'],
            new_value,
            ENV_UPDATE_CONFIG['jtc']['name']
        )

        return len(tokens)
    
    def update_envs(self) -> Tuple[int, int, List[Dict[str, Any]]]:
        """更新所有支持的环境变量"""
        if not self.env_list:
            raise Exception("请先获取环境变量列表")
        
        updated_env_count = 0
        updated_value_count = 0

        # 收集每个环境变量的更新结果，便于推送通知
        per_env_results: List[Dict[str, Any]] = []

        # 遍历支持更新的环境变量
        for env_name, config in ENV_UPDATE_CONFIG.items():
            env_info = self._get_env_by_name(env_name)
            if not env_info:
                msg = f"⚠️ 您未创建环境变量{env_name}，本次跳过更新"
                print(msg)
                per_env_results.append({
                    'key': env_name,
                    'name': config.get('name', ''),
                    'success': False,
                    'count': 0,
                    'message': '未创建此环境变量'
                })
                continue

            try:
                if env_name == 'quechao':
                    value_count = self._update_quechao_env(env_info)
                elif env_name == 'laobandianqi':
                    value_count = self._update_laobandianqi_env(env_info)
                elif env_name == 'jtc':
                    value_count = self._update_jtc_env(env_info)
                else:
                    print(f"⚠️ 环境变量{env_name}暂不支持更新")
                    per_env_results.append({
                        'key': env_name,
                        'name': config.get('name', ''),
                        'success': False,
                        'count': 0,
                        'message': '不支持更新'
                    })
                    continue

                # 成功更新
                updated_env_count += 1
                updated_value_count += value_count
                per_env_results.append({
                    'key': env_name,
                    'name': config.get('name', ''),
                    'success': True,
                    'count': value_count,
                    'message': ''
                })

            except Exception as e:
                print(f"❌ 环境变量{env_name}更新失败: {e}")
                per_env_results.append({
                    'key': env_name,
                    'name': config.get('name', ''),
                    'success': False,
                    'count': 0,
                    'message': str(e)
                })

        return updated_env_count, updated_value_count, per_env_results

def main():
    """主函数"""
    print("🔄 青龙面板环境变量更新脚本开始执行...")
    print("=" * 30)
    try:
        updater = QinglongEnvUpdater()
        updater.authenticate()
        updater.get_envs()
        env_count, value_count, per_env_results = updater.update_envs()

        print("=" * 30)
        print(f"✅ 脚本执行完成")
        # 构造更详细的推送内容，包含每个环境的中文名、key、成功/失败、数量与错误信息
        lines = []
        lines.append(f"本次成功更新了{env_count}个环境变量，共{value_count}个环境变量值")
        lines.append("")
        for r in per_env_results:
            name = r.get('name') or ''
            key = r.get('key')
            success = r.get('success')
            count = r.get('count')
            message = r.get('message') or ''

            if success:
                lines.append(f"{name}（{key}）更新成功，更新了{count}个环境变量值")
                lines.append("=" * 30)
            else:
                lines.append(f"{name}（{key}）更新失败，更新了{count}个环境变量值")
                if message:
                    lines.append(f"  错误信息: {message}")
                    lines.append("=" * 30)

        content = "\n".join(lines)
        # 发送推送通知
        try:
            title = "青龙环境变量更新脚本执行完成"
            SendNotify.SendNotify(title, content)
        except Exception as e:
            print(f"⚠️ 发送通知时出错: {e}")

    except Exception as e:
        print(f"❌ 脚本执行失败: {e}")
        # 失败时也尝试发送通知
        try:
            title = "青龙环境变量更新脚本执行失败"
            content = f"脚本执行失败: {e}"
            SendNotify.SendNotify(title, content)
        except Exception as e2:
            print(f"⚠️ 发送失败通知时出错: {e2}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())