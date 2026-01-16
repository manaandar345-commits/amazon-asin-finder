from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}
def has_renewed_offer(asin):
    url = f"https://www.amazon.sa/dp/{asin}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        return False

    page = r.text.lower()

    keywords = [
        "renewed",
        "refurbished",
        "amazon renewed",
        "used",
        "condition=used",
        "مجددة",
        "مستعملة"
    ]

    return any(k in page for k in keywords)

HTML = """
<!doctype html>
<html>
<head>
    <title>Amazon ASIN Finder</title>
    <style>
        body {
            font-family: Arial, Helvetica, sans-serif;
            background: linear-gradient(135deg, #232f3e, #131a22);
            height: 100vh;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #111;
        }
        .card {
            background: #fff;
            width: 420px;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 15px 40px rgba(0,0,0,0.35);
        }
        h2 {
            margin-top: 0;
            text-align: center;
            color: #232f3e;
        }
        input {
            width: 100%;
            padding: 12px;
            font-size: 15px;
            margin-top: 10px;
            border-radius: 6px;
            border: 1px solid #ccc;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            margin-top: 15px;
            padding: 12px;
            font-size: 15px;
            background: #febd69;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
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
            text-align: center;
            word-break: break-all;
        }
        .footer {
            margin-top: 15px;
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
            Smart ASIN detection • Amazon.sa
        </div>
    </div>
</body>
</html>
"""

def normalize(text):
    return text.lower().replace("-", " ").replace(",", " ")


def extract_keywords(text):
    tokens = normalize(text).split()
    important = []
    for t in tokens:
        if (
            "ipad" in t
            or "iphone" in t
            or "air" in t
            or "mini" in t
            or "pro" in t
            or "gb" in t
            or t.isdigit()
            or "wifi" in t
            or "cellular" in t
            or "4g" in t
            or "5g" in t
        ):
            important.append(t)
    return important


def title_matches(search, title):
    s_keys = extract_keywords(search)
    t = normalize(title)

    for key in s_keys:
        if key not in t:
            return False

    return True


def find_renewed_asin(product):
    query = urllib.parse.quote_plus(product)
    search_url = f"https://www.amazon.sa/s?k={query}"
    r = requests.get(search_url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    for div in soup.select("div[data-asin]"):
        asin = div.get("data-asin")
        if not asin:
            continue

        # open ASIN page
        url = f"https://www.amazon.sa/dp/{asin}"
        p = requests.get(url, headers=HEADERS, timeout=15)
        if p.status_code != 200:
            continue

        page = p.text.lower()

        # check refurbished / used
        keywords = [
            "renewed",
            "refurbished",
            "amazon renewed",
            "used",
            "condition=used",
            "مجددة",
            "مستعملة"
        ]

        if not any(k in page for k in keywords):
            continue

        # extract title
        psoup = BeautifulSoup(p.text, "html.parser")
        title_tag = psoup.find("span", {"id": "productTitle"})
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)

        # FINAL CHECK: exact match
        if title_matches(product, title):
            return asin

        time.sleep(1)

    return "NOT LISTED"

    url = f"https://www.amazon.sa/dp/{asin}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        return False

    page = r.text.lower()

    keywords = [
        "renewed",
        "refurbished",
        "amazon renewed",
        "used",
        "condition=used",
        "مجددة",
        "مستعملة"
    ]

    return any(word in page for word in keywords)


def find_renewed_asin(product):
    query = urllib.parse.quote_plus(product)
    search_url = f"https://www.amazon.sa/s?k={query}"
    r = requests.get(search_url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    for div in soup.select("div[data-asin]"):
        asin = div.get("data-asin")
        if asin and has_renewed_offer(asin):
            return asin
        time.sleep(1)

    return "NOT LISTED"


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        product = request.form["product"]
        result = find_renewed_asin(product)
    return render_template_string(HTML, result=result)


if __name__ == "__main__":
  import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



