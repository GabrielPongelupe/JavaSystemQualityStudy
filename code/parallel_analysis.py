#!/usr/bin/env python3
"""
Análise paralela de repositórios Java com CK Metrics
"""
import os
import sys
import pandas as pd
import subprocess
import tempfile
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import argparse

def run_command(cmd, cwd=None):
    """Executa comando e retorna resultado"""
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Erro: {result.stderr}")
    return result.returncode == 0

def clone_repository(clone_url, dest_dir):
    """Clona repositório"""
    cmd = ["git", "clone", "--depth", "1", clone_url, dest_dir]
    return run_command(cmd)

def run_ck_analysis(ck_jar, project_dir, output_dir):
    """Executa análise CK"""
    os.makedirs(output_dir, exist_ok=True)
    
    cmd = ["java", "-jar", ck_jar, project_dir, "false", "0", "false", output_dir]
    success = run_command(cmd)
    
    if success:
        csv_files = []
        
        # Procurar CSVs na raiz do diretório atual
        for filename in ['class.csv', 'method.csv', 'field.csv', 'variable.csv', 
                        'ck_outputclass.csv', 'ck_outputmethod.csv', 'ck_outputfield.csv', 'ck_outputvariable.csv']:
            if os.path.exists(filename):
                csv_files.append(filename)
        
        # Se não encontrou na raiz, procurar no diretório de saída
        if not csv_files and os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                if filename.lower().endswith('.csv'):
                    csv_files.append(os.path.join(output_dir, filename))
        
        # Se ainda não encontrou, procurar em /tmp
        if not csv_files:
            for filename in ['/tmp/ck_outputclass.csv', '/tmp/ck_outputmethod.csv', 
                           '/tmp/ck_outputfield.csv', '/tmp/ck_outputvariable.csv']:
                if os.path.exists(filename):
                    csv_files.append(filename)
        
        return csv_files
    return []

def count_java_lines(project_dir):
    """Conta linhas de código Java"""
    import pathlib
    java_files = list(pathlib.Path(project_dir).rglob("*.java"))
    total_loc = 0
    total_comments = 0
    
    for java_file in java_files:
        try:
            with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            in_block_comment = False
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                    
                total_loc += 1
                
                # Detectar comentários
                if stripped.startswith('//'):
                    total_comments += 1
                elif stripped.startswith('/*'):
                    total_comments += 1
                    in_block_comment = True
                elif '*/' in stripped:
                    if in_block_comment:
                        total_comments += 1
                    in_block_comment = False
                elif in_block_comment:
                    total_comments += 1
                    
        except Exception as e:
            continue
    
    return total_loc, total_comments

def process_ck_data(csv_files, repo_name):
    """Processa dados do CK"""
    if not csv_files:
        return None
    
    # Usar class.csv se disponível
    class_csv = None
    for csv_file in csv_files:
        if 'class' in csv_file.lower():
            class_csv = csv_file
            break
    
    if not class_csv:
        class_csv = csv_files[0]
    
    try:
        df = pd.read_csv(class_csv)
        
        # Métricas obrigatórias
        metrics = ['cbo', 'dit', 'lcom', 'wmc', 'loc', 'rfc', 'noc']
        results = {}
        
        for metric in metrics:
            if metric in df.columns:
                values = pd.to_numeric(df[metric], errors='coerce').dropna()
                if len(values) > 0:
                    results[f'{metric}_mean'] = float(values.mean())
                    results[f'{metric}_median'] = float(values.median())
                    results[f'{metric}_std'] = float(values.std())
                    results[f'{metric}_min'] = float(values.min())
                    results[f'{metric}_max'] = float(values.max())
                    results[f'{metric}_count'] = len(values)
        
        return results
        
    except Exception as e:
        return None

def get_github_metrics(repo_name, token=None):
    """Coleta métricas do GitHub"""
    import requests
    headers = {'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = f'token {token}'

    try:
        # Dados do repositório
        repo_url = f"https://api.github.com/repos/{repo_name}"
        response = requests.get(repo_url, headers=headers)
        
        if response.status_code != 200:
            return None
            
        repo_data = response.json()
        
        # Calcular idade
        created_date = datetime.fromisoformat(repo_data['created_at'].replace('Z', '+00:00'))
        age_years = (datetime.now().replace(tzinfo=created_date.tzinfo) - created_date).days / 365.25
        
        # Buscar releases
        releases_url = f"https://api.github.com/repos/{repo_name}/releases"
        releases_response = requests.get(releases_url, headers=headers)
        releases_count = len(releases_response.json()) if releases_response.status_code == 200 else 0
        
        return {
            'repository': repo_name,
            'stars': repo_data['stargazers_count'],
            'forks': repo_data['forks_count'],
            'age_years': round(age_years, 2),
            'releases': releases_count,
            'size_kb': repo_data['size'],
            'open_issues': repo_data['open_issues_count'],
            'created_at': repo_data['created_at'],
            'updated_at': repo_data['updated_at']
        }
        
    except Exception as e:
        return None

def analyze_single_repo_parallel(repo_data, ck_jar, output_dir, token=None):
    """Analisa um único repositório (versão paralela)"""
    repo_name = repo_data['full_name']
    clone_url = repo_data['clone_url']
    
    print(f"[PARALELO] Analisando {repo_name}...")
    
    # Criar diretório temporário único
    temp_dir = tempfile.mkdtemp(prefix=f"repo_analysis_{repo_name.replace('/', '_')}_")
    project_dir = os.path.join(temp_dir, "repo")
    
    try:
        # 1. Clonar repositório
        if not clone_repository(clone_url, project_dir):
            print(f"❌ Falha ao clonar {repo_name}")
            return None
        
        # 2. Contar linhas de código
        loc, comments = count_java_lines(project_dir)
        
        # 3. Executar CK
        ck_output = os.path.join(temp_dir, "ck_output")
        csv_files = run_ck_analysis(ck_jar, project_dir, ck_output)
        
        if not csv_files:
            print(f"❌ CK não gerou CSVs para {repo_name}")
            return None
        
        # 4. Processar dados CK
        ck_results = process_ck_data(csv_files, repo_name)
        if not ck_results:
            print(f"❌ Falha ao processar dados CK para {repo_name}")
            return None
        
        # 5. Coletar métricas GitHub
        github_metrics = get_github_metrics(repo_name, token)
        
        # 6. Combinar resultados
        analysis_result = {
            'repository': repo_name,
            'analysis_date': datetime.now().isoformat(),
            'loc': loc,
            'comments': comments
        }
        
        if github_metrics:
            analysis_result.update(github_metrics)
        
        analysis_result.update(ck_results)
        
        # 7. Salvar resultados
        os.makedirs(output_dir, exist_ok=True)
        result_file = os.path.join(output_dir, f"analysis_{repo_name.replace('/', '_')}.csv")
        
        result_df = pd.DataFrame([analysis_result])
        result_df.to_csv(result_file, index=False)
        print(f"✅ {repo_name} concluído")
        
        return analysis_result
        
    except Exception as e:
        print(f"❌ Erro analisando {repo_name}: {e}")
        return None
        
    finally:
        # Limpeza
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Limpar CSVs da raiz
        for csv_file in ['class.csv', 'method.csv', 'field.csv', 'variable.csv']:
            if os.path.exists(csv_file):
                os.remove(csv_file)

def parallel_analyze_repos(repos_df, ck_jar, output_dir, max_workers=4, token=None):
    """Analisa repositórios em paralelo"""
    print(f"\n{'='*60}")
    print(f"ANÁLISE PARALELA - {max_workers} WORKERS")
    print(f"{'='*60}")
    
    results = []
    total_repos = len(repos_df)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submeter todas as tarefas
        future_to_repo = {
            executor.submit(analyze_single_repo_parallel, repo_data, ck_jar, output_dir, token): repo_data
            for _, repo_data in repos_df.iterrows()
        }
        
        # Processar resultados conforme completam
        completed = 0
        for future in as_completed(future_to_repo):
            repo_data = future_to_repo[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                completed += 1
                print(f"Progresso: {completed}/{total_repos} ({completed/total_repos*100:.1f}%)")
            except Exception as e:
                print(f"❌ Erro processando {repo_data['full_name']}: {e}")
                completed += 1
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Análise paralela de repositórios Java")
    parser.add_argument("--repos", required=True, help="Arquivo CSV com repositórios")
    parser.add_argument("--ck", required=True, help="Caminho para CK JAR")
    parser.add_argument("--output", default="results", help="Diretório de saída")
    parser.add_argument("--max-repos", type=int, help="Número máximo de repositórios")
    parser.add_argument("--workers", type=int, default=4, help="Número de workers paralelos")
    parser.add_argument("--token", help="GitHub token")
    
    args = parser.parse_args()
    
    # Carregar repositórios
    print(f"Carregando repositórios de {args.repos}...")
    repos_df = pd.read_csv(args.repos)
    
    if args.max_repos:
        repos_df = repos_df.head(args.max_repos)
    
    print(f"Analisando {len(repos_df)} repositórios com {args.workers} workers...")
    
    # Análise paralela
    start_time = time.time()
    results = parallel_analyze_repos(repos_df, args.ck, args.output, args.workers, args.token)
    end_time = time.time()
    
    # Salvar resultados consolidados
    if results:
        results_df = pd.DataFrame(results)
        consolidated_file = os.path.join(args.output, "complete_analysis.csv")
        results_df.to_csv(consolidated_file, index=False)
        print(f"\n✅ Análise concluída!")
        print(f"📊 {len(results)} repositórios analisados")
        print(f"⏱️  Tempo total: {end_time - start_time:.1f} segundos")
        print(f"📁 Resultados em: {consolidated_file}")
    else:
        print("❌ Nenhum resultado obtido")

if __name__ == "__main__":
    main()
