#!/usr/bin/env python3
import argparse, os, subprocess, tempfile, shutil, sys, pandas as pd, csv, pathlib
import requests, time
from datetime import datetime


def run_cmd(cmd, cwd=None):
    print("CMD:", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=cwd)


def clone_repo(clone_url, dest_dir):
    # For Windows, enable long path support and set core.longpaths
    try:
        # First try with longpaths support
        cmd = ["git", "clone", "--depth", "1", "--config", "core.longpaths=true", clone_url, dest_dir]
        run_cmd(cmd)
    except subprocess.CalledProcessError:
        print("Failed with longpaths, trying sparse checkout...")
        # Alternative: use sparse checkout to avoid problematic files
        try:
            os.makedirs(dest_dir, exist_ok=True)
            run_cmd(["git", "init"], cwd=dest_dir)
            run_cmd(["git", "remote", "add", "origin", clone_url], cwd=dest_dir)
            run_cmd(["git", "config", "core.sparseCheckout", "true"], cwd=dest_dir)

            # Create sparse-checkout file to exclude test directories with long names
            sparse_checkout_file = os.path.join(dest_dir, ".git", "info", "sparse-checkout")
            os.makedirs(os.path.dirname(sparse_checkout_file), exist_ok=True)
            with open(sparse_checkout_file, "w") as f:
                f.write("/*\n")
                f.write(
                    "!spring-test/src/test/java/org/springframework/test/context/bean/override/mockito/integration/MockitoBeanWithMultipleExistingBeansAndOnePrimaryAndOneConflictingQualifierIntegrationTests.java\n")
                f.write(
                    "!spring-test/src/test/java/org/springframework/test/context/bean/override/mockito/integration/MockitoSpyBeanWithGenericsOnTestFieldForExistingGenericBeanProducedByFactoryBeanIntegrationTests.java\n")

            run_cmd(["git", "pull", "origin", "main", "--depth", "1"], cwd=dest_dir)
        except subprocess.CalledProcessError:
            # Final fallback: clone without depth limit
            run_cmd(["git", "clone", "--config", "core.longpaths=true", clone_url, dest_dir])


def run_ck(ck_jar_path, project_dir, output_dir, use_jars="false", max_files="0", variables_and_fields="false"):
    os.makedirs(output_dir, exist_ok=True)
    cmd = ["java", "-jar", ck_jar_path, project_dir, use_jars, max_files, variables_and_fields, output_dir]
    run_cmd(cmd)


def find_csv(output_dir):
    # CK normalmente gera class.csv, method.csv, variable.csv inside output_dir
    candidates = []
    for name in os.listdir(output_dir):
        if name.lower().startswith("class") and name.lower().endswith(".csv"):
            return os.path.join(output_dir, name)
    # fallback
    for name in os.listdir(output_dir):
        if name.endswith(".csv"):
            candidates.append(os.path.join(output_dir, name))
    return candidates[0] if candidates else None


def summarize_class_csv(class_csv_path, out_summary_csv):
    df = pd.read_csv(class_csv_path)
    # metrics we care about (some may be missing; handle gracefully)
    metrics = ['cbo', 'dit', 'lcom', 'lcom*', 'wmc', 'loc']
    rows = []

    for m in metrics:
        if m in df.columns:
            col = pd.to_numeric(df[m], errors='coerce').dropna()
            if len(col) == 0:
                continue
            rows.append({
                'metric': m,
                'count': len(col),
                'mean': float(col.mean()),
                'median': float(col.median()),
                'std': float(col.std()),
                'min': float(col.min()),
                'max': float(col.max())
            })

    if rows:
        pd.DataFrame(rows).to_csv(out_summary_csv, index=False)
        print("Summary written to", out_summary_csv)
        return rows
    else:
        print("No matching metric columns found in", class_csv_path)
        return []


def get_github_metrics(repo_name, token=None):
    """Coleta métricas do repositório via GitHub API"""
    headers = {'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = f'token {token}'
        print(f"Using GitHub token: {token[:8]}...")  # Show first 8 chars for debugging

    try:
        # Dados básicos do repositório
        repo_url = f"https://api.github.com/repos/{repo_name}"
        repo_response = requests.get(repo_url, headers=headers)

        if repo_response.status_code != 200:
            print(f"Erro buscando dados do repo {repo_name}: {repo_response.status_code}")
            if repo_response.status_code == 401:
                print("Token inválido ou sem permissões. Verifique se o GITHUB_TOKEN está correto.")
                print("O token precisa ter pelo menos permissões de 'repo' ou 'public_repo'.")
            print(f"Response: {repo_response.text}")
            return None

        repo_data = repo_response.json()

        # Calcular idade do repositório
        created_date = datetime.fromisoformat(repo_data['created_at'].replace('Z', '+00:00'))
        age_years = (datetime.now().replace(tzinfo=created_date.tzinfo) - created_date).days / 365.25

        # Buscar releases
        releases_url = f"https://api.github.com/repos/{repo_name}/releases"
        releases_response = requests.get(releases_url, headers=headers)
        releases_count = 0
        if releases_response.status_code == 200:
            releases_count = len(releases_response.json())

        return {
            'stars': repo_data['stargazers_count'],
            'forks': repo_data['forks_count'],
            'size_kb': repo_data['size'],
            'age_years': round(age_years, 2),
            'releases': releases_count,
            'open_issues': repo_data['open_issues_count'],
            'created_at': repo_data['created_at'],
            'updated_at': repo_data['updated_at']
        }

    except Exception as e:
        print(f"Erro coletando métricas do GitHub para {repo_name}: {e}")
        return None


def count_lines_of_code(project_dir):
    """Conta linhas de código e comentários em arquivos Java"""
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
            print(f"Erro lendo {java_file}: {e}")
            continue

    return total_loc, total_comments


def save_complete_analysis(repo_name, github_metrics, loc, comments, ck_summary, output_file):
    """Salva análise completa em CSV"""
    # Preparar dados para CSV
    analysis_data = {
        'repository': repo_name,
        'analysis_date': datetime.now().isoformat(),
        'loc': loc,
        'comments': comments
    }

    # Adicionar métricas do GitHub
    if github_metrics:
        analysis_data.update(github_metrics)

    # Adicionar métricas CK sumarizadas
    for metric_data in ck_summary:
        metric = metric_data['metric']
        analysis_data[f'{metric}_mean'] = metric_data['mean']
        analysis_data[f'{metric}_median'] = metric_data['median']
        analysis_data[f'{metric}_std'] = metric_data['std']
        analysis_data[f'{metric}_count'] = metric_data['count']

    # Salvar em CSV
    fieldnames = sorted(analysis_data.keys())

    # Verificar se arquivo já existe para decidir se escreve header
    file_exists = os.path.exists(output_file)

    with open(output_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(analysis_data)

    print(f"Análise completa salva em: {output_file}")


def process_repos_from_csv(csv_file, ck_jar, outdir, token=None, max_repos=None):
    """Processa repositórios de um arquivo CSV"""
    print(f"Processando repositórios de {csv_file}")

    try:
        df = pd.read_csv(csv_file)
        repos_to_process = df.head(max_repos) if max_repos else df

        complete_analysis_file = os.path.join(outdir, "complete_analysis.csv")

        for idx, row in repos_to_process.iterrows():
            repo_name = row['full_name']
            clone_url = row['clone_url']

            print(f"\n=== Processando {idx + 1}/{len(repos_to_process)}: {repo_name} ===")

            # Usar o processo de análise individual
            analyze_single_repo_complete(repo_name, clone_url, ck_jar, outdir, token, complete_analysis_file)

            # Pequena pausa entre repositórios
            time.sleep(2)

    except Exception as e:
        print(f"Erro processando CSV: {e}")


def analyze_single_repo_complete(repo_name, clone_url, ck_jar, outdir, token=None, complete_analysis_file=None):
    """Análise completa de um único repositório"""
    shortname = repo_name.replace("/", "_")

    # 1. Coletar métricas do GitHub
    print("Coletando métricas do GitHub...")
    github_metrics = get_github_metrics(repo_name, token)

    tmpdir = tempfile.mkdtemp(prefix="lab02_")
    proj_dir = os.path.join(tmpdir, shortname)

    try:
        print("Cloning", clone_url, "->", proj_dir)
        clone_repo(clone_url, proj_dir)

        # 2. Contar linhas de código
        print("Contando linhas de código...")
        loc, comments = count_lines_of_code(proj_dir)

        # 3. Executar análise CK
        ck_out = os.path.join(tmpdir, "ck_out")
        print("Running CK ...")
        run_ck(ck_jar, proj_dir, ck_out)

        class_csv = find_csv(ck_out)
        if not class_csv:
            print("ERROR: class csv not found in", ck_out)
            return False

        # Salvar arquivos individuais
        os.makedirs(outdir, exist_ok=True)
        raw_dest = os.path.join(outdir, f"metricas_raw_{shortname}.csv")
        shutil.copy(class_csv, raw_dest)
        print("Raw class CSV copied to", raw_dest)

        summary_dest = os.path.join(outdir, f"metricas_summary_{shortname}.csv")
        ck_summary = summarize_class_csv(raw_dest, summary_dest)

        # 4. Salvar análise completa
        if complete_analysis_file:
            save_complete_analysis(repo_name, github_metrics, loc, comments, ck_summary, complete_analysis_file)

        return True

    except Exception as e:
        print(f"Erro analisando {repo_name}: {e}")
        return False

    finally:
        # Limpeza
        print("Cleaning up temporary clone:", tmpdir)
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(description="Análise completa de repositórios Java - Lab02")
    p.add_argument("--repo", help="owner/repo or full https git url (para repositório individual)")
    p.add_argument("--csv", help="arquivo CSV com lista de repositórios (gerado pelo script de fetch)")
    p.add_argument("--ck", required=True, help="path to ck-...jar")
    p.add_argument("--outdir", default="docs/results", help="where to save outputs")
    p.add_argument("--token", help="GitHub token para evitar rate limits")
    p.add_argument("--max-repos", type=int, help="máximo de repos para processar do CSV")
    args = p.parse_args()

    ck_jar = args.ck
    outdir = args.outdir

    if args.repo:
        # Análise de repositório individual (modo original)
        repo = args.repo.strip()

        # normalize clone URL
        if repo.startswith("http://") or repo.startswith("https://") or repo.endswith(".git"):
            clone_url = repo
            shortname = os.path.splitext(os.path.basename(clone_url))[0]
            repo_name = shortname  # Melhor seria extrair do URL
        else:
            clone_url = f"https://github.com/{repo}.git"
            shortname = repo.replace("/", "_")
            repo_name = repo

        complete_analysis_file = os.path.join(outdir, f"analysis_{shortname}.csv")
        analyze_single_repo_complete(repo_name, clone_url, ck_jar, outdir, args.token, complete_analysis_file)

    elif args.csv:
        # Processar múltiplos repositórios do CSV
        process_repos_from_csv(args.csv, ck_jar, outdir, args.token, args.max_repos)

    else:
        print("Use --repo para analisar um repositório ou --csv para processar lista de repositórios")
        print("Exemplos:")
        print(f"  python {sys.argv[0]} --ck tools/ck.jar --repo spring-projects/spring-framework --token TOKEN")
        print(f"  python {sys.argv[0]} --ck tools/ck.jar --csv repositorios_java.csv --max-repos 10 --token TOKEN")


if __name__ == "__main__":
    main()
