# Requisitos do projeto

## 1. Objetivo

Desenvolver uma aplicação web para descobrir recursos do tipo dataset em repositórios de ciência aberta, utilizando APIs do ecossistema EOSC/OpenAIRE, nomeadamente o OpenAIRE Graph, e serviços de identificação e acesso a repositórios, como o re3data e o Zenodo.

A aplicação deve permitir navegar nos metadados, filtrar, selecionar, comparar e relacionar datasets, bem como preparar dados para o treino de modelos de inteligência artificial (IA), de acordo com as necessidades do utilizador. Deve apoiar normas existentes para a descrição, o tratamento e a anotação de datasets destinados a IA.

## 2. Utilizador e âmbito inicial

O utilizador principal é uma pessoa que procura datasets científicos e pretende avaliar a sua adequação e preparar dados para uma tarefa de IA.

Os requisitos RF01 a RF08 mantêm as funcionalidades da proposta inicial. A preparação de ficheiros CSV pequenos é uma opção de âmbito dessa proposta, não uma limitação imposta pelo enunciado. O limite de tamanho deve ser definido e apresentado ao utilizador.

Não se assume a necessidade de contas de utilizador, de treinar modelos de IA na aplicação ou de alterar os datasets nos repositórios de origem.

## 3. Requisitos funcionais

| Código | Requisito |
|---|---|
| RF01 | Permitir pesquisar recursos do tipo dataset por palavras-chave através das fontes integradas, apresentando uma lista de resultados e indicando quando não existem correspondências. |
| RF02 | Permitir consultar os metadados de um dataset, incluindo, quando disponíveis, título, descrição, autores, identificador persistente, datas, palavras-chave, licença, formatos e repositório de origem. |
| RF03 | Permitir filtrar os resultados pelos campos disponibilizados pelas fontes integradas, como repositório, área científica, data, licença e formato, e remover os filtros aplicados. |
| RF04 | Permitir adicionar e remover datasets de uma seleção de trabalho e recuperar essa seleção após atualizar a página. |
| RF05 | Permitir comparar pelo menos dois datasets selecionados, apresentando os mesmos campos de metadados lado a lado e assinalando informação em falta. |
| RF06 | Permitir registar, consultar, editar e remover relações entre datasets selecionados, indicando o tipo de relação e uma descrição opcional; distinguir as relações introduzidas pelo utilizador das obtidas nas fontes. |
| RF07 | Permitir preparar um CSV dentro do limite de tamanho suportado: pré-visualizar os dados, selecionar colunas, identificar valores em falta e duplicados e aplicar operações de tratamento escolhidas pelo utilizador. |
| RF08 | Permitir exportar os dados preparados e a respetiva descrição, incluindo as fontes, as transformações aplicadas e as anotações produzidas. |
| RF09 | Consultar a API do OpenAIRE Graph para descobrir datasets e obter os respetivos metadados. |
| RF10 | Permitir identificar repositórios através do re3data e aceder a datasets e metadados de pelo menos um repositório integrado por API, como o Zenodo. |
| RF11 | Permitir navegar a partir dos metadados de um dataset para os recursos associados disponibilizados pela fonte, como autores, publicações, projetos, repositórios ou outros datasets, através de vistas internas ou ligações externas. |
| RF12 | Apresentar a ligação para o registo original do dataset e permitir obter os ficheiros acessíveis ou abrir a página de acesso, indicando eventuais restrições disponibilizadas pela fonte. |
| RF13 | Permitir carregar um ficheiro CSV local ou utilizar um CSV obtido de um dataset selecionado para iniciar a preparação, validando o formato e o limite de tamanho e comunicando os erros encontrados. |
| RF14 | Permitir descrever a finalidade de IA pretendida e anotar as colunas do dataset, incluindo significado, tipo de dados e papel na tarefa, como variável de entrada ou variável alvo, quando aplicável. |
| RF15 | Apoiar uma ou mais normas existentes para a descrição, o tratamento e a anotação de datasets para IA, usando os seus campos e regras aplicáveis e validando a descrição exportada. A norma, a versão e o nível de suporte devem ser identificados na documentação. |
| RF16 | Manter um registo das operações de preparação e permitir consultar uma pré-visualização do resultado antes da exportação, preservando o ficheiro original. |

## 4. Requisitos não funcionais

| Código | Requisito |
|---|---|
| RNF01 | A interface deve apresentar de forma consistente os estados de carregamento, ausência de resultados, sucesso e erro nas operações de pesquisa, consulta, preparação e exportação. |
| RNF02 | A aplicação deve tratar indisponibilidade, erros e limites de utilização das APIs, apresentando uma mensagem compreensível e permitindo repetir a operação. |
| RNF03 | Os metadados de fontes diferentes devem ser apresentados através de campos comuns, conservando a identificação da fonte e distinguindo valores ausentes de valores efetivamente fornecidos. |
| RNF04 | A aplicação deve validar os ficheiros carregados e tratar o seu conteúdo como dados, sem executar código neles contido. |
| RNF05 | As credenciais e chaves de API, quando necessárias, devem ser configuradas fora do código-fonte e excluídas do repositório GitHub. |
| RNF06 | Os dados exportados devem manter a identificação da origem e a informação de licença disponível; a aplicação deve assinalar quando essa informação não existe. |
| RNF07 | A aplicação deve apresentar resultados de pesquisa por páginas ou por carregamento incremental, evitando carregar todos os registos de uma só vez. |
| RNF08 | As integrações com APIs, as operações de preparação de dados e a interface devem estar organizadas em componentes separados, permitindo manutenção e substituição das fontes. |

## 5. Requisitos de documentação e entrega

| Código | Requisito |
|---|---|
| RD01 | Disponibilizar no GitHub todos os artefactos produzidos no projeto, incluindo código-fonte, requisitos, modelos, testes, exemplos e documentação, respeitando as licenças e excluindo credenciais e dados pessoais. |
| RD02 | Documentar o projeto com notações de engenharia de software e processos, por exemplo, diagramas UML de casos de uso e componentes e um processo BPMN de descoberta e preparação de datasets. |
| RD03 | Incluir no README instruções de instalação, configuração e execução, dependências, APIs utilizadas, limitações e exemplos de utilização. |
| RD04 | Documentar as normas adotadas, as respetivas versões, os campos suportados e a correspondência entre os metadados das fontes e a descrição exportada. |
| RD05 | Documentar a validação dos requisitos, relacionando os seus códigos com os testes ou cenários de demonstração e os resultados obtidos. |

## 6. Decisões a fechar na implementação

- Selecionar as APIs e os mecanismos de acesso efetivamente utilizados para o re3data e para o repositório integrado, verificando os campos e filtros disponíveis.
- Escolher e documentar as normas existentes a suportar, incluindo o formato da descrição exportada. Um formato próprio, por si só, não satisfaz o RF15.
- Definir o tamanho máximo do CSV e as operações de tratamento suportadas, incluindo o comportamento perante valores em falta e duplicados.
- Definir onde são guardadas a seleção, as relações e as anotações, bem como a duração da sua conservação.

Estas decisões completam os detalhes técnicos dos requisitos; não substituem as funcionalidades pedidas no enunciado.
