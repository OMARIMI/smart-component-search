import json
from pathlib import Path

import chromadb
import requests


DATA_PATH = Path("data/components.json")

DB_PATH = "chroma_db"
COLLECTION_NAME = "components"

OLLAMA_URL = "http://127.0.0.1:11434/api/embed"
EMBED_MODEL = "embeddinggemma"


def load_records():
    return json.loads(
        DATA_PATH.read_text(encoding="utf-8")
    )


def save_records(records):
    DATA_PATH.write_text(
        json.dumps(
            records,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def create_embedding(text):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": EMBED_MODEL,
            "input": text,
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()["embeddings"][0]


def record_to_text(record):
    return (
        f"Name: {record['name']}. "
        f"Category: {record['category']}. "
        f"Description: {record['description']} "
        f"Voltage range: "
        f"{record['voltage_min_v']} to "
        f"{record['voltage_max_v']} volts. "
        f"Material: {record['material']}. "
        f"Size: {record['size_mm']} mm. "
        f"Estimated cost: "
        f"${record['estimated_cost_usd']}. "
        f"Keywords: "
        f"{', '.join(record['keywords'])}."
    )


def get_collection():
    client = chromadb.PersistentClient(
        path=DB_PATH
    )

    return client.get_collection(
        name=COLLECTION_NAME
    )


def update_vector_database(record):
    collection = get_collection()

    text = record_to_text(record)

    embedding = create_embedding(text)

    metadata = {
        "name": record["name"],
        "category": record["category"],
        "voltage_min_v": record["voltage_min_v"],
        "voltage_max_v": record["voltage_max_v"],
        "material": record["material"],
        "size_mm": record["size_mm"],
        "estimated_cost_usd": record[
            "estimated_cost_usd"
        ],
        "keywords": ", ".join(
            record["keywords"]
        ),
        "source_type": record["source_type"],
        "source_reference": record[
            "source_reference"
        ],
    }

    collection.upsert(
        ids=[record["id"]],
        documents=[text],
        embeddings=[embedding],
        metadatas=[metadata],
    )


def normalize_name(name):
    return " ".join(
        name.lower().split()
    )


def name_exists(
    records,
    name,
    ignore_id=None,
):
    target = normalize_name(name)

    for record in records:
        if ignore_id:
            if record["id"] == ignore_id:
                continue

        if normalize_name(
            record["name"]
        ) == target:
            return True

    return False


def generate_next_id(records):
    numbers = []

    for record in records:
        component_id = record["id"]

        if component_id.startswith(
            "COMP-"
        ):
            try:
                numbers.append(
                    int(
                        component_id.split(
                            "-"
                        )[1]
                    )
                )

            except ValueError:
                pass

    next_number = (
        max(numbers) + 1
        if numbers
        else 1
    )

    return (
        f"COMP-{next_number:04d}"
    )


def read_float(prompt):
    while True:
        value = input(
            prompt
        ).strip()

        try:
            return float(value)

        except ValueError:
            print(
                "Please enter a valid number."
            )


def read_keywords():
    value = input(
        "Keywords separated by commas: "
    ).strip()

    return [
        keyword.strip()
        for keyword in value.split(",")
        if keyword.strip()
    ]


def add_component():
    records = load_records()

    print(
        "\nADD COMPONENT\n"
    )

    name = input(
        "Name: "
    ).strip()

    if not name:
        print(
            "Name cannot be blank."
        )
        return

    if name_exists(
        records,
        name,
    ):
        print(
            "\nDuplicate blocked."
        )

        print(
            "A component with that "
            "name already exists."
        )

        return

    component_id = (
        generate_next_id(
            records
        )
    )

    category = input(
        "Category: "
    ).strip().lower()

    description = input(
        "Description: "
    ).strip()

    voltage_min = read_float(
        "Minimum voltage: "
    )

    voltage_max = read_float(
        "Maximum voltage: "
    )

    material = input(
        "Material: "
    ).strip()

    size_mm = read_float(
        "Size in mm: "
    )

    cost = read_float(
        "Estimated cost USD: "
    )

    keywords = read_keywords()

    source_reference = input(
        "Source reference: "
    ).strip()

    usage_permission = input(
        "Usage permission / source note: "
    ).strip()

    record = {
        "id": component_id,
        "name": name,
        "category": category,
        "description": description,
        "voltage_min_v": voltage_min,
        "voltage_max_v": voltage_max,
        "material": material,
        "size_mm": size_mm,
        "estimated_cost_usd": cost,
        "keywords": keywords,
        "source_type": "user-added",
        "source_reference": (
            source_reference
            or "local://user-added"
        ),
        "usage_permission": (
            usage_permission
            or "User-added educational record."
        ),
    }

    records.append(record)

    save_records(records)

    update_vector_database(
        record
    )

    print()
    print(
        f"Added {component_id}"
    )
    print(
        f"Name: {name}"
    )
    print(
        "Dataset and Chroma "
        "were both updated."
    )


def update_component():
    records = load_records()

    print(
        "\nUPDATE COMPONENT\n"
    )

    component_id = input(
        "Component ID: "
    ).strip().upper()

    record = None

    for item in records:
        if item["id"] == component_id:
            record = item
            break

    if record is None:
        print(
            "Component not found."
        )
        return

    print()
    print(
        "Press Enter to keep "
        "the current value."
    )
    print()

    new_name = input(
        f"Name [{record['name']}]: "
    ).strip()

    if new_name:
        if name_exists(
            records,
            new_name,
            ignore_id=component_id,
        ):
            print(
                "\nDuplicate blocked."
            )
            print(
                "Another component already "
                "uses that name."
            )
            return

        record["name"] = new_name

    category = input(
        f"Category "
        f"[{record['category']}]: "
    ).strip()

    if category:
        record["category"] = (
            category.lower()
        )

    description = input(
        f"Description "
        f"[{record['description']}]: "
    ).strip()

    if description:
        record["description"] = (
            description
        )

    voltage_min = input(
        f"Minimum voltage "
        f"[{record['voltage_min_v']}]: "
    ).strip()

    if voltage_min:
        record[
            "voltage_min_v"
        ] = float(voltage_min)

    voltage_max = input(
        f"Maximum voltage "
        f"[{record['voltage_max_v']}]: "
    ).strip()

    if voltage_max:
        record[
            "voltage_max_v"
        ] = float(voltage_max)

    material = input(
        f"Material "
        f"[{record['material']}]: "
    ).strip()

    if material:
        record["material"] = (
            material
        )

    size = input(
        f"Size mm "
        f"[{record['size_mm']}]: "
    ).strip()

    if size:
        record[
            "size_mm"
        ] = float(size)

    cost = input(
        f"Cost USD "
        f"[{record['estimated_cost_usd']}]: "
    ).strip()

    if cost:
        record[
            "estimated_cost_usd"
        ] = float(cost)

    current_keywords = (
        ", ".join(
            record["keywords"]
        )
    )

    keywords = input(
        f"Keywords "
        f"[{current_keywords}]: "
    ).strip()

    if keywords:
        record["keywords"] = [
            keyword.strip()
            for keyword in keywords.split(",")
            if keyword.strip()
        ]

    source_reference = input(
        f"Source reference "
        f"[{record['source_reference']}]: "
    ).strip()

    if source_reference:
        record[
            "source_reference"
        ] = source_reference

    usage_permission = input(
        f"Usage permission "
        f"[{record['usage_permission']}]: "
    ).strip()

    if usage_permission:
        record[
            "usage_permission"
        ] = usage_permission

    save_records(records)

    update_vector_database(
        record
    )

    print()
    print(
        f"Updated {component_id}"
    )

    print(
        "Dataset and Chroma "
        "were both updated."
    )


def show_status():
    records = load_records()

    collection = get_collection()

    print(
        "\nDATABASE STATUS\n"
    )

    print(
        f"JSON records: "
        f"{len(records)}"
    )

    print(
        f"Chroma records: "
        f"{collection.count()}"
    )


def main():
    while True:
        print()
        print(
            "SMART COMPONENT MANAGER"
        )
        print(
            "1. Add component"
        )
        print(
            "2. Update component"
        )
        print(
            "3. Show database status"
        )
        print(
            "4. Exit"
        )

        choice = input(
            "\nChoose: "
        ).strip()

        if choice == "1":
            add_component()

        elif choice == "2":
            update_component()

        elif choice == "3":
            show_status()

        elif choice == "4":
            break

        else:
            print(
                "Invalid option."
            )


if __name__ == "__main__":
    main()