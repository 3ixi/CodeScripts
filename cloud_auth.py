#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3iXi云函数认证模块
用于与3iXi认证服务器进行安全通信，云端加密敏感信息
创建日期：2025-09-08
模块作者：3iXi
项目主页：https://github.com/3ixi/CloudScripts
获取授权码：https://3ixi.top

安全说明：
- 本模块仅用于与云函数认证服务器进行安全通信
- 不会收集或上传用户的个人账号数据
- 所有敏感信息均在云端加密处理
- 仅传输必要的认证信息，保护用户隐私
"""

import os
import json
import time
import uuid
import base64
import sys
from datetime import datetime, timezone, timedelta

def check_required_packages():
    missing_packages = []

    try:
        import requests
    except ImportError:
        missing_packages.append('requests')

    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad, unpad
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_v1_5
    except ImportError:
        missing_packages.append('pycryptodome')

    if missing_packages:
        print("❌ 缺少必需的依赖库，请安装以下库：")
        print()
        for package in missing_packages:
            print(f"   pip install {package}")
        print()
        print("安装完成后请重新运行脚本。")
        sys.exit(1)

check_required_packages()

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

PRIMARY_BASE_URL = "https://3ixi.top"
BACKUP_BASE_URL = "https://cloud.3ixi.top"

class CloudAuth:
    def __init__(self):
        self.base_urls = [PRIMARY_BASE_URL, BACKUP_BASE_URL]
        self.current_url_index = 0
        self.auth_code = None
        self.session = requests.Session()
        self._load_auth_code()

        if self.auth_code:
            self._verify_auth_code()

    def _set_connection(self):
        key_fragments = {
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                'prefix': 'QGp3','middle1': 'PFUk','middle2': 'MERJYmQp','suffix': 'ZW4pPw==',}

        sequence = ['prefix', 'middle1', 'middle2', 'suffix']
        encoded_key = ''.join([key_fragments[part] for part in sequence])

        try:
            decoded_key = base64.b64decode(encoded_key).decode('utf-8')
            if len(decoded_key) == 16:
                return decoded_key
        except:
            pass

        backup_data = [64, 106, 119, 60, 85, 36, 48, 68, 73, 98, 100, 41, 101, 110, 41, 63]
        return ''.join([chr(x) for x in backup_data])
    
    def _switch_to_next_url(self):
        self.current_url_index = (self.current_url_index + 1) % len(self.base_urls)
        return self.base_urls[self.current_url_index]
    
    def _get_current_url(self):
        return self.base_urls[self.current_url_index].rstrip('/')
    
    def _load_auth_code(self):
        self.auth_code = os.getenv('CloudAuth')
        if not self.auth_code:
            raise ValueError("未找到环境变量'CloudAuth'，请访问https://3ixi.top获取授权码")
        
        try:
            uuid.UUID(self.auth_code)
        except ValueError:
            raise ValueError("授权码格式无效，请访问https://3ixi.top重新获取")
    
    def _get_timestamp(self):
        timestamp_ms = int(time.time() * 1000)
        timestamp_bytes = timestamp_ms.to_bytes(8, byteorder='big') + b'\x00' * 8
        return timestamp_bytes, timestamp_ms
    
    def _aes_encrypt(self, data):
        timestamp_data, timestamp_ms = self._get_timestamp()

        cipher = AES.new(self._set_connection().encode('utf-8'), AES.MODE_CBC, timestamp_data)
        
        padded_data = pad(data.encode('utf-8'), AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        
        encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
        random_hex = hex(timestamp_ms)[2:]
        
        return encrypted_b64, random_hex
    
    def _aes_decrypt(self, encrypted_data, random_hex):
        timestamp_ms = int(random_hex, 16)
        timestamp_bytes = timestamp_ms.to_bytes(8, byteorder='big') + b'\x00' * 8

        cipher = AES.new(self._set_connection().encode('utf-8'), AES.MODE_CBC, timestamp_bytes)
        
        encrypted_bytes = base64.b64decode(encrypted_data)
        decrypted_padded = cipher.decrypt(encrypted_bytes)
        decrypted_data = unpad(decrypted_padded, AES.block_size)
        
        return decrypted_data.decode('utf-8')
    
    def _make_request(self, endpoint, data=None, method='POST'):
        if data is None:
            data = {}
        
        data['auth_code'] = self.auth_code
        json_data = json.dumps(data, ensure_ascii=False)
        encrypted_data, random_hex = self._aes_encrypt(json_data)
        
        headers = {
            'Content-Type': 'application/json',
            'random': random_hex
        }
        
        for _ in range(len(self.base_urls)):
            current_url = self._get_current_url()
            url = f"{current_url}{endpoint}"
            
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, headers=headers, timeout=30)
                else:
                    response = self.session.post(url, json={'data': encrypted_data}, headers=headers, timeout=30)
                
                response.raise_for_status()
                
                response_data = response.json()
                if 'data' in response_data:
                    decrypted_response = self._aes_decrypt(response_data['data'], random_hex)
                    return json.loads(decrypted_response)
                else:
                    return response_data
                    
            except requests.RequestException as e:
                print(f"请求失败: {e}")
                self._switch_to_next_url()
                print(f"尝试切换到备用地址")
            except json.JSONDecodeError as e:
                print(f"响应解析失败: {e}")
                self._switch_to_next_url()
                print(f"尝试切换到备用地址")
            except Exception as e:
                print(f"解密失败: {e}")
                self._switch_to_next_url()
                print(f"尝试切换到备用地址")
        
        raise Exception("所有服务器地址均请求失败，请检查网络连接或服务器状态")
    
    def _verify_auth_code(self):
        try:
            response = self._make_request('/api/verify')

            if response.get('success'):
                expire_date = response.get('expire_date')
                if expire_date:
                    china_tz = timezone(timedelta(hours=8))
                    expire_dt = datetime.fromisoformat(expire_date.replace('Z', '+00:00'))
                    china_time = expire_dt.astimezone(china_tz)

                    print(f"📅 授权码截止日期: {china_time.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print("✅ 授权码验证成功，但未获取到截止日期")

                notifications = response.get('notifications', [])
                if notifications:
                    print("\n" + "="*30)
                    print("📢 系统通知:")
                    for i, notification in enumerate(notifications, 1):
                        title = notification.get('title', '无标题')
                        content = notification.get('content', '无内容')
                        print(f"\n{i}. {title}")
                        print(f"   {content}")
                    print("="*30)

            else:
                error_msg = response.get('error', '未知错误')

                if '禁用' in error_msg:
                    disable_reason = response.get('disable_reason', '未知原因')
                    disabled_at = response.get('disabled_at', '')

                    print(f"❌ 授权码已被禁用")
                    print(f"📝 禁用原因: {disable_reason}")
                    
                    if disabled_at:
                        try:
                            china_tz = timezone(timedelta(hours=8))
                            disabled_dt = datetime.fromisoformat(disabled_at.replace('Z', '+00:00'))
                            china_time = disabled_dt.astimezone(china_tz)
                            print(f"⏰ 禁用时间: {china_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        except:
                            print(f"⏰ 禁用时间: {disabled_at}")
                else:
                    print(f"❌ 授权码验证失败: {error_msg}")

                raise Exception(f"授权码验证失败: {error_msg}")

        except Exception as e:
            if "授权码验证失败:" not in str(e):
                print(f"❌ 授权码验证失败: {e}")
            raise
    
    def call_service(self, service_name, **kwargs):
        data = {
            'mod': service_name,
            **kwargs
        }

        try:
            response = self._make_request('/api/service', data)

            if response.get('success'):
                return response
            else:
                error_msg = response.get('error', '未知错误')
                raise Exception(f"{service_name}服务调用失败: {error_msg}")

        except Exception as e:
            print(f"❌ {service_name}服务调用失败: {e}")
            raise


def get_auth_client():
    return CloudAuth()


def call_service(service_name, **kwargs):
    client = get_auth_client()
    return client.call_service(service_name, **kwargs)


if __name__ == "__main__":
    print("3iXi认证模块")
    print("=" * 30)
    print("访问https://3ixi.top获取授权码")