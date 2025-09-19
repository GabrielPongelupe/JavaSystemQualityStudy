#!/usr/bin/env python3
"""
Execução da análise paralela completa
"""
import os
import sys
import subprocess
import argparse

def run_step(step_name, command, description):
    """Executa um passo da análise"""
    print(f"\n{'='*60}")
    print(f"PASSO: {step_name}")
    print(f"{'='*60}")
    print(description)
    print(f"Executando: {command}")
    
    result = subprocess.run(command, check=True, shell=True)
    if result.returncode == 0:
        print(f"✅ {step_name} concluído com sucesso!")
        return True
    else:
        print(f"❌ {step_name} falhou!")
        return False

def main():
    parser = argparse.ArgumentParser(description="Análise paralela completa de repositórios Java")
    parser.add_argument("--ck", required=True, help="Caminho para CK JAR")
    parser.add_argument("--max-repos", type=int, default=1000, help="Número máximo de repositórios")
    parser.add_argument("--workers", type=int, default=6, help="Número de workers paralelos")
    parser.add_argument("--token", help="GitHub token")
    
    args = parser.parse_args()
    
    print("🚀 ANÁLISE PARALELA - LAB02S02")
    print("="*60)
    print(f"📊 Repositórios: {args.max_repos}")
    print(f"⚡ Workers: {args.workers}")
    print(f"🔧 CK JAR: {args.ck}")
    
    # Verificar requisitos
    print("\nVerificando requisitos...")
    try:
        import pandas
        import numpy
        import matplotlib
        import seaborn
        import scipy
        import requests
        print("✓ Todos os requisitos estão instalados!")
    except ImportError as e:
        print(f"❌ Requisito faltando: {e}")
        return 1
    
    # Verificar Java
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Java está instalado")
        else:
            print("❌ Java não encontrado")
            return 1
    except FileNotFoundError:
        print("❌ Java não encontrado")
        return 1
    
    # Verificar CK JAR
    if not os.path.exists(args.ck):
        print(f"❌ CK JAR não encontrado: {args.ck}")
        return 1
    print(f"✓ CK JAR encontrado: {args.ck}")
    
    # Verificar arquivo de repositórios
    repos_file = "repositorios_java.csv"
    if not os.path.exists(repos_file):
        print(f"❌ Arquivo de repositórios não encontrado: {repos_file}")
        print("Execute primeiro: python3 fetch_repos.py")
        return 1
    print(f"✓ Arquivo de repositórios encontrado: {repos_file}")
    
    # Passo 1: Análise paralela
    token_cmd = f"--token {args.token}" if args.token else ""
    cmd = f"python3 parallel_analysis.py --repos {repos_file} --ck {args.ck} --output results --max-repos {args.max_repos} --workers {args.workers} {token_cmd}"
    
    if not run_step(
        "1. ANÁLISE PARALELA",
        cmd,
        f"Analisando {args.max_repos} repositórios com {args.workers} workers..."
    ):
        return 1
    
    # Passo 2: Análise estatística
    analysis_file = "results/complete_analysis.csv"
    if os.path.exists(analysis_file):
        cmd = f"python3 statistical_analysis.py --data {analysis_file} --output results"
        
        if not run_step(
            "2. ANÁLISE ESTATÍSTICA",
            cmd,
            "Gerando visualizações e relatório final..."
        ):
            return 1
    else:
        print(f"❌ Arquivo de análise não encontrado: {analysis_file}")
        return 1
    
    # Resumo final
    print(f"\n{'='*60}")
    print("🎉 ANÁLISE PARALELA CONCLUÍDA!")
    print(f"{'='*60}")
    print(f"📁 Resultados em: results/")
    print(f"📊 Dados brutos: results/complete_analysis.csv")
    print(f"📈 Visualizações: results/plots/")
    print(f"📋 Relatório: results/final_report.md")
    print(f"⚡ Análise paralela com {args.workers} workers")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
