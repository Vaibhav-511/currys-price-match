import re
import requests
from bs4 import BeautifulSoup
import streamlit as st

st.set_page_config(
    page_title="Currys Price Match", page_icon="⚡", layout="centered"
)

st.markdown(
    "⚡ Currys Price Match",
    unsafe_allow_html=True,
)
st.markdown(
    "Smart Irish Competitor Price Scanner",
    unsafe_allow_html=True,
)

query = st.text_input(
    "Product Search",
    placeholder="Type EAN barcode, model number, or product name...",
)

RETAILERS = {
    "Harvey Norman": "harveynorman.ie",
    "DID Electrical": "did.ie",
    "Power City": "powercity.ie",
    "Smyths Toys": "smythstoys.com",
    "Amazon IE": "amazon.ie",
    "Expert Ireland": "expert.ie",
}

SERPAPI_KEY = "PASTE_YOUR_SERPAPI_KEY_HERE"


def clean_search_keywords(title):
    """Clean extra fluff words and keep the top 4-5 core keywords."""
    # Remove special characters
    clean = re.sub(r"[^\w\s]", " ", title)
    words = clean.split()

    # Filter out common junk words
    ignore_words = {
        "buy",
        "online",
        "currys",
        "ireland",
        "ie",
        "free",
        "delivery",
        "store",
        "shop",
        "official",
    }
    filtered = [w for w in words if w.lower() not in ignore_words]

    # Return top 4 core words for standard searches, top 5 for longer ones
    return " ".join(filtered[:5])


def resolve_barcode(barcode, api_key):
    """Converts a raw barcode to product name using open UPC database + fallback."""
    # 1. Try free UPC database API first
    try:
        upc_url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}"
        res = requests.get(upc_url, timeout=3).json()
        items = res.get("items", [])
        if items:
            return items[0].get("title", "")
    except Exception:
        pass

    # 2. Fallback to Google via SerpAPI
    try:
        serp_url = f"https://serpapi.com/search.json?q={barcode}&engine=google&gl=ie&hl=en&api_key={api_key}"
        res = requests.get(serp_url, timeout=4).json()
        organic = res.get("organic_results", [])
        if organic:
            return organic[0].get("title", "")
    except Exception:
        pass

    return barcode


def parse_snippet_price(result):
    if "price" in result:
        return str(result["price"])
    if "extracted_price" in result:
        return f"€{result['extracted_price']}"

    rich_snippet = result.get("rich_snippet", {})
    detected = rich_snippet.get("detected_extensions", {})
    if "price" in detected:
        return f"€{detected['price']}"

    full_text = f"{result.get('title', '')} {result.get('snippet', '')}"
    price_matches = re.findall(
        r"(?:€|EUR\s?)\s?[\d,]+(?:\.\d{2})?|[\d,]+(?:\.\d{2})?\s?(?:€|EUR)",
        full_text,
        re.IGNORECASE,
    )

    if price_matches:
        return price_matches[0].strip()

    return None


def scrape_live_page_price(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=3)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            price_tags = soup.find_all(
                ["span", "p", "div"],
                class_=re.compile(r"price|amount|val|cost", re.I),
            )
            for tag in price_tags:
                text = tag.get_text()
                match = re.search(
                    r"€\s?[\d,]+(?:\.\d{2})?", text, re.IGNORECASE
                )
                if match:
                    return match.group(0).strip()
    except Exception:
        pass
    return None


if (
    st.button("🔍 Search Competitors", use_container_width=True, type="primary")
    and query
):
    clean_query = query.strip()
    search_keywords = clean_query

    # Convert numeric barcode if entered
    if clean_query.isdigit():
        with st.spinner("Decoding barcode..."):
            raw_title = resolve_barcode(clean_query, SERPAPI_KEY)
            search_keywords = clean_search_keywords(raw_title)
            st.info(
                f"📦 Barcode Detected: **{raw_title}**\n\n🔍 Searching as: **{search_keywords}**"
            )
    else:
        search_keywords = clean_search_keywords(clean_query)

    st.markdown("---")

    with st.spinner("Scanning competitor prices..."):
        for name, domain in RETAILERS.items():
            with st.container(border=True):
                col1, col2 = st.columns([2.5, 1.2])

                # Query using clean 4-word keywords
                params = {
                    "q": f"site:{domain} {search_keywords}",
                    "engine": "google",
                    "gl": "ie",
                    "hl": "en",
                    "api_key": SERPAPI_KEY,
                }

                try:
                    res = requests.get(
                        "https://serpapi.com/search.json", params=params
                    ).json()

                    # Check for API usage limit reached
                    if "error" in res:
                        with col1:
                            st.markdown(f"### {name}")
                            st.caption(f"API Note: {res['error']}")
                        with col2:
                            st.metric(label="Live Price", value="Limit")
                            st.error("API Limit")
                        continue

                    organic = res.get("organic_results", [])

                    # Fallback to broader search if site: operator yielded no result
                    if not organic:
                        fallback_params = {
                            "q": f"{search_keywords} {name} Ireland",
                            "engine": "google",
                            "gl": "ie",
                            "hl": "en",
                            "api_key": SERPAPI_KEY,
                        }
                        res = requests.get(
                            "https://serpapi.com/search.json",
                            params=fallback_params,
                        ).json()
                        organic = res.get("organic_results", [])

                    if organic:
                        top_match = organic[0]
                        title = top_match.get("title", "Product Found")
                        link = top_match.get("link", "#")

                        price = parse_snippet_price(top_match)

                        if not price and link != "#":
                            price = scrape_live_page_price(link)

                        with col1:
                            st.markdown(f"### {name}")
                            st.write(f"{title}")
                            st.markdown(f"[🔗 Open Direct Link]({link})")

                        with col2:
                            if price:
                                st.metric(label="Live Price", value=price)
                                st.success("In Stock / Found")
                            else:
                                st.metric(
                                    label="Live Price", value="Check Link"
                                )
                                st.warning("Price in Link")
                    else:
                        with col1:
                            st.markdown(f"### {name}")
                            st.caption("No matching product found.")
                        with col2:
                            st.metric(label="Live Price", value="-")
                            st.error("Unavailable")

                except Exception:
                    with col1:
                        st.markdown(f"### {name}")
                        st.caption("Error loading data.")
                    with col2:
                        st.metric(label="Live Price", value="Error")
                        st.error("Failed")
