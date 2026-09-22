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

### PLANEJADO

| Entidade | Descricao |
|----------|-----------|
| Exercise | Exercicios dentro dos treinos |
| WorkoutExercise | Relacao treino-exercicio |
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

Coach (1) ──→ (many) CoachSport
Coach (1) ──→ (many) Team

Team (1) ──→ (many) TeamAthlete
Athlete (1) ──→ (many) TeamAthlete
Athlete (many) ──→ (many) Team (via TeamAthlete)

Team (1) ──→ (many) Workout

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

## Regras de Equipe

- Apenas treinador cria equipes
- Treinador so administra suas proprias equipes
- Atleta so entra em equipe do mesmo esporte
- Mesmo atleta nao pode ser adicionado duas vezes
- Atleta pode participar de multiplas equipes
- Excluir equipe remove vinculos TeamAthlete, nao usuarios
