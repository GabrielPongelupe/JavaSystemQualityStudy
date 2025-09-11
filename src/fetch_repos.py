#!/usr/bin/env python3
import requests, csv, os, time, argparse

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

def fetch_top_java(token=None, per_page=100, pages=10, out_csv="repositorios_java.csv"):
    headers = {'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = f'token {token}'

    fieldnames = ["full_name","html_url","clone_url","stargazers_count","forks_count","created_at","updated_at","size","language","open_issues_count","default_branch"]
    rows = []

    for page in range(1, pages+1):
        params = {
            'q': 'language:Java',
            'sort': 'stars',
            'order': 'desc',
            'per_page': per_page,
            'page': page
        }
        print(f"[fetch] page {page} ...")
        r = requests.get(GITHUB_SEARCH_URL, headers=headers, params=params)
        if r.status_code != 200:
            print("ERROR", r.status_code, r.text)
            break
        data = r.json()
        items = data.get('items', [])
        for it in items:
            rows.append({k: it.get(k,"") for k in fieldnames})
        # be polite with rate-limits
        time.sleep(2)

    # write csv
    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} repos to {out_csv}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="GitHub token (or env GITHUB_TOKEN)")
    p.add_argument("--out", default="repositorios_java.csv")
    p.add_argument("--pages", type=int, default=10)
    args = p.parse_args()
    fetch_top_java(token=args.token, pages=args.pages, out_csv=args.out)
