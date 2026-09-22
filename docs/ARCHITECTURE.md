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
- `database/migrations.py` - migracoes leves e idempotentes de schema

## Migracao de Schema

- `create_all` cria tabelas novas, mas NAO altera tabelas existentes
- `database/migrations.py::run_migrations` roda no startup (lifespan)
- Adiciona colunas que faltam em bancos criados antes da coluna existir no model
- Mapa `MISSING_COLUMN_FIXES` (ex.: `teams.created_at`); idempotente (checa `PRAGMA table_info`)

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

## Perfis e Atributos

- Atleta: `sport`, `position`, `attributes` (0-100)
- Trocar/limpar esporte do atleta limpa posicao e atributos e remove de times de esporte incompativel
- Posicao validada contra o esporte do atleta; `position_id` pode ser `null`
- Atualizacao de atributos tipada (Pydantic), duplicatas rejeitadas, lista vazia inadmitida
- Treinador: `sports` (esportes que treina); criar time/exercicio exige o esporte no perfil do treinador
- Exclusao de time remove treinos (Workout/WorkoutExercise) vinculados em cascata
- WorkoutExercise atualizado/excluido sempre validando o `workout_id` da URL

## Exercicios

```
Coach → Exercise (por esporte)
Workout → WorkoutExercise → Exercise
```

- Treinador cria exercicios vinculados ao seu esporte
- Exercicio tem tipo (repetitions, duration, distance, mixed)
- Exercicio e criado por um treinador (created_by)
- Treinador so edita/exclui seus proprios exercicios
- Exercicio so e excluido se nao estiver em nenhum treino (409)
- WorkoutExercise vincula exercicio ao treino com configuracao
- WorkoutExercise e PLANNING: order, sets, reps, duration, distance, rest, notes
- Validacao de esporte: exercise.sport_id == team.sport_id
- Mesmo exercicio pode aparecer varias vezes no mesmo treino
- Autorizacao: coach proprietario do treino ou atleta da equipe

## Principios

- Separacao de responsabilidades
- Servicos para logica de negocio
- Rotas para HTTP/validacao
- Pydantic para validacao de entrada
- Seguranca real no backend
