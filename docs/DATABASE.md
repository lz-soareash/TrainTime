# Banco de Dados - TrainTime

## Entidades

### IMPLEMENTADO

| Entidade | Tabela | Descricao |
|----------|--------|-----------|
| User | users | Usuarios do sistema (atletas e treinadores) |
| Sport | sports | Esportes cadastrados |
| Position | positions | Posicoes por esporte |
| SportAttribute | sport_attributes | Atributos avaliaveis por esporte |
| Athlete | athletes | Dados esportivos do atleta |
| Coach | coaches | Dados do treinador |
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

Coach (1) ──→ (many) Team
Team  (1) ──→ (many) TeamAthlete
Athlete (1) ──→ (many) TeamAthlete

Athlete (many) ──→ (many) Team  (via TeamAthlete)
```

## Observacoes

- Um usuario e ou atleta ou treinador (role no User)
- Um atleta pode participar de multiplas equipes
- Posicao e obrigatoria por esporte (nao e texto livre)
- Atributos sao especificos de cada esporte
