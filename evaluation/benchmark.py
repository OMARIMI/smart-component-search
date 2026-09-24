import json
from pathlib import Path
from datetime import datetime, timezone

from src.hybrid_search import (
    vector_search,
    keyword_search,
    hybrid_search,
    rerank_results,
)


OUTPUT_PATH = Path("evaluation/benchmark_results.json")


TEST_CASES = [
    {
        "query": "cheap temperature sensor",
        "category": "sensor",
        "max_cost": 3,
        "target_voltage": 5,
        "relevant_ids": ["COMP-0037", "COMP-0042", "COMP-0121"],
    },
    {
        "query": "humidity sensor",
        "category": "sensor",
        "max_cost": None,
        "target_voltage": 5,
        "relevant_ids": ["COMP-0038", "COMP-0043", "COMP-0048"],
    },
    {
        "query": "light sensor",
        "category": "sensor",
        "max_cost": None,
        "target_voltage": 5,
        "relevant_ids": ["COMP-0039", "COMP-0044"],
    },
    {
        "query": "distance sensor",
        "category": "sensor",
        "max_cost": None,
        "target_voltage": 5,
        "relevant_ids": ["COMP-0040", "COMP-0045"],
    },
    {
        "query": "motion sensor",
        "category": "sensor",
        "max_cost": None,
        "target_voltage": 5,
        "relevant_ids": ["COMP-0041", "COMP-0046"],
    },
    {
        "query": "Wi-Fi microcontroller",
        "category": "microcontroller",
        "max_cost": None,
        "target_voltage": None,
        "relevant_ids": ["COMP-0051", "COMP-0055", "COMP-0059"],
    },
    {
        "query": "low power microcontroller",
        "category": "microcontroller",
        "max_cost": None,
        "target_voltage": None,
        "relevant_ids": ["COMP-0052", "COMP-0056", "COMP-0060"],
    },
    {
        "query": "NPN transistor",
        "category": "transistor",
        "max_cost": None,
        "target_voltage": None,
        "relevant_ids": ["COMP-0061", "COMP-0065", "COMP-0069"],
    },
    {
        "query": "N-channel MOSFET",
        "category": "transistor",
        "max_cost": None,
        "target_voltage": None,
        "relevant_ids": ["COMP-0063", "COMP-0067", "COMP-0071"],
    },
    {
        "query": "5V relay",
        "category": "relay",
        "max_cost": None,
        "target_voltage": 5,
        "relevant_ids": [
            "COMP-0073",
            "COMP-0076",
            "COMP-0079",
            "COMP-0082",
        ],
    },
    {
        "query": "solid state relay",
        "category": "relay",
        "max_cost": None,
        "target_voltage": None,
        "relevant_ids": [
            "COMP-0075",
            "COMP-0078",
            "COMP-0081",
            "COMP-0084",
        ],
    },
    {
        "query": "servo motor",
        "category": "motor",
        "max_cost": None,
        "target_voltage": None,
        "relevant_ids": ["COMP-0088", "COMP-0092", "COMP-0096"],
    },
    {
        "query": "stepper motor",
        "category": "motor",
        "max_cost": None,
        "target_voltage": None,
        "relevant_ids": ["COMP-0087", "COMP-0091", "COMP-0095"],
    },
    {
        "query": "push button switch",
        "category": "switch",
        "max_cost": None,
        "target_voltage": None,
        "relevant_ids": ["COMP-0097", "COMP-0101", "COMP-0105"],
    },
    {
        "query": "limit switch",
        "category": "switch",
        "max_cost": None,
        "target_voltage": None,
        "relevant_ids": ["COMP-0100", "COMP-0104", "COMP-0108"],
    },
    {
        "query": "USB connector",
        "category": "connector",
        "max_cost": None,
        "target_voltage": None,
        "relevant_ids": ["COMP-0112", "COMP-0116", "COMP-0120"],
    },
    {
        "query": "JST connector",
        "category": "connector",
        "max_cost": None,
        "target_voltage": None,
        "relevant_ids": ["COMP-0111", "COMP-0115", "COMP-0119"],
    },
    {
        "query": "metal film resistor",
        "category": "resistor",
        "max_cost": None,
        "target_voltage": None,
        "relevant_ids": [
            "COMP-0002",
            "COMP-0004",
            "COMP-0006",
            "COMP-0008",
            "COMP-0010",
            "COMP-0012",
        ],
    },
    {
        "query": "electrolytic capacitor",
        "category": "capacitor",
        "max_cost": None,
        "target_voltage": None,
        "relevant_ids": [
            "COMP-0014",
            "COMP-0016",
            "COMP-0018",
            "COMP-0020",
            "COMP-0022",
            "COMP-0024",
        ],
    },
    {
        "query": "blue LED",
        "category": "led",
        "max_cost": None,
        "target_voltage": None,
        "relevant_ids": ["COMP-0027", "COMP-0031", "COMP-0035"],
    },
]


def extract_ids(results):
    return [result["id"] for result in results]


def score_result(result_ids, relevant_ids):
    relevant = set(relevant_ids)

    top_1 = (
        len(result_ids) >= 1
        and result_ids[0] in relevant
    )

    top_3 = any(
        component_id in relevant
        for component_id in result_ids[:3]
    )

    return top_1, top_3


def run_method(method_name, test_case):
    query = test_case["query"]
    category = test_case["category"]
    max_cost = test_case["max_cost"]
    target_voltage = test_case["target_voltage"]

    if method_name == "vector":
        results = vector_search(
            query=query,
            category=category,
            max_cost=max_cost,
            target_voltage=target_voltage,
            limit=5,
        )

    elif method_name == "keyword":
        results = keyword_search(
            query=query,
            category=category,
            max_cost=max_cost,
            target_voltage=target_voltage,
        )

    elif method_name == "hybrid":
        results = hybrid_search(
            query=query,
            category=category,
            max_cost=max_cost,
            target_voltage=target_voltage,
        )

    elif method_name == "reranked":
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

    else:
        raise ValueError(
            f"Unknown method: {method_name}"
        )

    result_ids = extract_ids(results)

    top_1, top_3 = score_result(
        result_ids,
        test_case["relevant_ids"],
    )

    return {
        "top_results": result_ids[:5],
        "top_1_success": top_1,
        "top_3_success": top_3,
    }


def calculate_summary(results, method):
    method_results = [
        result["methods"][method]
        for result in results
    ]

    total = len(method_results)

    top_1_count = sum(
        result["top_1_success"]
        for result in method_results
    )

    top_3_count = sum(
        result["top_3_success"]
        for result in method_results
    )

    return {
        "queries": total,
        "top_1_successes": top_1_count,
        "top_3_successes": top_3_count,
        "top_1_accuracy_percent": round(
            top_1_count / total * 100,
            1,
        ),
        "top_3_accuracy_percent": round(
            top_3_count / total * 100,
            1,
        ),
    }


def main():
    methods = [
        "vector",
        "keyword",
        "hybrid",
        "reranked",
    ]

    all_results = []

    print("\nSMART COMPONENT SEARCH BENCHMARK")
    print("=" * 40)

    for number, test_case in enumerate(
        TEST_CASES,
        start=1,
    ):
        print(
            f"\n[{number}/20] "
            f"{test_case['query']}"
        )

        result = {
            "id": number,
            "query": test_case["query"],
            "filters": {
                "category": test_case["category"],
                "max_cost": test_case["max_cost"],
                "target_voltage": test_case[
                    "target_voltage"
                ],
            },
            "relevant_ids": test_case[
                "relevant_ids"
            ],
            "methods": {},
        }

        for method in methods:
            method_result = run_method(
                method,
                test_case,
            )

            result["methods"][
                method
            ] = method_result

            top_1_text = (
                "PASS"
                if method_result[
                    "top_1_success"
                ]
                else "FAIL"
            )

            top_3_text = (
                "PASS"
                if method_result[
                    "top_3_success"
                ]
                else "FAIL"
            )

            print(
                f"  {method:8} "
                f"Top-1: {top_1_text} | "
                f"Top-3: {top_3_text}"
            )

        all_results.append(result)

    summary = {
        method: calculate_summary(
            all_results,
            method,
        )
        for method in methods
    }

    report = {
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "total_queries": len(TEST_CASES),
        "summary": summary,
        "results": all_results,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n")
    print("=" * 40)
    print("FINAL RESULTS")
    print("=" * 40)

    for method in methods:
        data = summary[method]

        print()
        print(method.upper())

        print(
            f"Top-1: "
            f"{data['top_1_successes']}"
            f"/{data['queries']} "
            f"("
            f"{data['top_1_accuracy_percent']}%"
            f")"
        )

        print(
            f"Top-3: "
            f"{data['top_3_successes']}"
            f"/{data['queries']} "
            f"("
            f"{data['top_3_accuracy_percent']}%"
            f")"
        )

    print()
    print(
        "Results saved to: "
        "evaluation/benchmark_results.json"
    )


if __name__ == "__main__":
    main()