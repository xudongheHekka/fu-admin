import urllib.parse
import requests

# 基础 URL
base_url = "http://127.0.0.1:8084/user/apple/ads_data/callback"

# 参数
params = {
    "event_name": "login",
    "idfv": "30CF1FE3-4F29-4030-B79D-12176E56B644",
    "bundleid": "com.innovation.driftbottle",
    "os_version": "17.7.2",
    "app_version": "7.10.7",
    "app_bundleid": "com.innovation.driftbottle",
    "channel_id": "-1",
    "event_custom_params": "{\"_coppa_enabled\":\"false\",\"_province\":\"ha\",\"random_user_id\":\"-2997023727792927530\",\"_screen_height\":\"2778\",\"ip_upload\":\"39.144.24.82\",\"_is_first_time\":\"false\",\"_event_type\":\"3\",\"_distinct_id_type\":\"1001\",\"_channel\":\"AppStore\",\"_app_version_code\":\"1\",\"_screen_width\":\"1284\",\"_city\":\"dongyu\",\"se_pro_id\":\"3953\",\"_isGDPRArea\":\"false\",\"_type\":\"event\",\"_lib\":\"2\",\"_country\":\"CN\",\"_log_count\":\"64\",\"_country_code\":\"CN\",\"_kidsapp_enabled\":\"false\",\"_app_name\":\"遇见漂流瓶\",\"ecpm_rate\":\"1\",\"_is_first_day\":\"false\",\"_sdk_type\":\"ios\",\"_source_type\":\"sdk\",\"_locale\":\"zh_CN\"}",
    "idfa": "00000000-0000-0000-0000-000000000000",
    "event_time": "1743030453396",
    "city": "",
    "app_platform": "ios",
    "event_data": "{\"login_type\":\"2\"}",
    "distinct_id": "DC81F7CF-F991-436F-B555-36AD6FAB6E87",
    "account_id": "",
    "report_time": "1743030453426",
    "order_id": "111",
    "order_amount": "11",
    "event_account_id": ""
}

# 拼接 URL
query_string = urllib.parse.urlencode(params)
full_url = f"{base_url}?{query_string}"

# # 打印拼接的 URL
# print("拼接的完整 URL:")
# print(full_url)

# 发送 GET 请求
response = requests.get(full_url)

# 打印响应结果
print("\n响应状态码:", response.status_code)
print("响应内容:")
print(response.text)
