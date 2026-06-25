import csv
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent

TRAIN_ROWS = [
    {"sample_id": "NSE-001", "suspicious_activities": 18, "confirmed_incidents": 3},
    {"sample_id": "NSE-002", "suspicious_activities": 22, "confirmed_incidents": 4},
    {"sample_id": "NSE-003", "suspicious_activities": 27, "confirmed_incidents": 5},
    {"sample_id": "NSE-004", "suspicious_activities": 31, "confirmed_incidents": 6},
    {"sample_id": "NSE-005", "suspicious_activities": 36, "confirmed_incidents": 7},
    {"sample_id": "NSE-006", "suspicious_activities": 42, "confirmed_incidents": 8},
    {"sample_id": "NSE-007", "suspicious_activities": 48, "confirmed_incidents": 10},
    {"sample_id": "NSE-008", "suspicious_activities": 53, "confirmed_incidents": 11},
    {"sample_id": "NSE-009", "suspicious_activities": 59, "confirmed_incidents": 12},
    {"sample_id": "NSE-010", "suspicious_activities": 64, "confirmed_incidents": 13},
    {"sample_id": "NSE-011", "suspicious_activities": 71, "confirmed_incidents": 15},
    {"sample_id": "NSE-012", "suspicious_activities": 78, "confirmed_incidents": 16},
    {"sample_id": "NSE-013", "suspicious_activities": 84, "confirmed_incidents": 18},
    {"sample_id": "NSE-014", "suspicious_activities": 91, "confirmed_incidents": 19},
    {"sample_id": "NSE-015", "suspicious_activities": 98, "confirmed_incidents": 21},
]

def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    write_csv(
        OUT_DIR / "smart_incident_train.csv",
        TRAIN_ROWS,
        ["sample_id", "suspicious_activities", "confirmed_incidents"],
    )


if __name__ == "__main__":
    main()
