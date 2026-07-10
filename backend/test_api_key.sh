#!/usr/bin/env bash
# Quick check that the API key gate actually works.
# Usage: ./test_api_key.sh [base_url]
#   ./test_api_key.sh                          # defaults to https://matchcalender.com
#   ./test_api_key.sh http://localhost:8000

set -euo pipefail

BASE_URL="${1:-https://matchcalender.com}"

# Reads API_KEY from ../.env relative to this script — doesn't hardcode the secret.
ENV_FILE="$(dirname "$0")/../.env"
API_KEY=$(grep -m1 '^API_KEY=' "$ENV_FILE" | cut -d= -f2-)

echo "Testing against: $BASE_URL"
echo

echo "1) No key at all (expect 401):"
curl -s -o /dev/null -w "   -> %{http_code}\n" "$BASE_URL/api/sports"

echo "2) Correct key (expect 200):"
curl -s -o /dev/null -w "   -> %{http_code}\n" \
    -H "X-API-Key: $API_KEY" \
    "$BASE_URL/api/sports"
