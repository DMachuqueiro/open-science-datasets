# open-science-datasets

Aplicação web para descoberta, comparação e preparação de datasets científicos para IA, com integrações previstas com OpenAIRE, Zenodo e re3data.

## Estado atual

Esta primeira etapa contém uma aplicação Python com Flask, uma página HTML renderizada no servidor e um formulário de pesquisa. O formulário recebe e apresenta o termo introduzido, mas ainda não pesquisa datasets nem contacta APIs. As restantes funcionalidades descritas nos requisitos estão previstas para etapas futuras.

## Instalar e executar

É necessário Python 3.9 ou superior e acesso à Internet para instalar as dependências. Executar os comandos na pasta raiz do repositório.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app run
```

Os comandos usam diretamente o Python do ambiente virtual, sem ser necessário ativá-lo ou alterar a política de execução do PowerShell.

### Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m flask --app app run
```

Com o servidor a correr, abrir **http://127.0.0.1:5000/** no navegador. Introduzir palavras-chave e carregar em **Pesquisar** para confirmar a receção do termo. Nesta etapa, não são apresentados resultados de datasets.

Para parar o servidor, usar **Ctrl+C** no terminal. Este comando inicia o servidor local de desenvolvimento do Flask.

Não são necessárias chaves de API nem um ficheiro `.env` nesta etapa. Os ambientes virtuais, os ficheiros `.env` e as caches de Python estão excluídos pelo `.gitignore`.

## Estrutura

```text
open-science-datasets/
├── app.py                 # Aplicação Flask e rota da página inicial
├── templates/
│   └── index.html         # Página renderizada no servidor
├── static/
│   └── style.css          # Estilos da página
├── docs/
│   ├── requisitos.md
│   └── uml/               # Diagrama e documentação dos casos de uso
├── requirements.txt
├── .gitignore
└── README.md
```

## Documentação

- [Requisitos do projeto](docs/requisitos.md)
- [Diagrama UML de casos de uso e instruções de abertura](docs/uml/README.md)
- [Documentação oficial do Flask](https://flask.palletsprojects.com/en/stable/quickstart/)
