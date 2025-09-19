#!/usr/bin/env python3
"""
Busca os top 1000 repositórios Java do GitHub
"""
import requests
import csv
import os
import time
import argparse

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

def fetch_top_java_repos(token=None, per_page=100, pages=10, output_file="repositorios_java.csv"):
    """Busca os top repositórios Java do GitHub"""
    headers = {'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = f'token {token}'

    fieldnames = [
        "full_name", "html_url", "clone_url", "stargazers_count", "forks_count", 
        "created_at", "updated_at", "size", "language", "open_issues_count", "default_branch"
    ]
    rows = []

    print(f"Buscando {pages * per_page} repositórios Java...")
    
    for page in range(1, pages + 1):
        params = {
            'q': 'language:Java',
            'sort': 'stars',
            'order': 'desc',
            'per_page': per_page,
            'page': page
        }
        
        print(f"Página {page}/{pages}...")
        response = requests.get(GITHUB_SEARCH_URL, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Erro {response.status_code}: {response.text}")
            break
            
        data = response.json()
        items = data.get('items', [])
        
        for item in items:
            rows.append({k: item.get(k, "") for k in fieldnames})
        
        # Respeitar rate limits
        time.sleep(1)

    # Salvar CSV
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ {len(rows)} repositórios salvos em {output_file}")
    return len(rows)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Busca repositórios Java do GitHub")
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="GitHub token")
    parser.add_argument("--output", default="repositorios_java.csv", help="Arquivo de saída")
    parser.add_argument("--pages", type=int, default=10, help="Número de páginas (100 repos por página)")
    
    args = parser.parse_args()
    
    if not args.token:
        print("⚠️  Sem token GitHub - pode atingir limite de rate")
        print("Configure: export GITHUB_TOKEN=seu_token")
    
    fetch_top_java_repos(args.token, pages=args.pages, output_file=args.output)
