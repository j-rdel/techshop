# TechShop

Uma API de e-commerce desenvolvida com FastAPI para gerenciar produtos e carrinhos de compra.

## Descrição

Este projeto implementa a base para uma plataforma de e-commerce chamada TechShop. Ele inclui a estrutura inicial do projeto, modelos de dados com Pydantic, e a lógica de negócio para um carrinho de compras.

A aplicação é construída utilizando FastAPI, garantindo alta performance e uma documentação de API interativa (via Swagger UI).

## Estrutura do Projeto

-   `src/`: Contém todo o código-fonte da aplicação.
    -   `main.py`: Ponto de entrada da API FastAPI.
    -   `models.py`: Definições dos modelos de dados (Product, CartItem) com Pydantic.
    -   `cart.py`: Lógica de negócio para o carrinho de compras (`ShoppingCart`).
-   `docs/`: Contém a documentação de planejamento do projeto.
    -   `PRD.md`: Documento de Requisitos do Produto.
    -   `BACKLOG.md`: User Stories.
    -   `DIAGRAMAS.md`: Diagrama Entidade-Relacionamento.
    -   `DIRETRIZES_IA.md`: Diretrizes para desenvolvimento com IA.

## Dependências

O projeto utiliza as seguintes bibliotecas:

-   `fastapi`: Framework web para a construção da API.
-   `pydantic`: Para validação e modelagem de dados.
-   `uvicorn`: Servidor ASGI para rodar a aplicação FastAPI.

As dependências de desenvolvimento incluem `mypy`, `pytest`, `ruff`, entre outras, e estão listadas no arquivo `pyproject.toml`.

## Instalação e Uso com `uv`

Este projeto utiliza `uv` como gerenciador de pacotes e ambiente virtual, por ser extremamente rápido.

### Pré-requisitos

Certifique-se de que você tem o `uv` instalado. Se não tiver, você pode instalá-lo com:

```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Passos para Instalação

1.  **Clone o repositório:**
    ```bash
    git clone <url-do-repositorio>
    cd techshop
    ```

2.  **Crie o ambiente virtual e instale as dependências:**
    O `uv` pode criar o ambiente e instalar as dependências de uma só vez.

    ```bash
    uv sync
    ```
    Este comando irá ler o `pyproject.toml`, criar um ambiente virtual `.venv` no diretório atual e instalar todas as dependências necessárias.

### Executando a Aplicação

1.  **Ative o ambiente virtual:**
    ```bash
    # Windows
    .venv\Scripts\activate

    # macOS / Linux
    source .venv/bin/activate
    ```

2.  **Inicie o servidor:**
    A aplicação principal está em `src/main.py`. Para executá-la, use o `uvicorn`:

    ```bash
    uvicorn src.main:app --reload
    ```
    -   `src.main:app`: Aponta para a instância `app` do FastAPI no arquivo `src/main.py`.
    -   `--reload`: Faz com que o servidor reinicie automaticamente após alterações no código.

3.  **Acesse a API:**
    A API estará disponível em `http://127.0.0.1:8000`.
    A documentação interativa (Swagger UI) pode ser acessada em `http://127.0.0.1:8000/docs`.
