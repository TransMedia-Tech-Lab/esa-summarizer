import google.generativeai as genai
from config.settings import GEMINI_API_KEY, GEMINI_MODEL, SUMMARY_LENGTHS, SUMMARY_STYLES


class GeminiClient:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
    
    def summarize(
        self, 
        title: str, 
        body: str, 
        category: str = "", 
        length: str = "medium",
        style: str = "bullet"
    ) -> str:
        """ドキュメントを要約"""
        
        length_instruction = SUMMARY_LENGTHS.get(length, SUMMARY_LENGTHS["medium"])
        style_instruction = SUMMARY_STYLES.get(style, SUMMARY_STYLES["bullet"])
        
        prompt = f"""
あなたは研究室の文書要約アシスタントです。
教授が書いた技術文書や研究資料を、研究室メンバーが理解しやすいように要約してください。

要約のポイント:
1. 重要な技術的詳細を省略しない
2. 専門用語はそのまま使用
3. 結論や行動項目を明確に
4. 長さ: {length_instruction}
5. 形式: {style_instruction}

【タイトル】
{title}

【カテゴリ】
{category if category else "なし"}

【本文】
{body}

上記の内容を{style_instruction}で要約してください:
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"要約生成エラー: {str(e)}"
    
    def summarize_long_document(self, title: str, body: str, category: str = "") -> str:
        """長文ドキュメントを分割して要約"""
        # 簡易的な実装：10,000文字以上なら分割
        MAX_LENGTH = 10000
        
        if len(body) <= MAX_LENGTH:
            return self.summarize(title, body, category)
        
        # セクション分割（Markdown の ## で分割する簡易版）
        sections = body.split('\n## ')
        summaries = []
        
        for i, section in enumerate(sections[:5]):  # 最大5セクション
            section_title = section.split('\n')[0] if i > 0 else "導入部"
            summary = self.summarize(
                f"{title} - {section_title}", 
                section[:MAX_LENGTH], 
                category,
                length="short"
            )
            summaries.append(f"**{section_title}**\n{summary}")
        
        # 全体サマリー
        combined = "\n\n".join(summaries)
        return f"📑 **セクション別要約**\n\n{combined}\n\n*(長文のため分割要約しました)*"