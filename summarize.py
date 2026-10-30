
import json

with open("runs/baseline-candidate.json") as f:
    r = json.load(f)

ok = sum(x["correct"] for x in r["results"])
original = sum(x["api_measurement"]["usage"]["total_tokens"] for x in r["results"])
current = sum(x["run_api_usage"]["total_tokens"] for x in r["results"])

print(f"accuracy={ok/len(r['results']):.1%} correct={ok}/18 original_api_tokens={original} current_run_api_tokens={current}")
