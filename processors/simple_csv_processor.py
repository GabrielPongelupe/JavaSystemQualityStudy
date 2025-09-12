#!/usr/bin/env python3
"""
Script simplificado que apenas processa CSVs existentes em docs/results
"""
import pandas as pd
import os
import argparse

def find_ck_csvs(csv_dir):
    """Encontra CSVs que contêm métricas de código CK"""
    ck_csvs = []
    
    if not os.path.exists(csv_dir):
        print(f"Diretório não encontrado: {csv_dir}")
        return []
    
    for file in os.listdir(csv_dir):
        if file.endswith('.csv'):
            file_path = os.path.join(csv_dir, file)
            try:
                # Lê apenas as primeiras linhas para verificar estrutura
                df_sample = pd.read_csv(file_path, nrows=5)
                columns = [col.lower() for col in df_sample.columns]
                
                # Verifica se tem métricas típicas do CK
                ck_metrics = ['cbo', 'dit', 'lcom', 'wmc', 'loc', 'class', 'file']
                has_ck_metrics = any(metric in columns for metric in ck_metrics)
                
                # Evita CSVs de repositórios GitHub
                github_metrics = ['stargazers_count', 'forks_count', 'full_name']
                has_github_metrics = any(metric in columns for metric in github_metrics)
                
                if has_ck_metrics and not has_github_metrics:
                    ck_csvs.append((file_path, file))
                    print(f"CSV CK encontrado: {file}")
                else:
                    print(f"CSV não-CK ignorado: {file} (colunas: {list(df_sample.columns)[:5]}...)")
                    
            except Exception as e:
                print(f"Erro ao ler {file}: {e}")
    
    return ck_csvs

def process_ck_csv(csv_path, repo_name="repositorio_analisado"):
    """Processa CSV do CK e gera resumo para o laboratório"""
    try:
        df = pd.read_csv(csv_path)
        print(f"\nProcessando: {os.path.basename(csv_path)}")
        print(f"Linhas: {len(df)}")
        print(f"Colunas: {list(df.columns)}")
        
        # Métricas obrigatórias do laboratório
        required_metrics = {
            'cbo': 'Coupling Between Objects',
            'dit': 'Depth Inheritance Tree', 
            'lcom': 'Lack of Cohesion of Methods'
        }
        
        # Métricas adicionais interessantes
        additional_metrics = {
            'wmc': 'Weighted Method Class',
            'loc': 'Lines of Code',
            'noc': 'Number of Children',
            'rfc': 'Response for Class',
            'fanin': 'Fan In',
            'fanout': 'Fan Out'
        }
        
        all_metrics = {**required_metrics, **additional_metrics}
        
        summary_data = []
        
        for metric_key, metric_name in all_metrics.items():
            # Procura a coluna correspondente (case insensitive)
            col_found = None
            for col in df.columns:
                if col.lower() == metric_key.lower():
                    col_found = col
                    break
            
            if col_found:
                # Converte para numérico e remove valores inválidos
                values = pd.to_numeric(df[col_found], errors='coerce').dropna()
                
                if len(values) > 0:
                    is_required = metric_key in required_metrics
                    
                    summary_data.append({
                        'repositorio': repo_name,
                        'metrica': metric_key.upper(),
                        'nome_metrica': metric_name,
                        'obrigatoria': is_required,
                        'classes_analisadas': len(values),
                        'media': round(values.mean(), 2),
                        'mediana': round(values.median(), 2),
                        'desvio_padrao': round(values.std(), 2) if len(values) > 1 else 0.0,
                        'minimo': int(values.min()),
                        'maximo': int(values.max()),
                        'q1': round(values.quantile(0.25), 2),
                        'q3': round(values.quantile(0.75), 2)
                    })
                    
                    print(f"  ✓ {metric_key.upper()}: {len(values)} valores válidos")
                else:
                    print(f"  ✗ {metric_key.upper()}: nenhum valor válido")
            else:
                print(f"  ✗ {metric_key.upper()}: coluna não encontrada")
        
        return summary_data
        
    except Exception as e:
        print(f"Erro ao processar CSV: {e}")
        return []

def generate_lab_report(summary_data, output_path):
    """Gera relatório final para o laboratório"""
    if not summary_data:
        print("Nenhum dado para gerar relatório")
        return False
    
    try:
        # Converte para DataFrame
        df = pd.DataFrame(summary_data)
        
        # Salva CSV completo
        df.to_csv(output_path, index=False)
        
        # Mostra resumo das métricas obrigatórias
        required_metrics = df[df['obrigatoria'] == True]
        
        print(f"\n{'='*60}")
        print("RELATÓRIO PARA LAB02S01")
        print(f"{'='*60}")
        print(f"Arquivo gerado: {output_path}")
        print(f"Total de métricas: {len(df)}")
        print(f"Métricas obrigatórias encontradas: {len(required_metrics)}")
        
        if len(required_metrics) > 0:
            print("\nMétricas obrigatórias (CBO, DIT, LCOM):")
            print(required_metrics[['metrica', 'classes_analisadas', 'media', 'mediana', 'desvio_padrao']].to_string(index=False))
        
        print("\nTodas as métricas:")
        print(df[['metrica', 'classes_analisadas', 'media', 'mediana']].to_string(index=False))
        
        return True
        
    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Processa CSVs existentes do CK")
    parser.add_argument("--csv-dir", default="docs/results", help="Diretório com CSVs")
    parser.add_argument("--output", default="docs/results/relatorio_lab02s01.csv", help="Arquivo de relatório")
    parser.add_argument("--repo-name", default="repositorio_java", help="Nome do repositório analisado")
    args = parser.parse_args()
    
    print("Processador de CSVs CK para Lab02S01")
    print("=" * 50)
    
    # Encontra CSVs do CK
    ck_csvs = find_ck_csvs(args.csv_dir)
    
    if not ck_csvs:
        print(f"\nNenhum CSV do CK encontrado em {args.csv_dir}")
        print("Verifique se você tem arquivos CSV com métricas de código (CBO, DIT, LCOM, etc.)")
        return
    
    # Usa o primeiro CSV válido encontrado
    csv_path, csv_name = ck_csvs[0]
    print(f"\nUsando: {csv_name}")
    
    # Processa o CSV
    summary_data = process_ck_csv(csv_path, args.repo_name)
    
    if summary_data:
        # Gera relatório final
        if generate_lab_report(summary_data, args.output):
            print(f"\n✅ SUCESSO! Relatório gerado para Lab02S01")
            print(f"Arquivo: {args.output}")
        else:
            print("❌ Falha ao gerar relatório")
    else:
        print("❌ Nenhuma métrica válida encontrada")

if __name__ == "__main__":
    main()