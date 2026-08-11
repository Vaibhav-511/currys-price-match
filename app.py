import re
import requests
from bs4 import BeautifulSoup
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Currys Price Match", page_icon="⚡", layout="centered"
)

# Header UI
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


def resolve_barcode_to_title(barcode, api_key):
    """Converts a raw 12/13-digit EAN barcode into a full product title."""
    url = f"https://serpapi.com/search.json?q={barcode}&engine=google&gl=ie&hl=en&api_key={api_key}"
    try:
        res = requests.get(url, timeout=5).json()
        organic = res.get("organic_results", [])
        if organic:
            raw_title = organic[0].get("title", "")
            # Remove generic store tags like "| Currys" or "- Amazon"
            clean_title = (
                raw_title.split("|")[0].split("-")[0].split(":")[0].strip()
            )
            return clean_title
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
        resp = requests.get(url, headers=headers, timeout=4)
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
    search_term = clean_query

    # Step 1: If input is a numeric barcode, convert it to product title
    if clean_query.isdigit():
        with st.spinner("Converting barcode to product name..."):
            resolved_name = resolve_barcode_to_title(
                clean_query, SERPAPI_KEY
            )
            if resolved_name != clean_query:
                st.info(f"📦 Barcode Identifed: **{resolved_name}**")
                search_term = resolved_name

    st.markdown("---")
    st.markdown(f"#### Results for: **'{search_term}'**")

    # Step 2: Search competitor websites using the exact product name
    with st.spinner("Searching competitor live prices..."):
        for name, domain in RETAILERS.items():
            with st.container(border=True):
                col1, col2 = st.columns([2.5, 1.2])

                params = {
                    "q": f"site:{domain} {search_term}",
                    "engine": "google",
                    "gl": "ie",
                    "hl": "en",
                    "api_key": SERPAPI_KEY,
                }

                try:
                    res = requests.get(
                        "https://serpapi.com/search.json", params=params
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
                        st.caption("Error fetching retailer data.")
                    with col2:
                        st.metric(label="Live Price", value="Error")
                        st.error("Failed")
