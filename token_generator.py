#!/usr/bin/env python3
import argparse
import secrets
import string


def generate_api_key(prefix: str = "sk", length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits
    token = "".join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}_{token}"


def main():
    parser = argparse.ArgumentParser(description="Generate secure API keys.")
    parser.add_argument("-c", "--count", type=int, default=1, help="Number of keys to generate")
    parser.add_argument(
        "-l", "--length", type=int, default=32, help="Token length (excluding prefix)"
    )
    parser.add_argument("-p", "--prefix", default="sk", help="Key prefix (default: sk)")
    parser.add_argument("-o", "--output", help="Optional output file (one key per line)")
    args = parser.parse_args()

    keys = [generate_api_key(args.prefix, args.length) for _ in range(args.count)]

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(keys) + "\n")
        print(f"Wrote {len(keys)} keys to {args.output}")
    else:
        print("\n".join(keys))


if __name__ == "__main__":
    main()
