import json
import re
from pathlib import Path


DATA_PATH = Path("data/components.json")


def tokenize(text):
    return set(
        re.findall(
            r"[a-zA-Z0-9.]+",
            text.lower()
        )
    )


def load_records():
    records = json.loads(
        DATA_PATH.read_text(encoding="utf-8")
    )

    return {
        record["id"]: record
        for record in records
    }


def rerank_results(
    query,
    results,
    category=None,
    max_cost=None,
    target_voltage=None,
):
    records = load_records()

    query_terms = tokenize(query)

    cheap_words = {
        "cheap",
        "budget",
        "affordable",
        "low-cost",
        "inexpensive",
    }

    wants_low_cost = bool(
        query_terms.intersection(cheap_words)
    )

    reranked = []

    for result in results:
        component_id = result["id"]

        if component_id not in records:
            continue

        record = records[component_id]

        score = result["hybrid_score"] * 100

        name_terms = tokenize(record["name"])
        category_terms = tokenize(record["category"])
        description_terms = tokenize(
            record["description"]
        )

        name_matches = len(
            query_terms.intersection(name_terms)
        )

        category_matches = len(
            query_terms.intersection(category_terms)
        )

        description_matches = len(
            query_terms.intersection(
                description_terms
            )
        )

        score += name_matches * 4
        score += category_matches * 2
        score += description_matches * 0.5

        if category:
            if (
                record["category"].lower()
                == category.lower()
            ):
                score += 3

        if target_voltage is not None:
            if (
                record["voltage_min_v"]
                <= target_voltage
                <= record["voltage_max_v"]
            ):
                score += 3

        if max_cost is not None:
            if (
                record["estimated_cost_usd"]
                <= max_cost
            ):
                score += 2

        if wants_low_cost:
            cost = record[
                "estimated_cost_usd"
            ]

            score += 5 / (1 + cost)

        reranked.append(
            {
                "id": component_id,
                "record": record,
                "rerank_score": score,
                "hybrid_score": result[
                    "hybrid_score"
                ],
            }
        )

    reranked.sort(
        key=lambda item: (
            -item["rerank_score"],
            item["record"][
                "estimated_cost_usd"
            ],
        )
    )

    return reranked


def print_reranked_results(
    results,
    top_k=5,
):
    print("\nRERANKED RESULTS\n")

    for rank, result in enumerate(
        results[:top_k],
        start=1,
    ):
        record = result["record"]

        print(
            f"{rank}. {record['name']}"
        )

        print(
            f"   ID: {record['id']}"
        )

        print(
            f"   Category: "
            f"{record['category']}"
        )

        print(
            f"   Voltage: "
            f"{record['voltage_min_v']} - "
            f"{record['voltage_max_v']} V"
        )

        print(
            f"   Cost: $"
            f"{record['estimated_cost_usd']}"
        )

        print(
            f"   Rerank score: "
            f"{result['rerank_score']:.4f}"
        )

        print()