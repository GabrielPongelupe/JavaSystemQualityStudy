# Lab02S02 - Análise de Qualidade de Sistemas Java

## 🎯 Objetivo

Analisar aspectos da qualidade de repositórios Java correlacionando-os com características do processo de desenvolvimento, respondendo às seguintes questões de pesquisa:

- **RQ01**: Qual a relação entre a popularidade dos repositórios e suas características de qualidade?
- **RQ02**: Qual a relação entre a maturidade dos repositórios e suas características de qualidade?
- **RQ03**: Qual a relação entre a atividade dos repositórios e suas características de qualidade?
- **RQ04**: Qual a relação entre o tamanho dos repositórios e suas características de qualidade?

## 🚀 Execução Rápida

### 1. Configuração Inicial
```bash
# Instalar dependências
pip install -r requirements.txt

# Verificar Java
java -version

# Verificar CK JAR
ls -la ../tools/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar
```

### 2. Análise Completa
```bash
# Análise completa (1000 repositórios)
python3 run_complete_analysis.py --ck ../tools/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar

# Análise com limite (recomendado para teste)
python3 run_complete_analysis.py --ck ../tools/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar --max-repos 50

# Com token GitHub (opcional, evita rate limits)
python3 run_complete_analysis.py --ck ../tools/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar --token $GITHUB_TOKEN
```

### 3. Análise Individual
```bash
# Analisar um repositório específico
python3 analyze_repo.py --repo apache/commons-lang --ck ../tools/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar
```

## 📁 Estrutura do Projeto

```
code/
├── requirements.txt              # Dependências Python
├── fetch_repos.py               # Busca repositórios do GitHub
├── analyze_repo.py              # Análise de repositório individual
├── batch_analysis.py            # Análise em lote
├── statistical_analysis.py      # Análise estatística e visualizações
├── run_complete_analysis.py     # Script principal
└── results/                     # Resultados (gerado automaticamente)
    ├── complete_analysis.csv    # Dados brutos
    ├── plots/                   # Visualizações
    │   ├── correlation_matrix.png
    │   ├── scatter_rq01.png
    │   ├── scatter_rq02.png
    │   ├── scatter_rq03.png
    │   ├── scatter_rq04.png
    │   └── distributions.png
    └── relatorio_final_lab02s02.md  # Relatório final
```

## 🔧 Scripts Disponíveis

### `fetch_repos.py`
Busca os top 1000 repositórios Java do GitHub.

```bash
python3 fetch_repos.py --output repositorios_java.csv --token $GITHUB_TOKEN
```

### `analyze_repo.py`
Analisa um repositório individual.

```bash
python3 analyze_repo.py --repo owner/repo --ck path/to/ck.jar --output results
```

### `batch_analysis.py`
Analisa múltiplos repositórios em lote.

```bash
python3 batch_analysis.py --repos repositorios_java.csv --ck path/to/ck.jar --output results
```

### `statistical_analysis.py`
Gera análise estatística e visualizações.

```bash
python3 statistical_analysis.py --data results/complete_analysis.csv --output results
```

## 📊 Métricas Coletadas

### Métricas de Processo
- **Popularidade**: Número de estrelas
- **Maturidade**: Idade do repositório (anos)
- **Atividade**: Número de releases
- **Tamanho**: Linhas de código (LOC) e tamanho em KB

### Métricas de Qualidade (CK Metrics)
- **CBO**: Coupling Between Objects (acoplamento)
- **DIT**: Depth Inheritance Tree (profundidade de herança)
- **LCOM**: Lack of Cohesion of Methods (falta de coesão)
- **WMC**: Weighted Method Class (complexidade)
- **LOC**: Lines of Code (linhas de código)
- **RFC**: Response for Class (métodos invocados)
- **NOC**: Number of Children (subclasses)

## 📈 Visualizações Geradas

1. **Matriz de Correlação**: Correlações entre todas as métricas
2. **Scatter Plots**: Relação entre processo e qualidade para cada RQ
3. **Distribuições**: Distribuições das métricas de qualidade
4. **Box Plots**: Análise por quartis de popularidade

## 📄 Relatório Final

O relatório final inclui:
- Introdução e hipóteses
- Metodologia
- Resultados estatísticos
- Análise de correlações
- Discussão e conclusões
- Limitações

## ⚙️ Configuração

### Token GitHub (Opcional)
Para evitar limites da API do GitHub:
```bash
export GITHUB_TOKEN=seu_token_aqui
```

### Parâmetros de Análise
- `--max-repos`: Limite de repositórios para analisar
- `--start-from`: Índice para começar a análise
- `--token`: Token GitHub para evitar rate limits

## 🐛 Resolução de Problemas

### CK não gera CSVs
- Verifique se Java está instalado: `java -version`
- Verifique se o CK JAR existe e é válido
- O CK gera CSVs na raiz do projeto, não no diretório especificado

### Erro de dependências
```bash
pip install -r requirements.txt
```

### Rate limit do GitHub
Configure um token GitHub:
```bash
export GITHUB_TOKEN=seu_token_aqui
```

## 📝 Exemplo de Uso Completo

```bash
# 1. Configurar ambiente
pip install -r requirements.txt
export GITHUB_TOKEN=seu_token_aqui

# 2. Executar análise completa
python3 run_complete_analysis.py --ck ../tools/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar --max-repos 100

# 3. Verificar resultados
ls -la results/
cat results/relatorio_final_lab02s02.md
```

## 🎯 Resultados Esperados

- **Dados brutos**: `results/complete_analysis.csv`
- **Visualizações**: `results/plots/`
- **Relatório final**: `results/relatorio_final_lab02s02.md`
- **Análise estatística**: Correlações de Pearson e Spearman
- **Testes de significância**: p < 0.05

## 📚 Referências

- [CK Metrics](https://github.com/mauricioaniche/ck)
- [GitHub API](https://docs.github.com/en/rest)
- [Pandas](https://pandas.pydata.org/)
- [Matplotlib](https://matplotlib.org/)
- [Seaborn](https://seaborn.pydata.org/)
- [SciPy](https://scipy.org/)
