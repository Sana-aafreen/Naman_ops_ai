import re
from collections import Counter

import httpx

JS_URL = "https://namandarshan.com/assets/index-BR4n9Ath.js"

def main() -> None:
    js = httpx.get(JS_URL, timeout=25, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}).text

    # Find API-ish path fragments even if not in plain quoted strings
    api_paths = re.findall(r"/api/[a-zA-Z0-9_./-]{1,120}", js)
    api_hosts = re.findall(r"api\\.namandarshan\\.com", js)

    domain_paths = re.findall(
        r"/(?:temples|darshan|blogs|blog|puja|prasadam|chadhava|packages|package|gallery|referral)[a-zA-Z0-9_./-]{0,120}",
        js,
    )

    counts = Counter(api_paths)
    print("JS_URL:", JS_URL)
    print("api.namandarshan.com occurrences:", len(api_hosts))
    print("/api/* unique:", len(counts))
    for s, n in counts.most_common(120):
        print(f"{n:>3}  {s}")

    dcounts = Counter(domain_paths)
    print("\nother path fragments unique:", len(dcounts))
    for s, n in dcounts.most_common(80):
        print(f"{n:>3}  {s}")


if __name__ == "__main__":
    main()
