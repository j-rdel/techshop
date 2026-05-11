# Diretrizes Universais para Assistentes de IA no Projeto TechShop

## 1. Contexto do Projeto

- **Nome:** TechShop
- **Objetivo:** Plataforma de e-commerce com foco em performance e experiência do usuário.
- **Stack Principal:** Python, FastAPI, Pydantic.
- **Banco de Dados:** A ser definido (provavelmente PostgreSQL).
- **Estilo de Código:** PEP 8, com formatação via Black.

## 2. Regras Estritas para Geração de Código

Qualquer código gerado por um assistente de IA **deve** seguir as seguintes regras, sem exceção:

1.  **Sempre documentar funções:** Todas as funções, métodos e classes devem conter docstrings claras e concisas, explicando seu propósito, argumentos e o que retornam. O formato preferencial é o do Google Style Guide.

2.  **Priorizar Python tipado (mypy):** Todo o código deve incluir anotações de tipo. A verificação de tipos com `mypy` será parte do pipeline de CI/CD. O objetivo é ter um código mais robusto e de fácil manutenção.

3.  **Utilizar padrão AAA nos testes:** Ao criar testes unitários, a estrutura "Arrange, Act, Assert" (Organizar, Agir, Afirmar) é obrigatória. Isso garante que os testes sejam legíveis, consistentes e focados em um único comportamento.
