import streamlit as st
import requests

st.set_page_config(page_title="Currys Price Match", layout="wide")

st.title("⚡ Currys Price Match Finder")
st.write("Search Irish competitor pricing instantly.")

query = st.text_input("Enter EAN Code or Product Model Number:", "")

RETAILERS = {
    "Harvey Norman": "harveynorman.ie",
    "DID Electrical": "did.ie",
    "Power City": "powercity.ie",
    "Smyths Toys": "smythstoys.com/ie",
    "Amazon IE": "amazon.ie",
    "Expert Ireland": "expert.ie"
}

SERPAPI_KEY = "ae5b948cffb6691798333d5a96dd29bcc07a27140271a720b392f5aca8e9e2f8"

if st.button("Search All Retailers") and query:
    results = []
    with st.spinner("Searching live retailer prices..."):
        for name, domain in RETAILERS.items():
            search_url = f"https://serpapi.com/search.json?q=site:{domain}+{query}&engine=google&gl=ie&hl=en&api_key={SERPAPI_KEY}"
            response = requests.get(search_url).json()
            organic = response.get("organic_results", [])

            if organic:
                top_match = organic[0]
                title = top_match.get("title", "Found")
                link = top_match.get("link", "#")
                snippet = top_match.get("snippet", "")

                price = "Check Link"
                for word in snippet.split():
                    if "€" in word or "EUR" in word:
                        price = word
                        break

                results.append({
                    "Retailer": name,
                    "Title": title,
                    "Price": price,
                    "Status": "Available",
                    "Link": link
                })
            else:
                results.append({
                    "Retailer": name,
                    "Title": "Not Found",
                    "Price": "-",
                    "Status": "Unavailable",
                    "Link": "#"
                })

    st.subheader(f"Results for: '{query}'")
    for item in results:
        col1, col2, col3, col4 = st.columns([2, 4, 2, 2])
        col1.write(f"**{item['Retailer']}**")
        col2.write(item['Title'])
        col3.write(item['Price'])
        if item['Status'] == "Available":
            col4.markdown(f"[🔗 View Product]({item['Link']})")
        else:
            col4.write("❌ Unavailable")
        st.divider()
