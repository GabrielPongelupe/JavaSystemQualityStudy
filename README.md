# Java System Quality Study - Lab02

Este repositório contém scripts e dados do **Laboratório 02**: um estudo das características de qualidade de sistemas Java usando **CK Metrics**.

---

## Estrutura do repositório

```
├── src/
│ ├── fetch_repos.py # Busca os top-1000 repositórios Java
│ ├── analyze_repo.py # Automatiza clone, CK, CSVs, resumo e cleanup
│ ├── utils.py # Funções auxiliares (atualmente vazio)
│ └── requirements.txt # Dependências Python
├── tools/
│ └── ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar
├── docs/
│ ├── results/ # CSVs de resultados e resumos
│ └── reports/ # Relatórios e observações
└── run_example.sh # Script de exemplo (opcional)
```


---

## Requisitos

- Python 3.8+  
- Java 8+  
- Git  
- Maven (se quiser gerar o JAR do CK você mesmo, opcional)  
- GitHub Personal Access Token (recomendado para evitar limites de API)

### Instalação de dependências Python

```bash
python3 -m venv .venv
source .venv/bin/activate       # Linux/Mac
# .venv\Scripts\activate       # Windows

pip install -r src/requirements.txt
```

# Passo 1 — Gerar lista dos 1000 repositórios Java

Crie um token no GitHub (Settings → Developer settings → Personal access tokens → classic → selecionar "public_repo") e exporte:

```
export GITHUB_TOKEN=SEU_TOKEN_AQUI
```

Rode o script:

```
python3 src/fetch_repos.py --token $GITHUB_TOKEN --out repositorios_java.csv --pages 10
```

Isso gera o arquivo repositorios_java.csv com os top 1000 repositórios Java mais estrelados.

# Passo 2 — Rodar análise em 1 repositório

Exemplo: spring-projects/spring-framework

```
python3 src/analyze_repo.py \
  --repo spring-projects/spring-framework \
  --ck tools/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar \
  --outdir docs/results
```

__O que acontece:__

* O script clona o repositório em um diretório temporário.

* Executa o CK Metrics no código Java.

* Copia class.csv para docs/results/metricas_raw_<repo>.csv.

* Gera um resumo estatístico em docs/results/metricas_summary_<repo>.csv.

* Remove o clone temporário para não ocupar espaço.