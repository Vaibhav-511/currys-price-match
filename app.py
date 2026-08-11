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
    "Exact Irish Competitor Price Scanner",
    unsafe_allow_html=True,
)

query = st.text_input(
    "Product Search",
    placeholder="Enter EAN code, exact model number, or product name...",
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
    st.markdown("---")
    st.markdown(f"#### Results for: **'{query}'**")

    # Clean raw input
    clean_query = query.strip()
    is_numeric = clean_query.isdigit()

    with st.spinner("Finding exact matching product and prices..."):
        for name, domain in RETAILERS.items():
            with st.container(border=True):
                col1, col2 = st.columns([2.5, 1.2])

                # Use quote marks on EAN codes to force exact match search
                search_term = (
                    f'"{clean_query}"' if is_numeric else clean_query
                )

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

                    # Fallback to broader search if quotes were too strict
                    if not organic and is_numeric:
                        fallback_params = {
                            "q": f"site:{domain} {clean_query}",
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
                            st.caption("No exact match found.")
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
