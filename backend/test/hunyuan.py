# cred = credential.Credential("AKIDOegYFoCQTIAoFVXLzVs31qdGjzazA8sO", "KRKyOccNuDJByWryrVv7f7RXP5e2DCzc")


# -*- coding: utf-8 -*-
import json

from tencentcloud.common.common_client import CommonClient
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile

class NonStreamResponse(object):
    def __init__(self):
        self.response = ""

    def _deserialize(self, obj):
        self.response = json.dumps(obj)

try:
    # 实例化一个认证对象，入参需要传入腾讯云账户 SecretId 和 SecretKey，此处还需注意密钥对的保密
    # 代码泄露可能会导致 SecretId 和 SecretKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考，建议采用更安全的方式来使用密钥，请参见：https://cloud.tencent.com/document/product/1278/85305
    # 密钥可前往官网控制台 https://console.cloud.tencent.com/cam/capi 进行获取
    cred = ("AKIDOegYFoCQTIAoFVXLzVs31qdGjzazA8sO", "KRKyOccNuDJByWryrVv7f7RXP5e2DCzc")

    httpProfile = HttpProfile()
    httpProfile.endpoint = "hunyuan.tencentcloudapi.com"
    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile

    params = "{}";
    common_client = CommonClient("hunyuan", "2023-09-01", cred, "", profile=clientProfile)
    resp = common_client._call_and_deserialize("ChatCompletions", json.loads(params), NonStreamResponse)
    if isinstance(resp, NonStreamResponse):  # 非流式响应
        print(resp.response)
    else:  # 流式响应
        for event in resp:
            print(event)
except TencentCloudSDKException as err:
    print(err)