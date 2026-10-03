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

## Metas (Goals)

```
Coach → Goal → Athlete
Athlete → Goal (proprias)
```

- Treinador cria meta para qualquer atleta de uma de suas equipes
- Atleta cria meta apenas para si
- Metas sao sempre de um atributo (`attribute_id`) com `target_value`
- `current_value` e alterado explicitamente; nao ha leitura automatica do atributo
- Conclusao automatica quando `current_value >= target_value`
- Cancelamento mantem o registro com status `cancelled`
- `progress_percentage` e `athlete_name` sao computados na resposta

Detalhes em [GOALS.md](GOALS.md).

## Execucao de Treinos

```
Workout → WorkoutExecution → Athlete
Workout → WorkoutExercise → WorkoutExerciseExecution (resultado)
```

- WorkoutExercise e PLANNING (o planejado); WorkoutExerciseExecution e o REALIZADO
- O resultado e criado sob demanda no POST do exercicio, nao no inicio da execucao
- Chave logica do resultado: `(execution_id, workout_exercise_id)`, com upsert
- Uma execucao `in_progress` por atleta e por treino
- Concluir gera `finished_at` e dispara a geracao automatica de performance
- Autorizacao: dono da execucao ou treinador da equipe do treino

Detalhes em [EXECUTIONS.md](EXECUTIONS.md).

## Desempenho (Performance)

```
Athlete → PerformanceRecord → WorkoutExecution (opcional)
```

- Registros manuais (metric, value, notes) e automaticos (metrica `volume`)
- `execution_id` e anulavel: um registro pode nao vir de execucao
- `GET /performance` e agregado: atleta ve o proprio, treinador ve os atletas
  das suas equipes (filtro por `team_athletes` + `teams.coach_id`)
- Ambos ordenam por `recorded_at` decrescente

Detalhes em [PERFORMANCE.md](PERFORMANCE.md).

## Principios

- Separacao de responsabilidades
- Servicos para logica de negocio
- Rotas para HTTP/validacao
- Pydantic para validacao de entrada
- Seguranca real no backend
- Testes de integracao contra a API real, nao apenas testes de unidade
