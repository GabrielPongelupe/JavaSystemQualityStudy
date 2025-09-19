# Java System Quality Study - Lab02

Este repositório implementa o **Laboratório 02** da disciplina de Laboratório de Experimentação de Software: um estudo das características de qualidade de sistemas Java usando métricas CK.

## Objetivo

Analisar aspectos da qualidade de repositórios Java correlacionando-os com características do processo de desenvolvimento, respondendo às seguintes questões de pesquisa:

- **RQ01**: Qual a relação entre a popularidade dos repositórios e suas características de qualidade?
- **RQ02**: Qual a relação entre a maturidade dos repositórios e suas características de qualidade?
- **RQ03**: Qual a relação entre a atividade dos repositórios e suas características de qualidade?
- **RQ04**: Qual a relação entre o tamanho dos repositórios e suas características de qualidade?

---

## Estrutura do Repositório

```
JavaSystemQualityStudy/
├── src/                           # Scripts principais
│   ├── fetch_repos.py            # Busca top-1000 repositórios Java do GitHub
│   ├── analyze_repo.py           # Automatiza clone + análise CK + limpeza 
│   ├── alternative_ck_runner.py      # Script com múltiplas estratégias para CK
│   └── utils.py                  # Funções auxiliares
├── processors/                           # Scripts principais
|   └── advanced_ck_diagnostic.py # Diagnostico se o CK está funcionando
│   ├── simple_csv_processor.py   # Processa CSVs existentes do CK
├── docs/
│   └── results/                  # CSVs de resultados
│       ├── test_ck_outclass.csv  # Métricas por classe (gerado pelo CK)
│       ├── test_ck_outmethod.csv # Métricas por método
│       ├── test_ck_outfield.csv  # Métricas por campo
│       └── relatorio_lab02s01.csv # Relatório final processado
├── tools/
│   └── ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar # Ferramenta CK Metrics
├── repositorios_java.csv         # Lista dos 1000 repositórios
├── requirements.txt              # Dependências Python
└── README.md                     # Este arquivo
```

---

## Requisitos do Sistema

### Software Necessário

- **Python 3.8+** 
- **Java 8+** (testado com Java 21)
- **Git**
- **Conexão com internet**

### Token do GitHub (Recomendado)

Para evitar limites da API do GitHub, crie um token:

1. Acesse [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Clique em "Generate new token (classic)"
3. Selecione escopo "public_repo"
4. Copie o token gerado

---

## Configuração do Ambiente

### 1. Clone o Repositório

```bash
git clone https://github.com/seu-usuario/JavaSystemQualityStudy.git
cd JavaSystemQualityStudy
```

### 2. Configure o Ambiente Python

```bash
# Cria ambiente virtual
python3 -m venv .venv

# Ativa ambiente virtual
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate        # Windows

# Instala dependências
pip install -r requirements.txt
```

### 3. Configure Token GitHub (Opcional mas Recomendado)

```bash
export GITHUB_TOKEN=seu_token_aqui
```

---

## Passo a Passo para Lab02S01

O **Lab02S01** requer três entregas:

### 1. Lista dos 1.000 Repositórios Java Mais Populares

```bash
python3 src/fetch_repos.py \
  --token $GITHUB_TOKEN \
  --out repositorios_java.csv \
  --pages 10
```

**O que acontece:**
- Busca os top 1000 repositórios Java por número de estrelas
- Coleta metadados: nome, URL, estrelas, forks, data de criação, etc.
- Salva em `repositorios_java.csv`
- **Tempo estimado**: 2-5 minutos

**Parâmetros importantes:**
- `--pages 10`: Busca 10 páginas × 100 repos = 1000 repositórios
- `--token`: Evita limite de 60 requisições/hora da API
- `--language java`: Filtra apenas repositórios Java

### 2. Script de Automação de Clone e Coleta de Métricas

O script principal é `src/analyze_repo.py`. Teste com um repositório pequeno:

```bash
python3 src/analyze_repo.py \
  --repo apache/commons-lang \
  --ck tools/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar \
  --outdir docs/results
```

**O que o script faz:**
1. **Clone**: Faz `git clone --depth 1` do repositório
2. **Análise**: Executa CK Metrics no código Java
3. **Coleta**: Extrai métricas CBO, DIT, LCOM, WMC, LOC, etc.
4. **Processamento**: Gera CSVs com dados brutos e resumo estatístico
5. **Limpeza**: Remove clone temporário

**Problema Conhecido**: A ferramenta CK pode não gerar CSVs em algumas configurações. Se isso acontecer, use o script alternativo:

```bash
python3 src/ck_bug_workaround.py \
  --repo apache/commons-lang \
  --ck tools/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar \
  --outdir docs/results
```

### 3. CSV com Métricas de 1 Repositório

Se você já tem CSVs do CK na pasta `docs/results` (como `test_ck_outclass.csv`), processe-os:

```bash
python3 src/simple_csv_processor.py \
  --csv-dir docs/results \
  --repo-name "repositorio_exemplo" \
  --output docs/results/relatorio_lab02s01.csv
```

**O que gera:**
- Relatório com estatísticas das métricas obrigatórias (CBO, DIT, LCOM)
- Métricas adicionais (WMC, LOC, NOC, RFC)
- Estatísticas: média, mediana, desvio padrão, min, max, quartis

---

## Métricas Coletadas

### Métricas Obrigatórias (conforme laboratório)

- **CBO (Coupling Between Objects)**: Acoplamento entre objetos
- **DIT (Depth Inheritance Tree)**: Profundidade da árvore de herança
- **LCOM (Lack of Cohesion of Methods)**: Falta de coesão dos métodos

### Métricas Adicionais

- **WMC (Weighted Method Class)**: Complexidade dos métodos da classe
- **LOC (Lines of Code)**: Linhas de código fonte
- **NOC (Number of Children)**: Número de subclasses diretas
- **RFC (Response for Class)**: Número de métodos invocados
- **Fan-in/Fan-out**: Dependências de entrada e saída

---

## Resolução de Problemas

### CK não gera CSVs

**Sintoma**: CK mostra "Metrics extracted!!!" mas não cria arquivos CSV.

**Soluções:**

1. **Use CSVs existentes**: Se você tem `test_ck_*.csv` em `docs/results`, processe-os:
   ```bash
   python3 src/simple_csv_processor.py
   ```

2. **Script com múltiplas estratégias**:
   ```bash
   python3 src/ck_bug_workaround.py --repo apache/commons-lang --ck tools/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar
   ```

3. **Teste com Java 8/11**: O CK pode ter problemas com Java versões mais recentes.

### Limite da API GitHub

**Sintoma**: Erro 403 ou "API rate limit exceeded"

**Solução**: Configure um token do GitHub:
```bash
export GITHUB_TOKEN=seu_token_aqui
```

### Projeto sem arquivos Java

**Sintoma**: "Nenhum arquivo .java encontrado"

**Solução**: Verifique se o repositório realmente contém código Java ou se há arquivos em subdiretórios como `src/main/java/`.

---

## Estrutura dos Dados de Saída

### repositorios_java.csv
```csv
full_name,html_url,stargazers_count,forks_count,created_at,updated_at,size,language,open_issues_count
spring-projects/spring-framework,https://github.com/spring-projects/spring-framework,56234,37891,2008-08-21T16:20:38Z,2024-01-15T10:30:45Z,85432,Java,245
```

### Arquivos CK (test_ck_outclass.csv)
```csv
class,file,cbo,dit,lcom,wmc,loc,noc,rfc
com.example.MyClass,/path/to/MyClass.java,5,2,0.8,12,156,0,18
```

### Relatório Final (relatorio_lab02s01.csv)
```csv
repositorio,metrica,nome_metrica,classes_analisadas,media,mediana,desvio_padrao,minimo,maximo
repositorio_exemplo,CBO,Coupling Between Objects,245,4.2,3.0,3.8,0,28
repositorio_exemplo,DIT,Depth Inheritance Tree,245,2.1,2.0,1.2,1,8
```

---

## Lab02S02 - Análise Completa e Relatório Final

### Execução Rápida

```bash
# 1. Instalar dependências
pip install -r src/requirements.txt

# 2. Executar análise completa (1000 repositórios)
python run_lab02s02.py --repos repositorios_java.csv --ck tools/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar

# 3. Teste com poucos repositórios (recomendado primeiro)
python test_analysis.py
```

### Funcionalidades Implementadas

1. **Análise Completa dos 1000 Repositórios**
   - Coleta automática de métricas do GitHub
   - Análise CK de qualidade de código
   - Processamento estatístico avançado

2. **Visualizações e Gráficos**
   - Matriz de correlação
   - Scatter plots com tendências
   - Distribuições das métricas
   - Box plots por quartis de popularidade

3. **Testes Estatísticos**
   - Correlação de Pearson (linear)
   - Correlação de Spearman (monotônica)
   - Correlação de Kendall
   - Testes de normalidade (Shapiro-Wilk)
   - Análise por quartis

4. **Relatório Final Automático**
   - Hipóteses para cada questão de pesquisa
   - Resultados estatísticos
   - Discussão e interpretação
   - Limitações e próximos passos

### Instruções Detalhadas

#### Passo 1: Preparação do Ambiente

```bash
# Instalar dependências Python
pip install -r src/requirements.txt

# Verificar Java (necessário para CK)
java -version

# Verificar se CK JAR existe
ls -la tools/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar
```

#### Passo 2: Coleta de Repositórios (se necessário)

```bash
# Buscar top 1000 repositórios Java
python src/fetch_repos.py --out repositorios_java.csv --pages 10
```

#### Passo 3: Teste com Poucos Repositórios (Recomendado)

```bash
# Teste rápido com 3 repositórios
python test_analysis.py
```

#### Passo 4: Análise Completa

```bash
# Análise completa (pode demorar várias horas)
python run_lab02s02.py \
  --repos repositorios_java.csv \
  --ck tools/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar \
  --outdir docs/results \
  --max-repos 100  # Limite para teste

# Para análise completa (1000 repositórios)
python run_lab02s02.py \
  --repos repositorios_java.csv \
  --ck tools/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar \
  --token $GITHUB_TOKEN  # Opcional, evita rate limits
```

#### Passo 5: Análise dos Resultados

```bash
# Visualizar resultados
ls -la docs/results/
ls -la docs/results/plots/

# Ler relatório final
cat docs/results/relatorio_final_lab02s02.md
```

### Estrutura de Saída

```
docs/results/
├── complete_analysis.csv          # Dados brutos de todos os repositórios
├── relatorio_final_lab02s02.md    # Relatório final do laboratório
├── statistical_report.md          # Relatório estatístico detalhado
└── plots/                         # Visualizações
    ├── correlation_heatmap.png
    ├── scatter_stars.png
    ├── distributions.png
    ├── quality_by_popularity_quartiles.png
    └── pairplot.png
```

### Parâmetros de Configuração

- `--repos`: Arquivo CSV com lista de repositórios
- `--ck`: Caminho para ferramenta CK JAR
- `--outdir`: Diretório de saída (padrão: docs/results)
- `--token`: Token GitHub (opcional, evita rate limits)
- `--max-repos`: Limite de repositórios para analisar
- `--skip-checks`: Pula verificações de requisitos
- `--stats-only`: Executa apenas análise estatística

---

## Scripts de Exemplo

### Análise de múltiplos repositórios
```bash
#!/bin/bash
repos=("apache/commons-lang" "google/gson" "junit-team/junit5")

for repo in "${repos[@]}"; do
    echo "Analisando $repo..."
    python3 src/analyze_repo.py --repo $repo --ck tools/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar --outdir docs/results
    sleep 5  # Evita sobrecarga
done
```

### Verificação de CSVs existentes
```bash
python3 -c "
import pandas as pd
import os

csv_dir = 'docs/results'
for file in os.listdir(csv_dir):
    if file.endswith('.csv'):
        try:
            df = pd.read_csv(os.path.join(csv_dir, file))
            print(f'{file}: {len(df)} linhas, colunas: {list(df.columns)[:5]}...')
        except:
            print(f'{file}: erro ao ler')
"
```

---

## Contribuição e Suporte

Este é um projeto acadêmico para a disciplina de Laboratório de Experimentação de Software.

**Problemas conhecidos:**
- CK pode não funcionar em todas as configurações Java
- Alguns repositórios grandes podem demorar para processar
- Limites de API do GitHub sem token

**Suporte**: Consulte a documentação da ferramenta CK e as issues do repositório original para problemas específicos da análise de métricas.