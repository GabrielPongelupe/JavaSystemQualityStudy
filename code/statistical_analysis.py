#!/usr/bin/env python3
"""
Análise estatística e geração de relatório final
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from datetime import datetime
import os

def load_analysis_data(csv_file):
    """Carrega dados da análise completa"""
    df = pd.read_csv(csv_file)
    print(f"Dados carregados: {len(df)} repositórios")
    return df

def clean_data(df):
    """Limpa dados para análise"""
    # Remover linhas com valores nulos críticos
    critical_cols = ['stars', 'cbo_mean', 'dit_mean', 'lcom_mean']
    available_critical = [col for col in critical_cols if col in df.columns]
    
    if not available_critical:
        print("⚠️  Nenhuma coluna crítica encontrada")
        return None
    
    clean_df = df[available_critical].dropna()
    
    # Remover outliers extremos
    for col in clean_df.select_dtypes(include=[np.number]).columns:
        Q1 = clean_df[col].quantile(0.25)
        Q3 = clean_df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        clean_df = clean_df[(clean_df[col] >= lower_bound) & (clean_df[col] <= upper_bound)]
    
    print(f"Dados limpos: {len(clean_df)} repositórios")
    return clean_df

def analyze_correlations(df):
    """Analisa correlações entre métricas"""
    print("\n" + "="*60)
    print("ANÁLISE DE CORRELAÇÕES")
    print("="*60)
    
    # Variáveis de processo e qualidade
    process_vars = ['stars', 'age_years', 'releases', 'size_kb', 'loc']
    quality_vars = ['cbo_mean', 'dit_mean', 'lcom_mean', 'wmc_mean']
    
    # Filtrar variáveis disponíveis
    available_process = [var for var in process_vars if var in df.columns]
    available_quality = [var for var in quality_vars if var in df.columns]
    
    if not available_process or not available_quality:
        print("⚠️  Variáveis insuficientes para análise")
        return None
    
    results = {}
    
    print(f"Analisando {len(df)} repositórios com dados completos")
    
    # Mapeamento das questões de pesquisa
    rq_mappings = {
        'RQ01': ('stars', 'Popularidade'),
        'RQ02': ('age_years', 'Maturidade'),
        'RQ03': ('releases', 'Atividade'),
        'RQ04': ('size_kb', 'Tamanho')
    }
    
    for rq, (process_var, process_name) in rq_mappings.items():
        if process_var not in df.columns:
            continue
            
        print(f"\n--- {rq}: {process_name} vs Qualidade ---")
        results[rq] = {}
        
        for quality_var in available_quality:
            if quality_var in df.columns:
                # Remover valores nulos
                clean_data = df[[process_var, quality_var]].dropna()
                
                if len(clean_data) > 3:
                    # Correlação de Pearson
                    pearson_r, pearson_p = stats.pearsonr(clean_data[process_var], clean_data[quality_var])
                    
                    # Correlação de Spearman
                    spearman_r, spearman_p = stats.spearmanr(clean_data[process_var], clean_data[quality_var])
                    
                    results[rq][quality_var] = {
                        'pearson_r': pearson_r,
                        'pearson_p': pearson_p,
                        'spearman_r': spearman_r,
                        'spearman_p': spearman_p,
                        'n': len(clean_data)
                    }
                    
                    # Interpretação
                    strength = "forte" if abs(pearson_r) > 0.7 else "moderada" if abs(pearson_r) > 0.3 else "fraca"
                    direction = "positiva" if pearson_r > 0 else "negativa"
                    significance = "significativa" if pearson_p < 0.05 else "não significativa"
                    
                    print(f"  {quality_var}: r={pearson_r:.3f} (p={pearson_p:.3f}) - {strength} {direction} {significance}")
    
    return results

def create_visualizations(df, output_dir):
    """Cria visualizações dos dados"""
    print("\n" + "="*60)
    print("GERANDO VISUALIZAÇÕES")
    print("="*60)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Configuração do estilo
    plt.style.use('default')
    sns.set_palette("husl")
    
    # 1. Matriz de correlação
    numeric_cols = ['stars', 'age_years', 'releases', 'size_kb', 'loc', 
                   'cbo_mean', 'dit_mean', 'lcom_mean', 'wmc_mean']
    available_cols = [col for col in numeric_cols if col in df.columns]
    
    if len(available_cols) > 2:
        corr_matrix = df[available_cols].corr()
        
        plt.figure(figsize=(12, 10))
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
        plt.title('Matriz de Correlação - Métricas de Processo vs Qualidade', fontsize=14)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/correlation_matrix.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Matriz de correlação salva")
    
    # 2. Scatter plots para cada RQ
    rq_mappings = {
        'RQ01': ('stars', 'Popularidade (Estrelas)'),
        'RQ02': ('age_years', 'Maturidade (Anos)'),
        'RQ03': ('releases', 'Atividade (Releases)'),
        'RQ04': ('size_kb', 'Tamanho (KB)')
    }
    
    quality_vars = ['cbo_mean', 'dit_mean', 'lcom_mean']
    
    for rq, (process_var, process_name) in rq_mappings.items():
        if process_var not in df.columns:
            continue
            
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle(f'{rq}: {process_name} vs Qualidade', fontsize=16)
        
        for i, quality_var in enumerate(quality_vars):
            if quality_var in df.columns:
                # Remover valores nulos
                plot_data = df[[process_var, quality_var]].dropna()
                
                if len(plot_data) > 0:
                    # Scatter plot
                    axes[i].scatter(plot_data[process_var], plot_data[quality_var], 
                                  alpha=0.6, s=50, color='blue')
                    
                    # Linha de tendência
                    z = np.polyfit(plot_data[process_var], plot_data[quality_var], 1)
                    p = np.poly1d(z)
                    axes[i].plot(plot_data[process_var], p(plot_data[process_var]), 
                               "r--", alpha=0.8, linewidth=2)
                    
                    # Correlação
                    corr = plot_data[process_var].corr(plot_data[quality_var])
                    axes[i].set_title(f'{quality_var}\n(r = {corr:.3f})')
                    axes[i].set_xlabel(process_name)
                    axes[i].set_ylabel(quality_var.replace('_', ' ').title())
                    axes[i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/scatter_{rq.lower()}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Scatter plot {rq} salvo")
    
    # 3. Distribuições das métricas
    quality_vars = ['cbo_mean', 'dit_mean', 'lcom_mean', 'wmc_mean']
    available_vars = [var for var in quality_vars if var in df.columns]
    
    if available_vars:
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        axes = axes.flatten()
        
        for i, var in enumerate(available_vars[:4]):
            if i < len(axes):
                data = df[var].dropna()
                if len(data) > 0:
                    axes[i].hist(data, bins=30, alpha=0.7, edgecolor='black')
                    mean_val = data.mean()
                    median_val = data.median()
                    axes[i].axvline(mean_val, color='red', linestyle='--', 
                                  label=f'Média: {mean_val:.2f}')
                    axes[i].axvline(median_val, color='green', linestyle='--', 
                                  label=f'Mediana: {median_val:.2f}')
                    axes[i].set_title(f'Distribuição de {var.replace("_", " ").title()}')
                    axes[i].set_xlabel(var.replace('_', ' ').title())
                    axes[i].set_ylabel('Frequência')
                    axes[i].legend()
                    axes[i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/distributions.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Distribuições salvas")
    
    print(f"Visualizações salvas em: {output_dir}/")

def generate_final_report(df, correlation_results, output_file):
    """Gera relatório final"""
    print("\n" + "="*60)
    print("GERANDO RELATÓRIO FINAL")
    print("="*60)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Relatório Final - Lab02S02\n")
        f.write("## Estudo das Características de Qualidade de Sistemas Java\n\n")
        f.write(f"**Data de geração:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"**Repositórios analisados:** {len(df)}\n\n")
        
        # Introdução
        f.write("## 1. Introdução\n\n")
        f.write("Este relatório apresenta a análise de qualidade de sistemas Java desenvolvidos ")
        f.write("em repositórios open-source do GitHub. O objetivo é investigar a relação entre ")
        f.write("características do processo de desenvolvimento e métricas de qualidade de código.\n\n")
        
        # Hipóteses
        f.write("## 2. Hipóteses\n\n")
        hypotheses = {
            'RQ01': {
                'question': 'Qual a relação entre a popularidade dos repositórios e suas características de qualidade?',
                'hypothesis': 'Repositórios mais populares (mais estrelas) tendem a ter melhor qualidade de código.'
            },
            'RQ02': {
                'question': 'Qual a relação entre a maturidade dos repositórios e suas características de qualidade?',
                'hypothesis': 'Repositórios mais maduros (mais antigos) podem ter pior qualidade devido ao débito técnico.'
            },
            'RQ03': {
                'question': 'Qual a relação entre a atividade dos repositórios e suas características de qualidade?',
                'hypothesis': 'Repositórios mais ativos (mais releases) mantêm melhor qualidade.'
            },
            'RQ04': {
                'question': 'Qual a relação entre o tamanho dos repositórios e suas características de qualidade?',
                'hypothesis': 'Repositórios maiores tendem a ter pior qualidade devido à complexidade.'
            }
        }
        
        for rq, data in hypotheses.items():
            f.write(f"### {rq}\n")
            f.write(f"**Pergunta:** {data['question']}\n\n")
            f.write(f"**Hipótese:** {data['hypothesis']}\n\n")
        
        # Metodologia
        f.write("## 3. Metodologia\n\n")
        f.write("### 3.1 Coleta de Dados\n")
        f.write("- **Repositórios:** Top 1000 repositórios Java mais populares do GitHub\n")
        f.write("- **Métricas de processo:** Popularidade, maturidade, atividade, tamanho\n")
        f.write("- **Métricas de qualidade:** CBO, DIT, LCOM, WMC (via CK Metrics)\n")
        f.write("- **Análise estatística:** Correlações de Pearson e Spearman\n\n")
        
        # Resultados
        f.write("## 4. Resultados\n\n")
        
        # Estatísticas descritivas
        f.write("### 4.1 Estatísticas Descritivas\n\n")
        numeric_cols = ['stars', 'age_years', 'releases', 'size_kb', 'loc', 
                       'cbo_mean', 'dit_mean', 'lcom_mean', 'wmc_mean']
        available_cols = [col for col in numeric_cols if col in df.columns]
        
        if available_cols:
            desc_stats = df[available_cols].describe()
            f.write("```\n")
            f.write(desc_stats.to_string())
            f.write("\n```\n\n")
        
        # Correlações
        f.write("### 4.2 Análise de Correlações\n\n")
        if correlation_results:
            for rq, correlations in correlation_results.items():
                f.write(f"#### {rq}\n\n")
                for metric, stats in correlations.items():
                    f.write(f"**{metric}:**\n")
                    f.write(f"- Pearson r = {stats['pearson_r']:.3f} (p = {stats['pearson_p']:.3f})\n")
                    f.write(f"- Spearman ρ = {stats['spearman_r']:.3f} (p = {stats['spearman_p']:.3f})\n")
                    f.write(f"- N = {stats['n']}\n\n")
        
        # Discussão
        f.write("## 5. Discussão\n\n")
        f.write("### 5.1 Principais Descobertas\n")
        f.write("- Análise baseada em dados reais de repositórios Java\n")
        f.write("- Correlações entre características de processo e qualidade\n")
        f.write("- Visualizações para interpretação dos resultados\n\n")
        
        f.write("### 5.2 Limitações\n")
        f.write("- Análise baseada em snapshot dos repositórios\n")
        f.write("- Métricas CK podem não capturar todos os aspectos de qualidade\n")
        f.write("- Correlação não implica causalidade\n\n")
        
        f.write("## 6. Conclusões\n\n")
        f.write("Este estudo fornece insights sobre a relação entre características do processo ")
        f.write("de desenvolvimento e qualidade de código em repositórios Java open-source. ")
        f.write("Os resultados podem informar práticas de desenvolvimento e políticas de qualidade.\n")
    
    print(f"Relatório final salvo em: {output_file}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Análise estatística e relatório final")
    parser.add_argument("--data", required=True, help="CSV com dados da análise completa")
    parser.add_argument("--output", default="results", help="Diretório de saída")
    
    args = parser.parse_args()
    
    # Carregar dados
    df = load_analysis_data(args.data)
    
    # Limpar dados
    clean_df = clean_data(df)
    if clean_df is None:
        print("❌ Dados insuficientes para análise")
        return
    
    # Análise de correlações
    correlation_results = analyze_correlations(clean_df)
    
    # Visualizações
    plots_dir = os.path.join(args.output, "plots")
    create_visualizations(clean_df, plots_dir)
    
    # Relatório final
    report_file = os.path.join(args.output, "relatorio_final_lab02s02.md")
    generate_final_report(clean_df, correlation_results, report_file)
    
    print("\n" + "="*60)
    print("ANÁLISE ESTATÍSTICA CONCLUÍDA!")
    print("="*60)
    print(f"📊 Dados analisados: {len(clean_df)} repositórios")
    print(f"📁 Resultados em: {args.output}/")
    print(f"📄 Relatório: {report_file}")

if __name__ == "__main__":
    main()
