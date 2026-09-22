# Arquitetura - TrainTime

## Visao Geral

```
Frontend (HTML/CSS/JS)
        ↓
    API (FastAPI)
        ↓
  Services (regras de negocio)
        ↓
  Banco de Dados (SQLite/SQLAlchemy)
```

## Backend

- `core/config.py` - configuracoes, env vars
- `core/security.py` - bcrypt, JWT
- `core/deps.py` - get_current_user, require_role
- `models/models.py` - entidades SQLAlchemy
- `schemas/` - validacao Pydantic v2
- `routes/` - endpoints da API
- `services/` - logica de negocio
- `database/connection.py` - engine, sessao

## Autenticacao

- Senhas: bcrypt
- JWT com SECRET_KEY via .env
- Roles: athlete, coach
- Autorizacao: dependencias FastAPI

## Equipes

```
Coach → Team → TeamAthlete → Athlete
```

- Treinador cria/edita/exclui equipes
- Atletas sao adicionados/removidos pelo treinador
- Validacao de esporte compativel no backend
- Autorizacao: coach so acessa suas equipes
- Atleta so visualiza equipes que participa

## Treinos

```
Coach → Team → Workout
```

- Treinador cria/edita/exclui treinos nas proprias equipes
- Atleta visualiza treinos das equipes que participa
- Treino pertence a uma equipe (nao diretamente a atletas)
- Autorizacao: coach proprietario ou atleta membro da equipe
- Filtros: team_id, status
- Ordenacao: scheduled_at ASC

## Principios

- Separacao de responsabilidades
- Servicos para logica de negocio
- Rotas para HTTP/validacao
- Pydantic para validacao de entrada
- Seguranca real no backend
