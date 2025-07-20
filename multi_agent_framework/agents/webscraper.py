from .base import Agent
import requests
from bs4 import BeautifulSoup

class WebScraperAgent(Agent):
    def process(self, msg):
        # msg: {"type": "scrape", "url": ...}
        if msg["type"] == "scrape":
            try:
                resp = requests.get(msg["url"], timeout=10)
                soup = BeautifulSoup(resp.text, "html.parser")
                text = soup.get_text(separator=" ", strip=True)
                # Chunk if large
                chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
                for chunk in chunks:
                    self.send({"type": "text", "content": chunk}, "processing")
            except Exception as e:
                self.logger.error(f"Web scraping failed: {e}")