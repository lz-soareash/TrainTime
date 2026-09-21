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

## Backend

- Python com FastAPI
- Arquitetura organizada em camadas:
  - `core/` - configuracoes
  - `models/` - entidades do banco
  - `schemas/` - validacao com Pydantic
  - `routes/` - endpoints da API
  - `services/` - logica de negocio
  - `database/` - conexao e sessao

## Banco de Dados

- SQLite para desenvolvimento
- SQLAlchemy ORM
- Migragem futura para PostgreSQL via alteracao de URL

## Principios

- Separacao de responsabilidades
- API retorna JSON consistente
- Validacao via Pydantic
- Frontend nao contem regras de negocio
- Estrutura preparada para novos esportes
- Independente de IA
