#!/usr/bin/env python3
import argparse, os, subprocess, tempfile, shutil, sys, pandas as pd
import time

def run_cmd(cmd, cwd=None, capture_output=True):
    print("CMD:", " ".join(cmd))
    try:
        result = subprocess.run(cmd, check=True, cwd=cwd, capture_output=capture_output, text=True)
        if capture_output:
            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print("Erro ao executar comando:", e)
        if capture_output:
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)
        sys.exit(1)

def clone_repo(clone_url, dest_dir):
    run_cmd(["git","clone","--depth","1", clone_url, dest_dir])

def check_java_files(project_dir):
    """Verifica se existem arquivos .java no projeto"""
    java_count = 0
    for root, dirs, files in os.walk(project_dir):
        # Ignora diretórios ocultos
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith('.java'):
                java_count += 1
    return java_count

def run_ck(ck_jar_path, project_dir, output_dir, use_jars="false", max_files="0", variables_and_fields="false"):
    os.makedirs(output_dir, exist_ok=True)
    
    # Verifica se há arquivos Java
    java_files = check_java_files(project_dir)
    print(f"Encontrados {java_files} arquivos .java no projeto")
    
    if java_files == 0:
        print("AVISO: Nenhum arquivo .java encontrado no projeto!")
        return False
    
    # Lista alguns arquivos Java para verificação
    print("Alguns arquivos .java encontrados:")
    count = 0
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith('.java') and count < 5:
                print(f"  {os.path.join(root, file)}")
                count += 1
    
    cmd = ["java", "-jar", ck_jar_path, project_dir, use_jars, max_files, variables_and_fields, output_dir]
    
    print(f"Executando CK com output em: {output_dir}")
    result = run_cmd(cmd, capture_output=False)
    
    # Aguarda um pouco para garantir que os arquivos foram escritos
    time.sleep(2)
    
    print("Conteúdo do diretório de saída após CK:")
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        print(f"Arquivos encontrados: {files}")
        for f in files:
            full_path = os.path.join(output_dir, f)
            if os.path.isfile(full_path):
                size = os.path.getsize(full_path)
                print(f"  {f}: {size} bytes")
    else:
        print(f"Diretório {output_dir} não existe!")
        
    return True

def find_csv(output_dir):
    """Busca arquivos CSV no diretório de saída"""
    if not os.path.exists(output_dir):
        return None
        
    csv_files = []
    for name in os.listdir(output_dir):
        if name.lower().endswith(".csv"):
            csv_files.append(os.path.join(output_dir, name))
    
    print(f"Arquivos CSV encontrados: {[os.path.basename(f) for f in csv_files]}")
    
    # Prioriza arquivo que contém "class" no nome
    for csv_file in csv_files:
        if "class" in os.path.basename(csv_file).lower():
            return csv_file
    
    # Se não encontrou um com "class", retorna o primeiro
    return csv_files[0] if csv_files else None

def summarize_class_csv(class_csv_path, out_summary_csv):
    try:
        df = pd.read_csv(class_csv_path)
        print(f"CSV carregado com {len(df)} linhas e colunas: {list(df.columns)}")
        
        # Lista de métricas a serem analisadas
        metrics = ['cbo', 'dit', 'lcom', 'lcom*', 'wmc', 'loc', 'noc', 'rfc', 'fanin', 'fanout']
        rows = []
        
        for m in metrics:
            # Tenta diferentes variações do nome da métrica
            col_name = None
            for col in df.columns:
                if col.lower() == m.lower():
                    col_name = col
                    break
            
            if col_name and col_name in df.columns:
                col = pd.to_numeric(df[col_name], errors='coerce').dropna()
                if len(col) == 0:
                    continue
                rows.append({
                    'metric': m,
                    'count': len(col),
                    'mean': float(col.mean()),
                    'median': float(col.median()),
                    'std': float(col.std()) if len(col) > 1 else 0.0,
                    'min': float(col.min()),
                    'max': float(col.max())
                })
                print(f"Métrica {m}: {len(col)} valores válidos")
        
        if rows:
            summary_df = pd.DataFrame(rows)
            summary_df.to_csv(out_summary_csv, index=False)
            print("Resumo salvo em:", out_summary_csv)
            print("\nResumo das métricas:")
            print(summary_df.to_string(index=False))
        else:
            print("Nenhuma métrica reconhecida encontrada no CSV")
            print("Colunas disponíveis:", list(df.columns))
    except Exception as e:
        print(f"Erro ao processar CSV: {e}")

def main():
    parser = argparse.ArgumentParser(description="Análise de métricas de código usando CK")
    parser.add_argument("--repo", required=True, help="owner/repo ou URL HTTPS completa")
    parser.add_argument("--ck", required=True, help="caminho para ck-...jar")
    parser.add_argument("--outdir", default="docs/results", help="onde salvar os resultados")
    parser.add_argument("--use-jars", default="false", choices=["true", "false"], 
                       help="usar JARs para melhor resolução de tipos")
    parser.add_argument("--max-files", default="0", help="máximo de arquivos por partição (0=automático)")
    parser.add_argument("--variables-fields", default="false", choices=["true", "false"],
                       help="incluir métricas de variáveis e campos")
    args = parser.parse_args()

    ck_jar = args.ck
    outdir = args.outdir
    repo = args.repo.strip()

    # Verifica se o JAR do CK existe
    if not os.path.exists(ck_jar):
        print(f"ERRO: JAR do CK não encontrado: {ck_jar}")
        sys.exit(1)

    # normaliza URL do repositório
    if repo.startswith("http://") or repo.startswith("https://") or repo.endswith(".git"):
        clone_url = repo
        shortname = os.path.splitext(os.path.basename(clone_url))[0]
    else:
        clone_url = f"https://github.com/{repo}.git"
        shortname = repo.replace("/","_")

    tmpdir = tempfile.mkdtemp(prefix="lab02_")
    proj_dir = os.path.join(tmpdir, shortname)

    try:
        print("Clonando", clone_url, "->", proj_dir)
        clone_repo(clone_url, proj_dir)

        ck_out = os.path.join(tmpdir, "ck_out")
        print("Executando CK...")
        success = run_ck(ck_jar, proj_dir, ck_out, args.use_jars, args.max_files, args.variables_fields)
        
        if not success:
            print("CK não foi executado devido à falta de arquivos Java")
            return

        class_csv = find_csv(ck_out)
        if not class_csv:
            print("ERRO: Nenhum arquivo CSV encontrado em", ck_out)
            print("Arquivos no diretório:", os.listdir(ck_out) if os.path.exists(ck_out) else "diretório não existe")
            return

        print(f"Usando arquivo CSV: {os.path.basename(class_csv)}")

        os.makedirs(outdir, exist_ok=True)
        raw_dest = os.path.join(outdir, f"metricas_raw_{shortname}.csv")
        shutil.copy(class_csv, raw_dest)
        print("CSV bruto copiado para:", raw_dest)

        summary_dest = os.path.join(outdir, f"metricas_summary_{shortname}.csv")
        summarize_class_csv(raw_dest, summary_dest)

    finally:
        print("Limpando clone temporário:", tmpdir)
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()