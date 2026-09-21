# Arquitetura - TrainTime

## Visao Geral

O TrainTime segue uma arquitetura em camadas com separacao clara de responsabilidades.

```
Frontend (HTML/CSS/JS)
        ↓
    API (FastAPI)
        ↓
  Regras de Negocio
        ↓
  Banco de Dados (SQLite/SQLAlchemy)
```

## Frontend

- HTML, CSS, JavaScript puro (sem frameworks)
- Design mobile-first
- Consome a API via fetch
- Servido pelo FastAPI em producao
- Gerenciamento de token JWT via localStorage

## Backend

- Python com FastAPI
- Arquitetura organizada em camadas:
  - `core/` - configuracoes, seguranca (hashing, JWT), dependencias (autenticacao, autorizacao)
  - `models/` - entidades do banco (SQLAlchemy ORM)
  - `schemas/` - validacao com Pydantic v2
  - `routes/` - endpoints da API
  - `services/` - logica de negocio (seed)
  - `database/` - conexao e sessao

## Autenticacao

- Senhas armazenadas com bcrypt (nunca em texto puro)
- JWT para autenticacao de sessao
- Secret key via variavel de ambiente (.env)
- Tokens validados em cada requisicao autenticada
- Controle de roles: athlete, coach

## Autorizacao

- `get_current_user()` - valida token e retorna usuario
- `require_role("athlete")` - exige role especifica
- Rotas protegidas verificam token no backend (nao confia no frontend)

## Banco de Dados

- SQLite para desenvolvimento
- SQLAlchemy ORM
- Estrutura preparada para migracao para PostgreSQL via alteracao de URL

## Principios

- Separacao de responsabilidades
- API retorna JSON consistente
- Validacao via Pydantic
- Frontend nao contem regras de negocio
- Seguranca real no backend
- Independente de IA
