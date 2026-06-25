import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path


RANDOM_SEED = 4747
OUT_DIR = Path(__file__).resolve().parent

TRAIN_ROWS = 2000
TEST_ROWS = 500

FIELDS = [
    "event_id",
    "timestamp",
    "user_role",
    "department",
    "device_type",
    "operating_system",
    "protocol",
    "action",
    "login_attempts",
    "failed_logins",
    "session_duration_sec",
    "bytes_received",
    "bytes_sent",
    "files_accessed",
    "sensitive_files_accessed",
    "unique_ports_contacted",
    "geo_distance_km",
    "ip_reputation_score",
    "off_hours_activity",
    "privilege_escalation",
]

CATEGORICAL = {
    "user_role": ["employee", "manager", "contractor", "admin", "service_account", "guest"],
    "department": ["IT", "Finance", "HR", "Sales", "Research", "Operations", "Legal", "Support"],
    "device_type": ["laptop", "desktop", "mobile", "server", "tablet", "unknown"],
    "operating_system": ["Windows", "Linux", "macOS", "Android", "iOS", "Other"],
    "protocol": ["HTTPS", "SSH", "RDP", "FTP", "SMTP", "DNS", "SMB", "VPN"],
    "action": ["login", "file_access", "download", "upload", "config_change", "privilege_request", "api_call"],
}


def weighted_choice(options):
    values, weights = zip(*options)
    return random.choices(values, weights=weights, k=1)[0]


def sigmoid(value):
    return 1 / (1 + math.exp(-value))


def random_timestamp():
    start = datetime(2026, 2, 1)
    day_offset = random.randint(0, 59)
    # Normal office traffic dominates, but suspicious activity is not limited to night.
    if random.random() < 0.72:
        hour = min(23, max(0, int(random.gauss(13, 4))))
    else:
        hour = random.choice(list(range(0, 7)) + list(range(19, 24)))
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return start + timedelta(days=day_offset, hours=hour, minutes=minute, seconds=second)


def base_event(event_id):
    timestamp = random_timestamp()
    department = weighted_choice(
        [
            ("IT", 17),
            ("Finance", 12),
            ("HR", 8),
            ("Sales", 15),
            ("Research", 14),
            ("Operations", 18),
            ("Legal", 6),
            ("Support", 10),
        ]
    )
    role = weighted_choice(
        [
            ("employee", 48),
            ("manager", 13),
            ("contractor", 13),
            ("admin", 8),
            ("service_account", 10),
            ("guest", 8),
        ]
    )
    device = weighted_choice(
        [
            ("laptop", 42),
            ("desktop", 24),
            ("mobile", 14),
            ("server", 8),
            ("tablet", 7),
            ("unknown", 5),
        ]
    )
    os_name = weighted_choice(
        [
            ("Windows", 44),
            ("Linux", 20),
            ("macOS", 15),
            ("Android", 8),
            ("iOS", 7),
            ("Other", 6),
        ]
    )
    protocol = weighted_choice(
        [
            ("HTTPS", 38),
            ("SSH", 12),
            ("RDP", 8),
            ("FTP", 6),
            ("SMTP", 8),
            ("DNS", 10),
            ("SMB", 9),
            ("VPN", 9),
        ]
    )
    action = weighted_choice(
        [
            ("login", 25),
            ("file_access", 24),
            ("download", 16),
            ("upload", 9),
            ("config_change", 6),
            ("privilege_request", 5),
            ("api_call", 15),
        ]
    )

    off_hours = int(timestamp.hour < 7 or timestamp.hour >= 19 or timestamp.weekday() >= 5)
    login_attempts = max(1, int(random.expovariate(0.75)) + 1)
    failed_logins = min(login_attempts, max(0, int(random.expovariate(1.2)) - 1))
    if random.random() < 0.08:
        failed_logins = min(login_attempts + random.randint(1, 4), failed_logins + random.randint(2, 5))
        login_attempts = max(login_attempts, failed_logins + random.randint(0, 2))

    session_duration = int(max(30, random.lognormvariate(6.8, 0.85)))
    bytes_received = int(max(200, random.lognormvariate(9.3, 1.0)))
    bytes_sent = int(max(100, random.lognormvariate(8.8, 1.15)))
    files_accessed = max(0, int(random.expovariate(0.18)))
    sensitive_files = min(files_accessed, max(0, int(random.expovariate(0.7)) - 1))
    ports = max(1, int(random.expovariate(0.35)) + 1)
    geo_distance = round(max(0, random.lognormvariate(3.0, 1.15) - 12), 2)
    ip_reputation = round(min(100, max(0, random.gauss(28, 18))), 2)
    privilege_escalation = int(action == "privilege_request" and random.random() < 0.22)

    # Correlated but imperfect suspicious behaviors.
    if random.random() < 0.12:
        bytes_sent = int(bytes_sent * random.uniform(4, 15))
    if random.random() < 0.10:
        sensitive_files = min(files_accessed + random.randint(1, 6), sensitive_files + random.randint(1, 4))
        files_accessed = max(files_accessed, sensitive_files + random.randint(0, 8))
    if random.random() < 0.09:
        ports += random.randint(8, 30)
    if random.random() < 0.07:
        geo_distance += round(random.uniform(150, 3000), 2)
    if random.random() < 0.06:
        ip_reputation = round(min(100, ip_reputation + random.uniform(35, 70)), 2)

    row = {
        "event_id": event_id,
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "user_role": role,
        "department": department,
        "device_type": device,
        "operating_system": os_name,
        "protocol": protocol,
        "action": action,
        "login_attempts": login_attempts,
        "failed_logins": failed_logins,
        "session_duration_sec": session_duration,
        "bytes_received": bytes_received,
        "bytes_sent": bytes_sent,
        "files_accessed": files_accessed,
        "sensitive_files_accessed": sensitive_files,
        "unique_ports_contacted": ports,
        "geo_distance_km": geo_distance,
        "ip_reputation_score": ip_reputation,
        "off_hours_activity": off_hours,
        "privilege_escalation": privilege_escalation,
    }
    return row


def malicious_probability(row):
    failed_ratio = row["failed_logins"] / max(1, row["login_attempts"])
    sensitive_ratio = row["sensitive_files_accessed"] / max(1, row["files_accessed"])
    data_total = row["bytes_sent"] + row["bytes_received"]

    score = -2.55
    score += 0.55 * row["off_hours_activity"]
    score += 0.95 * failed_ratio
    score += 0.65 if row["failed_logins"] >= 3 else 0
    score += 0.75 if row["sensitive_files_accessed"] >= 3 else 0
    score += 0.55 * sensitive_ratio
    score += 0.65 if row["bytes_sent"] > 90000 else 0
    score += 0.50 if data_total > 160000 else 0
    score += 0.75 if row["unique_ports_contacted"] >= 12 else 0
    score += 0.85 if row["geo_distance_km"] > 600 else 0
    score += 0.95 if row["ip_reputation_score"] > 65 else 0
    score += 0.80 * row["privilege_escalation"]
    score += 0.45 if row["protocol"] in {"SSH", "RDP", "FTP", "SMB"} else 0
    score += 0.45 if row["user_role"] in {"admin", "service_account", "contractor"} else 0
    score += 0.35 if row["device_type"] == "unknown" else 0
    score += 0.35 if row["action"] in {"download", "upload", "config_change", "privilege_request"} else 0
    score += random.gauss(0, 0.72)
    return sigmoid(score)


def add_missing_values(rows, include_target=False):
    nullable = [
        "user_role",
        "department",
        "device_type",
        "operating_system",
        "protocol",
        "login_attempts",
        "failed_logins",
        "session_duration_sec",
        "bytes_received",
        "bytes_sent",
        "files_accessed",
        "sensitive_files_accessed",
        "unique_ports_contacted",
        "geo_distance_km",
        "ip_reputation_score",
    ]
    for row in rows:
        for field in nullable:
            if random.random() < 0.018:
                row[field] = ""
        if include_target and random.random() < 0.0:
            row["is_malicious"] = ""


def generate_rows(start_index, count, with_target):
    rows = []
    for index in range(start_index, start_index + count):
        row = base_event(f"EVT-{index:04d}")
        if with_target:
            row["is_malicious"] = int(random.random() < malicious_probability(row))
        rows.append(row)
    return rows


def inject_duplicates(rows, duplicate_count):
    positions = random.sample(range(len(rows)), duplicate_count)
    sources = random.sample(range(len(rows)), duplicate_count)
    for position, source in zip(positions, sources):
        rows[position] = dict(rows[source])


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    random.seed(RANDOM_SEED)
    train = generate_rows(1, TRAIN_ROWS, with_target=True)
    test = generate_rows(2001, TEST_ROWS, with_target=False)

    inject_duplicates(train, duplicate_count=28)
    add_missing_values(train)
    add_missing_values(test)

    write_csv(OUT_DIR / "nova_security_train.csv", train, FIELDS + ["is_malicious"])
    write_csv(OUT_DIR / "nova_security_test.csv", test, FIELDS)
    write_csv(
        OUT_DIR / "sample_submission.csv",
        [{"event_id": row["event_id"], "is_malicious": 0} for row in test],
        ["event_id", "is_malicious"],
    )


if __name__ == "__main__":
    main()
