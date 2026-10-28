# open-science-datasets

Aplicação web para descoberta, comparação e preparação de datasets científicos para IA, com integrações previstas com OpenAIRE, Zenodo e re3data.

## Estado atual

A aplicação Flask pesquisa datasets reais no Zenodo, com até 20 resultados por página e navegação **Anterior / Seguinte**. Cada título abre um pop-up com os metadados disponíveis, descrição completa, autores, licença, acesso, ficheiros e recursos associados, sem sair da pesquisa. A ligação ao registo original aparece apenas nos detalhes, com o texto **Link** e contexto adicional para leitores de ecrã. As restantes funcionalidades descritas nos requisitos estão previstas para etapas futuras.

## Instalar e executar

É necessário Python 3.9 ou superior e acesso à Internet para instalar as dependências e consultar o Zenodo. Executar os comandos na pasta raiz do repositório. A integração utiliza `requests`, incluído em `requirements.txt`; se já existir um ambiente virtual, repetir a instalação das dependências.

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

Com o servidor a correr, abrir **http://127.0.0.1:5000/** no navegador. Introduzir palavras-chave, por exemplo `climate`, e carregar em **Pesquisar**. Usar **Seguinte** e **Anterior** para navegar em blocos de 20. Abrir um título para consultar os detalhes no pop-up; aí, **Link** permite visitar o registo original no Zenodo. Usar **Fechar** ou **Esc** para regressar à pesquisa, conservando a página e a posição.

Para parar o servidor, usar **Ctrl+C** no terminal. Este comando inicia o servidor local de desenvolvimento do Flask.

Não são necessárias chaves de API nem um ficheiro `.env` para esta pesquisa pública. Os ambientes virtuais, os ficheiros `.env` e as caches de Python estão excluídos pelo `.gitignore`.

## Integração Zenodo

Documentação oficial consultada em 28 de outubro de 2026:

- [REST API — Records / List e Retrieve](https://developers.zenodo.org/#records): pesquisa, filtro por tipo, paginação, formatos e consulta de um registo pelo identificador.
- [REST API — HTTP status codes](https://developers.zenodo.org/#http-status-codes): falhas HTTP, incluindo limites de utilização e indisponibilidade.
- [REST API — Deposit metadata](https://developers.zenodo.org/#deposit-metadata): a descrição pode conter HTML, que é convertido em texto antes da apresentação.

O servidor envia `GET https://zenodo.org/api/records/` com `q` igual ao termo introduzido, `type=dataset`, `size=20` e `page`, usando `Accept: application/json`. Cada navegação consulta apenas a página pedida. A biblioteca HTTP codifica os parâmetros. A página atual e o termo são conservados nos controlos de navegação e na ligação de regresso do detalhe.

A navegação usa as ligações `links.prev` e `links.next` devolvidas pela API, convertidas em destinos locais. Se essas informações não existirem, um total exato permite determinar as páginas adjacentes. Totais ausentes não são inventados e totais com `relation=gte` são apresentados como limites inferiores. As ligações da API têm precedência sobre o total, respeitando os limites de navegação disponibilizados pela fonte. Parâmetros `page` não inteiros ou inferiores a 1 passam a 1. Uma página vazia posterior à primeira apresenta uma mensagem própria e uma ligação para reiniciar a pesquisa. Pedidos que o Zenodo rejeite, incluindo páginas fora dos seus limites, apresentam uma mensagem de falha da API.

O detalhe tem o endereço `/datasets/zenodo/<identificador>` e consulta `GET https://zenodo.org/api/records/<identificador>`, mesmo quando aberto diretamente. Um registo inexistente apresenta HTTP 404, um timeout HTTP 504 e uma falha da API HTTP 502. Registos explicitamente identificados pela fonte como outro tipo de recurso não são apresentados como datasets.

Na pesquisa, `static/detail.js` abre um diálogo nativo e pede ao Flask apenas o conteúdo do detalhe. A consulta ao Zenodo continua a acontecer no servidor. O pop-up apresenta carregamento e erros, cancela pedidos pendentes ao fechar e devolve o foco ao título de origem. O conteúdo é partilhado com a página direta através de `_detail_content.html`. Sem JavaScript ou suporte ao diálogo, o título continua a abrir a página de detalhe.

O timeout é de 10 segundos para ligação e leitura, não um prazo global da operação. As descrições e condições de acesso são convertidas em texto; o resumo da pesquisa tem até 300 caracteres, enquanto o detalhe conserva a descrição completa. Os templates mantêm o escape automático do Jinja e nunca aplicam `safe` ao HTML recebido. Não há resultados locais de substituição em caso de falha.

### Representação dos metadados

`models.py` define o modelo comum; `metadata.py` faz a correspondência do Zenodo sem realizar pedidos; `zenodo.py` trata o acesso HTTP e a paginação. `None` representa informação ausente, nula ou de tipo inesperado. Textos e listas explicitamente vazios são conservados; a página de detalhe distingue essas situações. Entradas inválidas dentro de listas são ignoradas.

| Campo comum | Origem no registo Zenodo |
|---|---|
| Fonte e identificador | Fonte da integração (`Zenodo`) e `id` |
| Título e descrição | `metadata.title`, `metadata.description` |
| Autores | `metadata.creators`: nome, afiliação e ORCID |
| DOI e destino | `metadata.doi` ou `doi`; `doi_url` ou `links.doi` |
| Publicação e atualização | `metadata.publication_date`; `updated` ou `modified` |
| Palavras-chave | `metadata.keywords` |
| Licença | `metadata.license`: identificador, título e URL, quando fornecidos |
| Ficheiros | `files`: nome, formato (`mimetype` ou `type`), tamanho e ligação |
| Acesso | `metadata.access_right`, `access_conditions`, `embargo_date` |
| Recursos associados | `metadata.related_identifiers`: identificador, relação, tipo e URL explícito |

O formato de um ficheiro não é deduzido da extensão: é assinalado como ausente quando a API não o fornece. Relações, autores e identificadores sem URL explícito são apresentados em texto; não são criadas ligações a partir de nomes ou de identificadores DOI/ORCID isolados. São aceites apenas destinos HTTP(S) válidos, sem credenciais. A ligação original pode ser reconstruída a partir do identificador numérico do registo. Os ficheiros são abertos na fonte, sem download pelo servidor Flask.

Este modelo facilita uma integração futura com outras fontes, mas não representa suporte a uma norma de anotação para IA. OpenAIRE Graph, seleção, comparação, gestão de relações e preparação de dados continuam fora desta etapa.

## Verificar

Os testes automáticos usam `unittest` e respostas simuladas exclusivamente nos testes, sem contactar a API nem exigir dependências adicionais:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Em Linux/macOS, usar `.venv/bin/python -m unittest discover -s tests -v`.

Os testes verificam pesquisa, tipo, tamanho e página enviados à API; limite de 20 resultados; navegação sem obter todas as páginas; preservação do contexto; totais exatos, desconhecidos e inferiores; detalhe direto; campos ausentes e vazios; descrições completas e seguras; ligações; registo inexistente; timeout; erros HTTP e respostas inválidas. Estes cenários cobrem a pesquisa e paginação (RF01/RNF07), a consulta dos metadados (RF02), ligações a recursos associados (parte de RF11) e acesso à fonte e ficheiros (parte de RF12).

Para verificar no navegador:

1. Pesquisar `climate`; confirmar até 20 resultados, sem ligação externa ao Zenodo na lista.
2. Carregar em **Seguinte** e confirmar página 2 com o mesmo termo; usar **Anterior** para regressar.
3. Na página 2, abrir um título. Confirmar que aparece um pop-up com descrição completa, autores, datas, licença, acesso, ficheiros, recursos associados e **Link**, conforme existam na fonte. Fechar pelo botão ou por **Esc**: a pesquisa deve manter termo, página e posição, com o foco no título.
4. Abrir o título num novo separador, ou copiar o seu endereço, e remover `?q=...&page=...`: o detalhe continua acessível diretamente, com ligação de regresso à pesquisa.
5. Pesquisar `zzzxqv987654321inexistente` para testar ausência de correspondências; abrir `/?q=climate&page=abc` para confirmar a normalização para a página 1.
6. Abrir `/?q=%20%20` e confirmar a indicação para introduzir palavras-chave, sem pedido ao Zenodo.
7. Confirmar que descrições aparecem como texto. Os cenários de registo inexistente, páginas vazias, timeout e falhas da API são reproduzidos pelos testes automáticos.

A pesquisa real depende da disponibilidade e dos limites de utilização do Zenodo e do acesso à rede do servidor Flask. Os testes isolados não comprovam, por si só, o acesso à API real.

Na consulta real de 28 de outubro de 2026, as páginas 1 e 2 de `climate` devolveram HTTP 200 e 20 datasets cada, com total e ligações de navegação. A consulta individual de um desses registos também devolveu HTTP 200, confirmando os campos usados na normalização. O contrato observado é um objeto de pesquisa com `hits.hits`, `hits.total` e `links`; estes detalhes foram confirmados nas respostas reais, complementando a documentação oficial.

Os 42 testes isolados passaram, incluindo o conteúdo parcial do pop-up e a ausência da ligação externa na pesquisa. Foram também verificados pedidos HTTP ao servidor Flask local com a API real: duas páginas distintas de 20 resultados, detalhe aberto a partir da página 2 com regresso preservado, detalhe direto, página sem resultados e registo inexistente com HTTP 404. O comportamento do pop-up foi verificado adicionalmente no Edge em modo headless, com dados simulados apenas nessa verificação: abertura, conteúdo seguro, foco, fecho, erros de API/rede, cancelamento, reabertura e conservação do endereço da pesquisa.

## Estrutura

```text
open-science-datasets/
├── app.py                 # Rotas de pesquisa e detalhe
├── zenodo.py              # Pedidos à API e paginação
├── models.py              # Representação comum dos metadados
├── metadata.py            # Normalização do Zenodo e conversão para texto
├── templates/
│   ├── index.html         # Pesquisa e navegação entre páginas
│   ├── detail.html        # Consulta direta dos metadados
│   └── _detail_content.html # Conteúdo comum à página e ao pop-up
├── static/
│   ├── style.css          # Estilos da página e do pop-up
│   └── detail.js          # Abertura, carregamento e fecho do pop-up
├── docs/
│   ├── requisitos.md
│   └── uml/               # Diagrama e documentação dos casos de uso
├── requirements.txt
├── tests/
│   ├── test_search.py      # Pesquisa e paginação
│   └── test_detail.py      # Detalhe e normalização
├── .gitignore
└── README.md
```

## Documentação

- [Requisitos do projeto](docs/requisitos.md)
- [Diagrama UML de casos de uso e instruções de abertura](docs/uml/README.md)
- [Documentação oficial do Flask](https://flask.palletsprojects.com/en/stable/quickstart/)
