# --- THE AXIOM: Parser Logic & Regression Tests ---
# พิกัด: tests/test_parser_logic.py

import pytest
import re
from bs4 import BeautifulSoup

# --- Mock Engine (จำลองการทำงานของ scraper.py เพื่อทำ Unit Test) ---
def parse_mock_html(html: str, css: str, regex_fb: str) -> float | None:
    soup = BeautifulSoup(html, 'html.parser')
    for s in soup(['script', 'style']): s.decompose()
    
    raw_val = None
    if css:
        elem = soup.select_one(css)
        raw_val = elem.get_text(strip=True) if elem else None
        
    if not raw_val and regex_fb:
        clean_text = soup.get_text(separator=' ').replace(',', '').replace(' ', '')
        match = re.search(regex_fb, clean_text)
        if match:
            # ใช้ Group 1 ถ้ามีกำหนดใน Regex, ถ้าไม่มีใช้ Group 0
            raw_val = match.group(1) if len(match.groups()) > 0 else match.group(0)
            
    if not raw_val: return None
    
    # Clean & Validate
    clean_str = ''.join(c for c in str(raw_val) if c.isdigit() or c == '.')
    try:
        val = float(clean_str)
        if val in [60000.0, 10000.0, 0.0] or val <= 0: return None
        return val
    except:
        return None

# --- Test Cases ---

def test_finance_index_css_parsing():
    """ทดสอบพิกัด CSS สำหรับตลาดหุ้น (เช่น Google Finance)"""
    mock_html = """
    <html>
        <body>
            <div class="YMlKec fxKbKc">39,069.23</div>
            <div class="other-data">60000.0</div>
        </body>
    </html>
    """
    result = parse_mock_html(mock_html, css="div.YMlKec.fxKbKc", regex_fb=None)
    assert result == 39069.23, f"Expected 39069.23, got {result}"

def test_lottery_regex_fallback():
    """ทดสอบ Regex Fallback เมื่อ CSS พัง (โครงสร้างเว็บเปลี่ยน)"""
    mock_html = """
    <html>
        <body>
            <!-- สมมติว่า id 'number-first' หายไป -->
            <div class="changed-class">
                <h2>ผลการออกรางวัลที่ 1</h2>
                <span>827364</span>
            </div>
        </body>
    </html>
    """
    # ทดสอบการใช้ Regex ทะลวงหาเลขหลังคำว่า "รางวัลที่ 1"
    regex = r"รางวัลที่\s?1.*?(\d{6})"
    result = parse_mock_html(mock_html, css="strong#number-first", regex_fb=regex)
    assert result == 827364.0, f"Regex Fallback failed, got {result}"

def test_blacklist_rejection():
    """ทดสอบระบบดีดเลขขยะ (Zero-Trust Validation)"""
    mock_html = """
    <html>
        <body>
            <span class="mkc-stock_prices_price">60,000.00</span>
        </body>
    </html>
    """
    result = parse_mock_html(mock_html, css="span.mkc-stock_prices_price", regex_fb=None)
    assert result is None, "Security Violation: Blacklisted value 60000.0 bypassed the filter!"

def test_negative_value_rejection():
    """ทดสอบการปฏิเสธค่าติดลบ"""
    mock_html = """<div class="result">-150.50</div>"""
    result = parse_mock_html(mock_html, css="div.result", regex_fb=None)
    assert result is None, "Validation Error: Negative values should be rejected."