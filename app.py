import streamlit as st

from src.hybrid_search import (
    hybrid_search,
    rerank_results,
)


st.set_page_config(
    page_title="Smart Component Search",
    layout="wide",
)


st.title("Smart Component Search")

st.write(
    "Search electronic components using semantic search, "
    "keyword matching, metadata filters, and reranking."
)


CATEGORY_OPTIONS = [
    "Any",
    "resistor",
    "capacitor",
    "led",
    "sensor",
    "microcontroller",
    "transistor",
    "relay",
    "motor",
    "switch",
    "connector",
]


with st.sidebar:
    st.header("Filters")

    category_choice = st.selectbox(
        "Category",
        CATEGORY_OPTIONS,
    )

    use_price_filter = st.checkbox(
        "Set maximum price"
    )

    max_cost = None

    if use_price_filter:
        max_cost = st.number_input(
            "Maximum price ($)",
            min_value=0.0,
            value=5.0,
            step=0.25,
        )

    use_voltage_filter = st.checkbox(
        "Set required voltage"
    )

    target_voltage = None

    if use_voltage_filter:
        target_voltage = st.number_input(
            "Required voltage (V)",
            min_value=0.0,
            value=5.0,
            step=0.1,
        )


category = (
    None
    if category_choice == "Any"
    else category_choice
)


query = st.text_input(
    "What component are you looking for?",
    placeholder="Example: cheap 5V temperature sensor",
)


search_clicked = st.button(
    "Search Components",
    type="primary",
    use_container_width=True,
)


if search_clicked:
    if not query.strip():
        st.warning(
            "Enter a search query first."
        )

    else:
        with st.spinner(
            "Searching components..."
        ):
            try:
                hybrid_results = hybrid_search(
                    query=query,
                    category=category,
                    max_cost=max_cost,
                    target_voltage=target_voltage,
                )

                results = rerank_results(
                    query=query,
                    results=hybrid_results,
                    category=category,
                    max_cost=max_cost,
                    target_voltage=target_voltage,
                )

            except Exception as error:
                st.error(
                    f"Search failed: {error}"
                )
                st.stop()

        if not results:
            st.warning(
                "No components matched your search and filters."
            )

        else:
            st.success(
                f"Found {len(results)} matching components."
            )

            st.subheader(
                "Top Results"
            )

            for rank, result in enumerate(
                results[:10],
                start=1,
            ):
                record = result["record"]

                with st.container(
                    border=True
                ):
                    left, right = st.columns(
                        [3, 1]
                    )

                    with left:
                        st.subheader(
                            f"#{rank} — {record['name']}"
                        )

                        st.write(
                            record["description"]
                        )

                        st.caption(
                            f"Component ID: {record['id']}"
                        )

                    with right:
                        st.metric(
                            "Estimated Cost",
                            f"${record['estimated_cost_usd']:.2f}",
                        )

                    col1, col2, col3, col4 = st.columns(
                        4
                    )

                    with col1:
                        st.write("**Category**")
                        st.write(
                            record["category"].title()
                        )

                    with col2:
                        st.write("**Voltage Range**")
                        st.write(
                            f"{record['voltage_min_v']}–"
                            f"{record['voltage_max_v']} V"
                        )

                    with col3:
                        st.write("**Material**")
                        st.write(
                            record["material"].title()
                        )

                    with col4:
                        st.write("**Size**")
                        st.write(
                            f"{record['size_mm']} mm"
                        )

                    st.write(
                        "**Keywords:** "
                        + ", ".join(
                            record["keywords"]
                        )
                    )

                    st.caption(
                        "Search score: "
                        f"{result['rerank_score']:.4f}"
                    )


with st.expander(
    "How does this search work?"
):
    st.write(
        """
        The system combines four retrieval techniques:

        1. Semantic vector search using embeddings.
        2. Keyword matching.
        3. Metadata filters for category, price, and voltage.
        4. Reranking to improve the final result order.

        The component records are stored in a local Chroma vector database.
        """
    )


with st.expander(
    "Project benchmark"
):
    st.write(
        """
        The Smart Component Search system was evaluated on
        20 search queries.

        Vector Search:
        - Top-1: 20/20
        - Top-3: 20/20

        Keyword Search:
        - Top-1: 20/20
        - Top-3: 20/20

        Hybrid Search:
        - Top-1: 20/20
        - Top-3: 20/20

        Reranked Search:
        - Top-1: 20/20
        - Top-3: 20/20

        The benchmark uses a structured synthetic educational dataset,
        so the results should not be treated as performance on a
        large real-world component catalog.
        """
    )