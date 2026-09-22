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

### PLANEJADO

| Entidade | Descricao |
|----------|-----------|
| WorkoutSession | Sessao de treino executada |
| PerformanceRecord | Registro de desempenho |
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

## Regras de Equipe

- Apenas treinador cria equipes
- Treinador so administra suas proprias equipes
- Atleta so entra em equipe do mesmo esporte
- Mesmo atleta nao pode ser adicionado duas vezes
- Atleta pode participar de multiplas equipes
- Excluir equipe remove vinculos TeamAthlete, nao usuarios
