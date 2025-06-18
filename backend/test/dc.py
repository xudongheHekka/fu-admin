import pandas as pd

# 主分类分段起始code
rows = [
    ["消息", "私聊", "RECEIVE_IM_PRIVATE_MESSAGE", 10000],
    ["消息", "家族", "RECEIVE_IM_FAMILY_MESSAGE", 10001],
    ["消息", "运营推送", "RECEIVE_IM_OPERATION_MESSAGE", 10002],
    ["消息", "礼物", "RECEIVE_GIFT_MESSAGE", 10003],
    ["匹配", "捞瓶子", "BE_MATCHED_BOTTLE", 20000],
    ["匹配", "星座速配", "BE_MATCHED_CONSTELLATION", 20001],
    ["匹配", "系统帮捞瓶子", "SYSTEM_MATCH_BOTTLE", 20002],
    ["访问", "个人资料", "PROFILE_VISITED", 30000],
    ["访问", "个人资料点赞", "PROFILE_LIKED", 30001],
    ["访问", "动态", "DYNAMIC_VISITED", 30002],
    ["通知", "动态被访问", "NOTIFY_DYNAMIC_VISITED", 40000],
    ["通知", "动态被评论", "NOTIFY_DYNAMIC_COMMENTED", 40001],
    ["通知", "动态被点赞", "NOTIFY_DYNAMIC_LIKED", 40002],
    ["通知", "被送礼", "NOTIFY_RECEIVE_GIFT", 40003],
    ["通知", "被踢出家族", "NOTIFY_KICKED_FROM_FAMILY", 40004],
    ["通知", "被通过加入家族", "NOTIFY_FAMILY_JOIN_APPROVED", 40005],
    ["通知", "加入家族申请", "NOTIFY_FAMILY_JOIN_APPLY", 40006],
    ["通知", "被关注", "NOTIFY_BE_FOLLOWED", 40007],
    ["通知", "被取消关注", "NOTIFY_BE_UNFOLLOWED", 40008],
    ["通知", "被举报", "NOTIFY_BE_REPORTED", 40009],
    ["通知", "被拉黑", "NOTIFY_BE_BLOCKED", 40010],
    ["通知", "被封禁", "NOTIFY_BE_BANNED", 40011],
    ["通知", "被沉默", "NOTIFY_BE_MUTED", 40012],
    ["状态变化", "会员到期", "VIP_EXPIRED", 50000],
    ["状态变化", "会员自动续费", "VIP_RENEWED", 50001],
    ["状态变化", "道具到期", "PROP_EXPIRED", 50002],
]

columns = ["主分类", "子分类", "枚举常量", "code"]
df = pd.DataFrame(rows, columns=columns)
df.to_excel("被动行为埋点事件枚举-主子分类.xlsx", index=False)
print("Excel表格已生成：doc/被动行为埋点事件枚举-主子分类.xlsx")