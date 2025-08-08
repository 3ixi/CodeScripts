# 微信iPad协议自动化脚本

## 环境准备

1. **兼容的协议服务**  
   支持以下微信iPad协议服务实现：
   - [WeChatPadPro](https://github.com/WeChatPadPro/WeChatPadPro)
   - [iwechat](https://github.com/iwechatcom/iwechat)
   - [牛子协议](https://github.com/wyourname/wool/tree/master/wechat)  
   兼容同样接口的协议服务，只要**确保接口一致**即可：

   | 功能类型 | 接口路径 | 接口说明 |
   |----------|----------|----------|
   | 管理 | `/admin/GetAuthKey`、`/admin/GetAllDevices`、`/api/v1/wx/user/status` | 获取授权码列表 |
   | 登录 | `/login/GetLoginStatus`、`/api/v1/wx/user/status` | 获取在线状态 |
   | 公众号/小程序 | `/applet/JsLogin`、`/api/v1/wx/app/get/code` | 授权小程序(返回授权后的code) |

2. **环境配置**  
   搭建教程请自行参考对应仓库内搭建教程【[WeChatPadPro官方教程](https://github.com/WeChatPadPro/WeChatPadPro/blob/main/%E5%BE%AE%E4%BF%A1%E7%99%BB%E5%BD%95%E9%AA%8C%E8%AF%81%E7%A0%81API%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97.md)、[iwechat官方教程](https://s.apifox.cn/c599d413-b785-4df9-a5f7-482786f96188/6693955m0)、[牛子协议教程](https://github.com/wyourname/wool/blob/master/wechat/readme.md)】，这里不提供。  
   搭建完成后需要：
   - 登录微信账号
   - 创建环境变量：
     - `WECHAT_SERVER`：协议服务IP地址和端口（如 `192.168.110.100:1238`）  
     - `ADMIN_KEY`：与搭建时设置的ADMIN_KEY一致（**仅WeChatPadPro或iwechat需要**，牛子协议不需要）  
     - `WX_ID`：**可选**，指定要获取Code的微信号（未设置微信号的话就是wxid_开头的微信号），多个用&分隔  
       - 对应iwechat接口的wx_id字段或WeChatPadPro接口的deviceId字段
       - 如果不设置这个环境变量则获取所有有效账号的Code
       - 示例：`WX_ID=wxid_23grbf32&wxid_s7dvuh23`
   - **必须**将 `getCode.py` 文件放置在脚本目录下（用于获取Code值，仓库内所有脚本都依赖这个文件）

## 模块说明

`getCode.py` 是获取Code核心模块（对应微信接口wx.login），用于通过微信iPad协议接口获取小程序登录Code值。所有自动化脚本都依赖此模块。

## 自动化脚本列表

| 脚本名 | 可用状态 | 小程序名 | 可获奖励 | 备注 |
|--------|----------|----------|----------|------|
| [杰士邦签到+抽奖](./jieshibang.py) | ⚠️ | 杰士邦会员中心 | 积分/抽奖实物 |  |
| [1点点签到](./1diandian.py) | ✅ | 1点点alittleTea+ | 积分 | 自动领优惠券 |
| [优智云家签到](./youzhiyunjia.py) | ✅ | 优智云家品牌商城 | 积分 | 兑换智能家电 |
| [三福会员中心签到](./sanfu.py) | ✅ | 三福会员中心 | 福币 |  |
| [蓝氏宠物签到](./lanshi.py) | ✅ | 蓝氏宠物LEGENDSANDY | 积分 |  |
| [途虎养车签到](./tuhu.py) | ✅ | 途虎养车 | 积分 |  |

  
> - ✅ 表示完全可用  
> - ⚠️ 表示部分功能可用  
> - ❌ 表示暂时不可用  
> - 脚本如果提示“获取用户信息失败”等类似提示或直接报错，表示没有注册小程序，需要先用对应微信打开小程序手动登录一次再运行脚本