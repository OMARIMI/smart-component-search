import json
from pathlib import Path


OUTPUT_PATH = Path("data/components.json")


COMPONENT_TYPES = [
    {
        "category": "resistor",
        "names": ["Carbon Film Resistor", "Metal Film Resistor"],
        "materials": ["carbon film", "metal film"],
        "voltage": (0, 250),
        "sizes": [3, 5, 6],
        "costs": [0.05, 0.08, 0.12],
        "keywords": ["resistor", "current limiting", "voltage divider", "passive"]
    },
    {
        "category": "capacitor",
        "names": ["Ceramic Capacitor", "Electrolytic Capacitor"],
        "materials": ["ceramic", "aluminum"],
        "voltage": (5, 50),
        "sizes": [3, 5, 8],
        "costs": [0.08, 0.15, 0.25],
        "keywords": ["capacitor", "filtering", "energy storage", "passive"]
    },
    {
        "category": "led",
        "names": ["Red LED", "Green LED", "Blue LED", "White LED"],
        "materials": ["semiconductor"],
        "voltage": (1.8, 3.4),
        "sizes": [3, 5],
        "costs": [0.05, 0.10, 0.15],
        "keywords": ["led", "light", "indicator", "diode"]
    },
    {
        "category": "sensor",
        "names": [
            "Temperature Sensor",
            "Humidity Sensor",
            "Light Sensor",
            "Distance Sensor",
            "Motion Sensor"
        ],
        "materials": ["semiconductor", "plastic"],
        "voltage": (3.3, 5),
        "sizes": [10, 15, 20, 25],
        "costs": [1.50, 2.50, 4.00, 6.00],
        "keywords": ["sensor", "measurement", "input", "electronics"]
    },
    {
        "category": "microcontroller",
        "names": [
            "8-bit Microcontroller",
            "32-bit Microcontroller",
            "Wi-Fi Microcontroller",
            "Low-Power Microcontroller"
        ],
        "materials": ["silicon"],
        "voltage": (1.8, 5),
        "sizes": [7, 10, 15],
        "costs": [2.00, 4.50, 7.00],
        "keywords": ["microcontroller", "processor", "embedded", "programmable"]
    },
    {
        "category": "transistor",
        "names": [
            "NPN Transistor",
            "PNP Transistor",
            "N-Channel MOSFET",
            "P-Channel MOSFET"
        ],
        "materials": ["silicon"],
        "voltage": (0, 60),
        "sizes": [4, 6, 10],
        "costs": [0.10, 0.25, 0.60],
        "keywords": ["transistor", "switching", "amplifier", "semiconductor"]
    },
    {
        "category": "relay",
        "names": [
            "5V Relay",
            "12V Relay",
            "Solid State Relay"
        ],
        "materials": ["copper", "plastic"],
        "voltage": (5, 24),
        "sizes": [15, 20, 30],
        "costs": [1.50, 3.00, 5.00],
        "keywords": ["relay", "switch", "control", "load"]
    },
    {
        "category": "motor",
        "names": [
            "DC Motor",
            "Gear Motor",
            "Stepper Motor",
            "Servo Motor"
        ],
        "materials": ["steel", "copper", "plastic"],
        "voltage": (3, 24),
        "sizes": [20, 30, 40, 50],
        "costs": [3.00, 6.00, 12.00],
        "keywords": ["motor", "motion", "actuator", "rotation"]
    },
    {
        "category": "switch",
        "names": [
            "Push Button Switch",
            "Toggle Switch",
            "Slide Switch",
            "Limit Switch"
        ],
        "materials": ["plastic", "metal"],
        "voltage": (0, 24),
        "sizes": [5, 10, 15],
        "costs": [0.20, 0.50, 1.00],
        "keywords": ["switch", "input", "control", "mechanical"]
    },
    {
        "category": "connector",
        "names": [
            "Pin Header",
            "Screw Terminal",
            "JST Connector",
            "USB Connector"
        ],
        "materials": ["copper", "plastic"],
        "voltage": (0, 30),
        "sizes": [5, 10, 15],
        "costs": [0.10, 0.40, 1.00],
        "keywords": ["connector", "wiring", "electrical", "connection"]
    },
]


def create_dataset():
    records = []
    component_number = 1

    for group_index, group in enumerate(COMPONENT_TYPES):
        for variation in range(12):
            name = group["names"][variation % len(group["names"])]
            material = group["materials"][variation % len(group["materials"])]
            size = group["sizes"][variation % len(group["sizes"])]
            cost = group["costs"][variation % len(group["costs"])]

            voltage_min, voltage_max = group["voltage"]

            record = {
                "id": f"COMP-{component_number:04d}",
                "name": f"{name} Model {variation + 1}",
                "category": group["category"],
                "description": (
                    f"{name} designed for general electronics and "
                    f"engineering projects. Suitable for applications "
                    f"related to {', '.join(group['keywords'][:3])}."
                ),
                "voltage_min_v": voltage_min,
                "voltage_max_v": voltage_max,
                "material": material,
                "size_mm": size,
                "estimated_cost_usd": cost,
                "keywords": group["keywords"],
                "source_type": "synthetic",
                "source_reference": (
                    f"synthetic://smart-component-search/"
                    f"COMP-{component_number:04d}"
                ),
                "usage_permission": (
                    "Synthetic educational dataset generated for this project."
                )
            }

            records.append(record)
            component_number += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_PATH.write_text(
        json.dumps(records, indent=2),
        encoding="utf-8"
    )

    print(f"Created {len(records)} component records.")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    create_dataset()