# Banco de Dados - TrainTime

## Entidades

### IMPLEMENTADO

| Entidade | Tabela | Descricao |
|----------|--------|-----------|
| User | users | Usuarios (id, name, email, password_hash, role, is_active, created_at, updated_at) |
| Sport | sports | Esportes cadastrados |
| Position | positions | Posicoes por esporte |
| SportAttribute | sport_attributes | Atributos avaliaveis por esporte |
| Athlete | athletes | Dados esportivos do atleta |
| Coach | coaches | Dados do treinador |
| CoachSport | coach_sports | Relacao treinador-esporte |
| AthleteAttribute | athlete_attributes | Valores dos atributos (0-100) |
| Team | teams | Equipes (id, name, sport_id, coach_id, created_at) |
| TeamAthlete | team_athletes | Relacao equipe-atleta (team_id, athlete_id, joined_at) |
| Workout | workouts | Treinos (id, team_id, title, description, scheduled_at, duration_minutes, status, created_at, updated_at) |
| Exercise | exercises | Exercicios (id, name, description, sport_id, exercise_type, created_by, created_at, updated_at) |
| WorkoutExercise | workout_exercises | Vinculo treino-exercicio (id, workout_id, exercise_id, order, sets, repetitions, duration_seconds, distance_meters, rest_seconds, notes, created_at, updated_at) |
| WorkoutExecution | workout_executions | Execucao de um treino por um atleta (id, workout_id, athlete_id, started_at, finished_at, status, notes, created_at, updated_at) |
| WorkoutExerciseExecution | workout_exercise_executions | Resultado realizado por exercicio (id, execution_id, workout_exercise_id, status, actual_sets, actual_repetitions, actual_duration_seconds, actual_distance_meters, actual_weight_kg, notes, completed_at, created_at, updated_at) |
| PerformanceRecord | performance_records | Registro de desempenho (id, athlete_id, execution_id anulavel, metric, value, recorded_at, notes, created_at) |
| Goal | goals | Meta de atributo (id, athlete_id, attribute_id, title, target_value, current_value, status, due_date, created_at, updated_at) |

### PLANEJADO

| Entidade | Descricao |
|----------|-----------|
| AthleteEvaluation | Avaliacao do treinador |
| TeamFormation | Escalacao |
| Match | Partidas |
| MatchStatistic | Estatisticas da partida |

## Relacionamentos

```
User (1) ──→ (1) Athlete
User (1) ──→ (1) Coach

Sport (1) ──→ (many) Position
Sport (1) ──→ (many) SportAttribute
Sport (1) ──→ (many) Exercise

Coach (1) ──→ (many) CoachSport
Coach (1) ──→ (many) Team
Coach (1) ──→ (many) Exercise (created_by)

Team (1) ──→ (many) TeamAthlete
Athlete (1) ──→ (many) TeamAthlete
Athlete (many) ──→ (many) Team (via TeamAthlete)

Team (1) ──→ (many) Workout
Workout (1) ──→ (many) WorkoutExercise
Exercise (1) ──→ (many) WorkoutExercise

Athlete (1) ──→ (many) AthleteAttribute
AthleteAttribute (many) ──→ (1) SportAttribute

Workout (1) ──→ (many) WorkoutExecution
Athlete (1) ──→ (many) WorkoutExecution
WorkoutExecution (1) ──→ (many) WorkoutExerciseExecution
WorkoutExercise (1) ──→ (many) WorkoutExerciseExecution

Athlete (1) ──→ (many) PerformanceRecord
WorkoutExecution (1) ──→ (many) PerformanceRecord (execution_id anulavel)

Athlete (1) ──→ (many) Goal
SportAttribute (1) ──→ (many) Goal
```

## Regras de Treino

- Apenas treinador cria treinos
- Treinador so administra treinos de suas proprias equipes
- Atleta visualiza treinos das equipes que participa
- Treino pertence a uma equipe (nao diretamente a atletas)
- Status: scheduled, completed, cancelled
- Excluir treino nao afeta equipe, atletas ou outros treinos

## Regras de Exercicio

- Apenas treinador cria exercicios
- Exercicio vinculado a um esporte
- Treinador so edita/exclui seus proprios exercicios (created_by)
- Exercicio so e excluido se nao estiver em nenhum WorkoutExercise (409)
- Tipos: repetitions, duration, distance, mixed
- Todos autenticados podem listar/visualizar exercicios

## Regras de Exercicio no Treino

- Apenas treinador proprietario do treino adiciona/edita/remove exercicios
- Validacao: exercise.sport_id == team.sport_id
- Mesmo exercicio pode aparecer varias vezes (sem UNIQUE constraint)
- Configuracao: order, sets, repetitions, duration_seconds, distance_meters, rest_seconds, notes
- WorkoutExercise e PLANNING (valores planejados, nao executados)
- Atleta da equipe pode listar exercicios do treino (somente leitura)
- Atleta NAO pode adicionar/editar/remover exercicios

## Regras de Execucao

- Apenas atleta inicia, atualiza e conclui a propria execucao
- Atleta so executa treinos de equipes que participa
- Uma execucao `in_progress` por atleta e por treino
- Resultado e criado sob demanda ao salvar o exercicio (nao no inicio)
- Chave logica do resultado: `(execution_id, workout_exercise_id)` com upsert
- Status do resultado: pending, done, skipped
- `completed_at` e preenchido ao virar `done` e zerado ao sair de `done`
- Concluir a execucao dispara a geracao automatica de `PerformanceRecord`

## Regras de Desempenho

- Apenas atleta registra desempenho, e sempre para si mesmo
- `execution_id` e opcional: registros manuais podem nao vir de execucao
- Metrica `volume` e gerada automaticamente ao concluir uma execucao
- Atleta ve apenas os proprios registros
- Treinador ve apenas registros de atletas de pelo menos uma de suas equipes
- Registrar desempenho de outro atleta exige ser treinador da equipe dele

## Regras de Meta

- Treinador cria meta para atletas de suas equipes
- Atleta cria meta apenas para si
- Meta referencia um SportAttribute com `target_value`
- `current_value` so muda por update explicito
- Conclusao automatica quando `current_value >= target_value`
- Cancelamento mantem o registro com status `cancelled`

## Regras de Equipe

- Apenas treinador cria equipes
- Treinador so administra suas proprias equipes
- Atleta so entra em equipe do mesmo esporte
- Mesmo atleta nao pode ser adicionado duas vezes
- Atleta pode participar de multiplas equipes
- Excluir equipe remove vinculos TeamAthlete, nao usuarios
