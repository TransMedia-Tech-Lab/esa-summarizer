from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from app.esa_client import EsaClient
from app.gemini_client import GeminiClient
from config.settings import SLACK_BOT_TOKEN, SLACK_APP_TOKEN
import re


class SlackBot:
    def __init__(self):
        self.app = App(token=SLACK_BOT_TOKEN)
        self.esa_client = EsaClient()
        self.gemini_client = GeminiClient()
        self.setup_handlers()
    
    def setup_handlers(self):
        """メンションイベントのセットアップ"""
        
        @self.app.event("app_mention")
        def handle_mention(event, say):
            """Botへのメンションを処理"""
            text = event['text']
            user_id = event['user']
            
            # Botのメンション部分を除去
            # <@U12345678> https://... -> https://...
            text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()
            
            # ヘルプメッセージ
            if not text or 'help' in text.lower() or 'ヘルプ' in text:
                help_message = self._get_help_message()
                say(f"<@{user_id}>\n{help_message}")
                return
            
            # パラメータ解析
            length = "medium"
            style = "bullet"
            
            # --length short などのオプション解析
            length_match = re.search(r'--length\s+(short|medium|long)', text)
            if length_match:
                length = length_match.group(1)
                text = re.sub(r'--length\s+(short|medium|long)', '', text).strip()
            
            style_match = re.search(r'--style\s+(bullet|paragraph)', text)
            if style_match:
                style = style_match.group(1)
                text = re.sub(r'--style\s+(bullet|paragraph)', '', text).strip()
            
            # URL抽出
            url_match = re.search(r'https?://[^\s]+', text)
            if not url_match:
                say(f"<@{user_id}> ❌ エラー: esaのURLを指定してください\n\n{self._get_help_message()}")
                return
            
            url = url_match.group(0)
            
            # 処理中メッセージ
            say(f"<@{user_id}> 📝 要約を生成中です... (長さ: {length}, 形式: {style})")
            
            # esa記事取得
            post = self.esa_client.get_post_from_url(url)
            if not post:
                say(f"<@{user_id}> ❌ 記事の取得に失敗しました。URLを確認してください。")
                return
            
            # 記事データ取得
            post_data = post.get('post', post)
            title = post_data.get('name', 'タイトルなし')
            body = post_data.get('body_md', '')
            category = post_data.get('category', '')
            updated_at = post_data.get('updated_at', '')
            post_number = post_data.get('number', '')
            
            if not body:
                say(f"<@{user_id}> ❌ 記事の本文が空です。")
                return
            
            # 要約生成
            try:
                if len(body) > 10000:
                    summary = self.gemini_client.summarize_long_document(title, body, category)
                else:
                    summary = self.gemini_client.summarize(title, body, category, length, style)
                
                # 結果を整形して投稿
                message = self._format_summary_message(
                    title, category, updated_at, summary, url, length, style, post_number, len(body)
                )
                say(message)
                
            except Exception as e:
                say(f"<@{user_id}> ❌ 要約生成中にエラーが発生しました: {str(e)}")
    
    def _format_summary_message(self, title, category, updated_at, summary, url, length, style, post_number, body_length):
        """要約結果のメッセージを整形"""
        return f"""
📄 *{title}*
🔢 記事番号: #{post_number}
🏷 カテゴリ: {category if category else 'なし'}
📅 更新日: {updated_at[:10] if updated_at else '不明'}
📊 文字数: {body_length:,}文字

📝 *要約* (長さ: {length}, 形式: {style})
{summary}

🔗 <{url}|元記事を見る>
"""
    
    def _get_help_message(self):
        """ヘルプメッセージ"""
        return """
*esa Document Summarizer の使い方* 📚

**基本的な使い方:**
```
@esa-summarizer https://your-team.esa.io/posts/123
```

**オプション付き:**
```
@esa-summarizer https://your-team.esa.io/posts/123 --length short --style paragraph
```

**オプション一覧:**
- `--length short` : 短い要約（3-5文）
- `--length medium` : 標準の要約（10文程度）※デフォルト
- `--length long` : 詳細な要約（20文以上）

- `--style bullet` : 箇条書き形式 ※デフォルト
- `--style paragraph` : 段落形式

**例:**
```
@esa-summarizer https://your-team.esa.io/posts/456 --length long --style bullet
```
"""
    
    def start(self):
        """Botを起動"""
        handler = SocketModeHandler(self.app, SLACK_APP_TOKEN)
        print("⚡️ Bolt app is running!")
        print("💡 Botにメンションして要約を開始してください")
        print("   例: @esa-summarizer https://your-team.esa.io/posts/123")
        handler.start()