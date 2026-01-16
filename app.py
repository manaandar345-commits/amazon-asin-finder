from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import os

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

# ---------------- UI ----------------

HTML = """
<!doctype html>
<html>
<head>
    <title>Amazon.sa ASIN Finder</title>
    <style>
        body {
            font-family: Arial, Helvetica, sans-serif;
            background: linear-gradient(135deg, #232f3e, #131a22);
            height: 100vh;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .card {
            background: #fff;
            width: 460px;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 15px 40px rgba(0,0,0,0.35);
        }
        h2 {
            text-align: center;
            color: #232f3e;
        }
        input {
            width: 100%;
            padding: 12px;
            font-size: 15px;
            border-radius: 6px;
            border: 1px solid #ccc;
        }
        button {
            width: 100%;
            margin-top: 15px;
            padding: 12px;
            font-size: 15px;
            background: #febd69;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover {
            background: #f3a847;
        }
        .result {
            margin-top: 20px;
            padding: 12px;
            border-radius: 6px;
            background: #f1f3f6;
            font-weight: bold;
            word-break: break-all;
        }
        .footer {
            margin-top: 12px;
            text-align: center;
            font-size: 12px;
            color: #555;
        }
    </style>
</head>
<body>
    <div class="card">
        <h2>Amazon.sa ASIN Finder</h2>
        <form method="post">
            <input name="product" placeholder="Enter product name" required>
            <button type="submit">Find ASIN</button>
        </form>

        {% if result %}
        <div class="result">{{ result }}</div>
        {% endif %}

        <div class="footer">
            Smart matching • Confidence-based • Amazon.sa
        </div>
    </div>
</body>
</html>
"""

# ---------------- LOGIC ----------------

def extract_features(text):
    text = text.lower()
    return {
        "ipad": "ipad" in text,
        "iphone": "iphone" in text,
        "gen9": "9th" in text,
        "gen8": "8th" in text,
        "64gb": "64gb" in text,
        "128gb": "128gb" in text,
        "256gb": "256gb" in text,
        "wifi": "wifi" in text,
        "cellular": "cellular" in text or "4g" in text or "5g" in text,
        "silver": "silver" in text,
        "spacegray": "space gray" in text or "spacegrey" in text
    }


def confidence_score(search, title):
    s = extract_features(search)
    t = extract_features(title)

    score = 0
    details = []

    for key in s:
        if s[key]:
            if t.get(key):
                score += 10
                details.append(key)
            else:
                details.append(f"missing:{key}")

    return min(score, 100), details


def find_asin(product):
    query = urllib.parse.quote_plus(product)
    search_url = f"https://www.amazon.sa/s?k={query}"
    r = requests.get(search_url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    best_match = None
    best_score = 0
    best_details = ""

    for div in soup.select("div[data-asin]"):
        asin = div.get("data-asin")
        if not asin:
            continue

        url = f"https://www.amazon.sa/dp/{asin}"
        p = requests.get(url, headers=HEADERS, timeout=15)
        if p.status_code != 200:
            continue

        psoup = BeautifulSoup(p.text, "html.parser")
        title_tag = psoup.find("span", {"id": "productTitle"})
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)

        score, details = confidence_score(product, title)

        if score > best_score:
            best_score = score
            best_match = asin
            best_details = ", ".join(details)

        time.sleep(1)

    if best_match and best_score >= 40:
        return f"{best_match} | Confidence: {best_score}% | Details: {best_details}"

    return "NOT LISTED"

# ---------------- ROUTE ----------------

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        product = request.form["product"]
        result = find_asin(product)
    return render_template_string(HTML, result=result)

# ---------------- RUN ----------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
