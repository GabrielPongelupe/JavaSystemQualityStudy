#!/usr/bin/env python3
"""
Workaround para o problema do CK não gerar arquivos CSV
Baseado na observação de que o CK executa com sucesso mas não produz saída
"""
import argparse, os, subprocess, tempfile, shutil, sys, pandas as pd
import time
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("CK execution timed out")

def run_cmd_with_monitoring(cmd, cwd=None, timeout=300):
    """Executa comando com monitoramento detalhado"""
    print("CMD:", " ".join(cmd))
    print("CWD:", cwd if cwd else os.getcwd())
    
    try:
        # Define timeout handler
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        stdout_lines = []
        stderr_lines = []
        
        # Lê output em tempo real
        while process.poll() is None:
            stdout_line = process.stdout.readline()
            stderr_line = process.stderr.readline()
            
            if stdout_line:
                stdout_lines.append(stdout_line.strip())
                print(f"STDOUT: {stdout_line.strip()}")
            
            if stderr_line:
                stderr_lines.append(stderr_line.strip())
                print(f"STDERR: {stderr_line.strip()}")
            
            time.sleep(0.1)
        
        # Lê qualquer output restante
        remaining_stdout, remaining_stderr = process.communicate()
        if remaining_stdout:
            stdout_lines.extend(remaining_stdout.strip().split('\n'))
            print(f"FINAL STDOUT: {remaining_stdout}")
        if remaining_stderr:
            stderr_lines.extend(remaining_stderr.strip().split('\n'))
            print(f"FINAL STDERR: {remaining_stderr}")
        
        signal.alarm(0)  # Cancela timeout
        
        return process.returncode, '\n'.join(stdout_lines), '\n'.join(stderr_lines)
        
    except TimeoutError:
        print(f"TIMEOUT: Comando demorou mais de {timeout} segundos")
        if 'process' in locals():
            process.kill()
        return -1, "", "TIMEOUT"
    except Exception as e:
        print(f"ERRO: {e}")
        return -1, "", str(e)
    finally:
        signal.alarm(0)

def try_different_ck_executions(ck_jar, project_dir, base_output_dir):
    """Tenta diferentes formas de executar o CK"""
    
    strategies = [
        {
            "name": "Estratégia 1: Executar no diretório do projeto",
            "setup": lambda out_dir: out_dir,
            "cwd": project_dir,
            "cmd_template": lambda jar, proj, out: [
                "java", "-jar", os.path.abspath(jar), ".", "false", "0", "false", os.path.abspath(out)
            ]
        },
        {
            "name": "Estratégia 2: Output no diretório atual",
            "setup": lambda out_dir: ".",
            "cwd": None,
            "cmd_template": lambda jar, proj, out: [
                "java", "-jar", jar, proj, "false", "0", "false", "."
            ]
        },
        {
            "name": "Estratégia 3: Usar classe Runner diretamente",
            "setup": lambda out_dir: out_dir,
            "cwd": None,
            "cmd_template": lambda jar, proj, out: [
                "java", "-cp", jar, "com.github.mauricioaniche.ck.Runner", proj, "false", "0", "false", out
            ]
        },
        {
            "name": "Estratégia 4: Java 8 compatibility flags",
            "setup": lambda out_dir: out_dir,
            "cwd": None,
            "cmd_template": lambda jar, proj, out: [
                "java", "--add-opens", "java.base/java.lang=ALL-UNNAMED",
                "--add-opens", "java.base/java.util=ALL-UNNAMED",
                "-jar", jar, proj, "false", "0", "false", out
            ]
        }
    ]
    
    for i, strategy in enumerate(strategies):
        print(f"\n{'='*60}")
        print(f"{strategy['name']}")
        print('='*60)
        
        # Prepara diretório de saída
        output_dir = os.path.join(base_output_dir, f"attempt_{i+1}")
        os.makedirs(output_dir, exist_ok=True)
        
        actual_output = strategy["setup"](output_dir)
        
        # Monta comando
        cmd = strategy["cmd_template"](ck_jar, project_dir, actual_output)
        
        print(f"Tentativa {i+1}: {strategy['name']}")
        print(f"Output directory: {actual_output}")
        
        # Executa comando
        returncode, stdout, stderr = run_cmd_with_monitoring(
            cmd, 
            cwd=strategy.get("cwd"),
            timeout=120
        )
        
        print(f"Return code: {returncode}")
        
        # Aguarda um pouco para arquivos serem escritos
        time.sleep(3)
        
        # Verifica resultados em vários locais possíveis
        search_dirs = [
            actual_output if os.path.isabs(actual_output) else os.path.join(os.getcwd(), actual_output),
            output_dir,
            os.getcwd(),
            project_dir,
            os.path.join(project_dir, "output"),
            "/tmp"
        ]
        
        found_files = []
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                for file in os.listdir(search_dir):
                    if file.endswith('.csv'):
                        file_path = os.path.join(search_dir, file)
                        size = os.path.getsize(file_path)
                        found_files.append((file_path, size))
                        print(f"ENCONTRADO: {file_path} ({size} bytes)")
        
        if found_files:
            print(f"SUCCESS! Arquivos encontrados na {strategy['name']}")
            return found_files
    
    return []

def manual_csv_generation(project_dir, output_file):
    """Gera CSV manualmente usando análise básica"""
    print("\nGerando CSV manualmente como fallback...")
    
    classes_data = []
    
    for root, dirs, files in os.walk(project_dir):
        # Ignora diretórios ocultos e de build
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['target', 'build', '.git']]
        
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Análise muito básica
                    lines = content.split('\n')
                    loc = len([l for l in lines if l.strip() and not l.strip().startswith('//')])
                    
                    # Conta métodos (aproximação)
                    methods = content.count('public ') + content.count('private ') + content.count('protected ')
                    methods = max(1, methods // 2)  # aproximação grosseira
                    
                    # Outras métricas básicas
                    imports = content.count('import ')
                    
                    class_name = file.replace('.java', '')
                    package = 'unknown'
                    
                    # Tenta extrair package
                    for line in lines[:20]:
                        if line.strip().startswith('package '):
                            package = line.strip().replace('package ', '').replace(';', '').strip()
                            break
                    
                    classes_data.append({
                        'class': f"{package}.{class_name}" if package != 'unknown' else class_name,
                        'file': file_path,
                        'loc': loc,
                        'wmc': max(1, methods),  # approximation
                        'cbo': min(imports, 20),  # approximation
                        'dit': 1,  # default
                        'noc': 0,  # default
                        'rfc': methods + imports,  # approximation
                        'lcom': 0,  # default
                        'fanin': 0,  # would need cross-reference analysis
                        'fanout': imports
                    })
                    
                except Exception as e:
                    print(f"Erro ao processar {file_path}: {e}")
    
    if classes_data:
        df = pd.DataFrame(classes_data)
        df.to_csv(output_file, index=False)
        print(f"CSV manual gerado: {output_file} com {len(classes_data)} classes")
        return True
    
    return False

def main():
    parser = argparse.ArgumentParser(description="CK com workaround para bugs")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--ck", required=True)
    parser.add_argument("--outdir", default="docs/results")
    args = parser.parse_args()

    ck_jar = args.ck
    outdir = args.outdir
    repo = args.repo.strip()

    # Verifica JAR
    if not os.path.exists(ck_jar):
        print(f"ERRO: JAR não encontrado: {ck_jar}")
        sys.exit(1)

    # Normaliza repo
    if repo.startswith("http"):
        clone_url = repo
        shortname = os.path.splitext(os.path.basename(repo))[0]
    else:
        clone_url = f"https://github.com/{repo}.git"
        shortname = repo.replace("/", "_")

    tmpdir = tempfile.mkdtemp(prefix="ck_workaround_")
    proj_dir = os.path.join(tmpdir, shortname)

    try:
        print(f"Clonando {clone_url}...")
        subprocess.run(["git", "clone", "--depth", "1", clone_url, proj_dir], 
                      check=True, capture_output=True)

        # Conta arquivos Java
        java_count = 0
        for root, dirs, files in os.walk(proj_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            java_count += sum(1 for f in files if f.endswith('.java'))

        print(f"Encontrados {java_count} arquivos .java")

        if java_count == 0:
            print("Nenhum arquivo Java encontrado!")
            return

        # Cria diretório de saída
        ck_output_base = os.path.join(tmpdir, "ck_attempts")
        os.makedirs(ck_output_base, exist_ok=True)

        # Tenta diferentes estratégias
        print("Tentando executar CK com diferentes estratégias...")
        found_csvs = try_different_ck_executions(ck_jar, proj_dir, ck_output_base)

        # Prepara resultado final
        os.makedirs(outdir, exist_ok=True)
        
        if found_csvs:
            # Usa o maior arquivo CSV encontrado
            best_csv = max(found_csvs, key=lambda x: x[1])  # maior por tamanho
            final_csv = os.path.join(outdir, f"metricas_raw_{shortname}.csv")
            shutil.copy(best_csv[0], final_csv)
            print(f"CSV copiado para: {final_csv}")
            
            # Gera resumo
            summary_csv = os.path.join(outdir, f"metricas_summary_{shortname}.csv")
            try:
                df = pd.read_csv(final_csv)
                print(f"CSV tem {len(df)} linhas e colunas: {list(df.columns)}")
                
                # Resumo básico
                metrics = ['cbo', 'dit', 'lcom', 'wmc', 'loc', 'noc', 'rfc']
                summary_data = []
                
                for metric in metrics:
                    col_found = None
                    for col in df.columns:
                        if col.lower() == metric.lower():
                            col_found = col
                            break
                    
                    if col_found:
                        values = pd.to_numeric(df[col_found], errors='coerce').dropna()
                        if len(values) > 0:
                            summary_data.append({
                                'metric': metric,
                                'count': len(values),
                                'mean': float(values.mean()),
                                'median': float(values.median()),
                                'std': float(values.std()) if len(values) > 1 else 0.0,
                                'min': float(values.min()),
                                'max': float(values.max())
                            })
                
                if summary_data:
                    pd.DataFrame(summary_data).to_csv(summary_csv, index=False)
                    print(f"Resumo salvo em: {summary_csv}")
            except Exception as e:
                print(f"Erro ao gerar resumo: {e}")
        
        else:
            print("CK falhou em todas as estratégias. Gerando CSV manual...")
            manual_csv = os.path.join(outdir, f"metricas_manual_{shortname}.csv")
            if manual_csv_generation(proj_dir, manual_csv):
                print(f"CSV manual gerado: {manual_csv}")
            else:
                print("Falha total - não foi possível gerar métricas")

    finally:
        print(f"Limpando: {tmpdir}")
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()