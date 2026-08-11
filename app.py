import re
import requests
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
    "Live Irish Competitor Price Scanner",
    unsafe_allow_html=True,
)

# Search Input Box
query = st.text_input(
    "Product Search",
    placeholder="Type EAN code, model number, or product name...",
)

RETAILERS = {
    "Harvey Norman": "harveynorman.ie",
    "DID Electrical": "did.ie",
    "Power City": "powercity.ie",
    "Smyths Toys": "smythstoys.com/ie",
    "Amazon IE": "amazon.ie",
    "Expert Ireland": "expert.ie",
}

SERPAPI_KEY = "PASTE_YOUR_SERPAPI_KEY_HERE"


def parse_price(result):
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


if (
    st.button("🔍 Search Competitors", use_container_width=True, type="primary")
    and query
):
    st.markdown("---")
    st.markdown(f"#### Results for: **'{query}'**")

    with st.spinner("Checking live store prices..."):
        for name, domain in RETAILERS.items():
            search_url = f"https://serpapi.com/search.json?q=site:{domain}+{query}&engine=google&gl=ie&hl=en&api_key={SERPAPI_KEY}"

            # Modern Card Container for each retailer
            with st.container(border=True):
                col1, col2 = st.columns([2.5, 1.2])

                try:
                    response = requests.get(search_url).json()
                    organic = response.get("organic_results", [])

                    if organic:
                        top_match = organic[0]
                        title = top_match.get("title", "Product Found")
                        link = top_match.get("link", "#")
                        price = parse_price(top_match)

                        with col1:
                            st.markdown(f"### {name}")
                            st.write(f"{title}")
                            st.markdown(f"[🔗 Open Direct Link]({link})")

                        with col2:
                            if price:
                                st.metric(
                                    label="Live Price",
                                    value=price,
                                )
                                st.success("In Stock / Found")
                            else:
                                st.metric(label="Live Price", value="Check Link")
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
                        st.caption("Unable to load retailer data.")
                    with col2:
                        st.metric(label="Live Price", value="Error")
                        st.error("Failed")
