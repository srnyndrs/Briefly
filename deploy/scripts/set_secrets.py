import argparse
import base64
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

REQUIRED = (
    "POSTGRES_USER", "POSTGRES_PASSWORD", "RABBITMQ_USER", "RABBITMQ_PASSWORD",
    "JWT_SECRET", "INTERNAL_ADMIN_TOKEN",
)
SENTRY = {
    "CRAWLER": "crawler", "CONTENT": "content", "ACCOUNT": "account",
    "ENRICHMENT": "enrichment", "PUBLIC_API": "public-api",
}


def load_values(path: Path) -> dict[str, str]:
    allowed = set(REQUIRED) | {f"{name}_SENTRY_DSN" for name in SENTRY}
    values: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or key not in allowed or key in values:
            raise ValueError(f"Invalid, unknown or duplicate input at line {number}.")
        if re.search(r"[\x00-\x1f\x7f]", value) or re.fullmatch(r"<.*>", value):
            raise ValueError(f"Invalid value for {key}.")
        values[key] = value
    for key in REQUIRED:
        if not values.get(key, "").strip():
            raise ValueError(f"Missing required input: {key}.")
    if values["RABBITMQ_USER"].lower() == "guest":
        raise ValueError("Use a non-guest RabbitMQ username.")
    for key in ("RABBITMQ_USER", "RABBITMQ_PASSWORD"):
        if re.search(r"[^\x20-\x7e]", values[key]):
            raise ValueError(f"Use printable ASCII for {key}.")
    return values


def build_secrets(values: dict[str, str]) -> dict[str, object]:
    db_user, db_password, broker_user, broker_password = (
        quote(values[key], safe="") for key in REQUIRED[:4]
    )
    entries = {
        "briefly-postgres": {
            "username": values["POSTGRES_USER"], "password": values["POSTGRES_PASSWORD"],
        },
        "briefly-rabbitmq": {
            "username": values["RABBITMQ_USER"], "password": values["RABBITMQ_PASSWORD"],
        },
        "briefly-backend": {
            "DATABASE_URL": f"postgresql+psycopg2://{db_user}:{db_password}@postgres:5432/briefly",
            "RABBITMQ_URL": f"amqp://{broker_user}:{broker_password}@rabbitmq:5672/%2F",
            "INTERNAL_ADMIN_TOKEN": values["INTERNAL_ADMIN_TOKEN"],
        },
        "briefly-jwt": {"JWT_SECRET": values["JWT_SECRET"]},
    }
    entries.update({
        f"{service}-sentry": {"SENTRY_DSN": values.get(f"{name}_SENTRY_DSN", "")}
        for name, service in SENTRY.items()
    })
    return {
        "apiVersion": "v1", "kind": "List",
        "items": [
            {
                "apiVersion": "v1", "kind": "Secret", "type": "Opaque",
                "metadata": {"name": name, "namespace": "briefly"},
                "data": {
                    key: base64.b64encode(value.encode()).decode()
                    for key, value in data.items()
                },
            }
            for name, data in entries.items()
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--env-file", type=Path, default=Path(__file__).resolve().parents[1] / ".env")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        if not args.context.strip() or args.context.startswith("<"):
            raise ValueError("Provide the verified Kubernetes context explicitly.")
        secrets = build_secrets(load_values(args.env_file))
        if args.validate_only:
            print("Input valid: 9 Secrets for namespace briefly. No cluster access performed.")
            return
        command = ["kubectl", "--context", args.context, "--namespace", "briefly"]
        result = subprocess.run(
            command + ["--request-timeout=15s", "get", "namespace", "briefly", "-o", "name"],
            capture_output=True,
        )
        if result.returncode:
            raise ValueError("Could not verify namespace briefly in the explicit context.")
        result = subprocess.run(
            command + ["--request-timeout=30s", "apply", "--server-side",
                       "--field-manager=briefly-local-secrets", "-f", "-"],
            input=json.dumps(secrets).encode(), capture_output=True,
        )
        if result.returncode:
            raise ValueError("Secret apply failed; some items may already be applied. Check cluster access and rerun.")
        print(f"Applied 9 Secrets to namespace briefly in context '{args.context}'.")
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
