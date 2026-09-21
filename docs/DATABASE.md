# Banco de Dados - TrainTime

## Entidades

### IMPLEMENTADO

| Entidade | Tabela | Descricao |
|----------|--------|-----------|
| User | users | Usuarios do sistema (id, name, email, password_hash, role, is_active, created_at, updated_at) |
| Sport | sports | Esportes cadastrados |
| Position | positions | Posicoes por esporte |
| SportAttribute | sport_attributes | Atributos avaliaveis por esporte |
| Athlete | athletes | Dados esportivos do atleta (user_id, sport_id, position_id) |
| Coach | coaches | Dados do treinador (user_id) |
| CoachSport | coach_sports | Relacao treinador-esporte |
| AthleteAttribute | athlete_attributes | Valores dos atributos do atleta (0-100) |
| Team | teams | Equipes |
| TeamAthlete | team_athletes | Relacao equipe-atleta |

### PLANEJADO

| Entidade | Descricao |
|----------|-----------|
| Workout | Treinos criados |
| Exercise | Exercicios |
| WorkoutExercise | Relacao treino-exercicio |
| WorkoutAssignment | Atribuicao de treino a atleta |
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
CoachSport (many) ──→ (1) Sport

Athlete (1) ──→ (many) AthleteAttribute
AthleteAttribute (many) ──→ (1) SportAttribute

Coach (1) ──→ (many) Team
Team  (1) ──→ (many) TeamAthlete
Athlete (1) ──→ (many) TeamAthlete

Athlete (many) ──→ (many) Team  (via TeamAthlete)
```

## Observacoes

- Um usuario e ou atleta ou treinador (role no User)
- Um treinador pode trabalhar com multiplos esportes
- Atributos esportivos sao validados pelo backend (0-100)
- Posicao deve pertencer ao esporte selecionado
- Senhas armazenadas com bcrypt (nunca em texto puro)
