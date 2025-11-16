import requests
from typing import Optional, Dict
from config.settings import ESA_ACCESS_TOKEN, ESA_TEAM_NAME, ESA_API_BASE


class EsaClient:
    def __init__(self):
        self.token = ESA_ACCESS_TOKEN
        self.team_name = ESA_TEAM_NAME
        self.base_url = f"{ESA_API_BASE}/teams/{self.team_name}"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def get_post_by_number(self, post_number: int) -> Optional[Dict]:
        """記事番号から記事を取得"""
        url = f"{self.base_url}/posts/{post_number}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"esa API Error: {e}")
            return None
    
    def extract_post_number_from_url(self, url: str) -> Optional[int]:
        """esaのURLから記事番号を抽出"""
        # https://team.esa.io/posts/123 -> 123
        import re
        match = re.search(r'/posts/(\d+)', url)
        if match:
            return int(match.group(1))
        return None
    
    def get_post_from_url(self, url: str) -> Optional[Dict]:
        """URLから記事を取得"""
        post_number = self.extract_post_number_from_url(url)
        if post_number:
            return self.get_post_by_number(post_number)
        return None