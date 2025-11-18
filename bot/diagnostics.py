import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config.settings import SLACK_BOT_TOKEN, SLACK_APP_TOKEN, ESA_WATCH_CHANNEL_ID, ESA_SUMMARY_CHANNEL_IDS

"""Slack環境診断スクリプト

実行: uv run python bot/diagnostics.py

確認内容:
1. auth_test: Bot Tokenの整合性
2. conversations.list: 監視/要約チャンネルの存在確認とBot参加状況
3. scopes(簡易): auth_test情報とpermission系APIの応答
4. Socket Mode用 App Token の形式検査

Slack APIではイベント購読設定(app_mention など)を直接取得できないため、
メンション未反応時は管理画面で Event Subscriptions を再確認する必要があります。
"""

logger = logging.getLogger("slack_diagnostics")
logging.basicConfig(level=logging.INFO)


def run():
    if not SLACK_BOT_TOKEN:
        logger.error("SLACK_BOT_TOKEN が空です。 .env を確認してください。")
        return
    if not SLACK_APP_TOKEN:
        logger.warning("SLACK_APP_TOKEN が空です。Socket Mode が無効の可能性。")

    if not SLACK_APP_TOKEN.startswith("xapp-"):
        logger.warning("SLACK_APP_TOKEN の形式が xapp- ではありません。App-Level Token を再確認。")
    if not SLACK_BOT_TOKEN.startswith("xoxb-"):
        logger.warning("SLACK_BOT_TOKEN の形式が xoxb- ではありません。Bot Token を再確認。")

    client = WebClient(token=SLACK_BOT_TOKEN)

    # 1. auth_test
    try:
        auth = client.auth_test()
        logger.info(f"auth_test OK user_id={auth.get('user_id')} team={auth.get('team')} url={auth.get('url')}")
    except SlackApiError as e:
        logger.error(f"auth_test 失敗: {e.response.status_code} {e.response.data}")
        return

    # 2. channels list
    target_ids = set([cid for cid in [ESA_WATCH_CHANNEL_ID, *ESA_SUMMARY_CHANNEL_IDS] if cid])
    found = {}
    cursor = None
    types = ["public_channel", "private_channel"]
    try:
        while True:
            resp = client.conversations_list(types=",".join(types), limit=200, cursor=cursor)
            for ch in resp.get("channels", []):
                cid = ch.get("id")
                if cid in target_ids:
                    found[cid] = ch
            cursor = resp.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
    except SlackApiError as e:
        logger.error(f"conversations.list 失敗: {e.response.status_code} {e.response.data}")
    
    for cid in target_ids:
        if cid not in found:
            logger.warning(f"チャンネル未検出: {cid} (Bot未参加かID不一致)" )
        else:
            ch = found[cid]
            logger.info(f"チャンネル検出: {cid} name={ch.get('name')} is_member={ch.get('is_member')} is_private={ch.get('is_private')}" )
            if not ch.get('is_member'):
                logger.warning(f"Botはチャンネル {cid} に参加していません。/invite で追加してください。")

    # 3. permission info (利用できない/エラーはログとして参考にする)
    try:
        perm = client.api_call("apps.permissions.info")
        logger.info(f"permissions.info 応答: keys={list(perm.keys())}")
    except SlackApiError as e:
        logger.warning(f"apps.permissions.info 取得失敗 (権限不足か非対応): {e.response.status_code}")

    logger.info("診断完了。イベント未着の場合は: 1) Event Subscriptions(app_mention) 2) Bot招待 3) スコープ再インストール を確認してください。")


if __name__ == "__main__":
    run()
