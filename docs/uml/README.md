# Diagrama UML de casos de uso

O ficheiro [casos-de-uso.drawio](casos-de-uso.drawio) representa as funcionalidades previstas da aplicação **Open Science Datasets**, com base no [README do projeto](../../README.md) e nos [requisitos](../requisitos.md). O diagrama não indica que essas funcionalidades já estejam implementadas.

O ator **Utilizador**, fora da fronteira do sistema, está ligado por associações simples, sem setas, aos oito casos de uso dentro dessa fronteira:

| Caso de uso | Requisito |
|---|---|
| pesquisar datasets | RF01 |
| consultar metadados | RF02 |
| filtrar resultados | RF03 |
| selecionar datasets | RF04 |
| comparar datasets | RF05 |
| relacionar datasets | RF06 |
| preparar dados para IA | RF07 |
| exportar resultados | RF08 |

Esta primeira vista apresenta as interações do utilizador. As integrações previstas com OpenAIRE, Zenodo e re3data constituem o contexto dessas funcionalidades. Não são usadas relações `include` ou `extend`, pois esta vista não especifica dependências entre os casos de uso.

## Abrir e editar

1. Abrir [diagrams.net](https://app.diagrams.net/) e escolher **Device / Dispositivo**, se for solicitado um local de armazenamento.
2. Selecionar **File → Open From → Device** (ou a opção equivalente no idioma da interface).
3. Escolher `docs/uml/casos-de-uso.drawio` no repositório.
4. Após editar, guardar o ficheiro no mesmo caminho, mantendo a extensão `.drawio`.

Também é possível abrir o ficheiro na aplicação draw.io Desktop. O diagrama é guardado como XML não comprimido, para permitir a consulta das alterações no Git.
