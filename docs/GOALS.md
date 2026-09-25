# Metas (Goals) - Fase 8

Sistema de metas por atleta com acompanhamento de progresso. Metas `active`,
`completed` ou `cancelled`, com conclusao automatica quando `current_value >=
target_value`.

## Fluxo de permissao

- **Atleta:** cria metas para si mesmo (`athlete_id` e ignorado e resolve para o
  proprio perfil). Lista somente as proprias metas.
- **Treinador:** cria metas para atletas das suas equipes (`athlete_id`
  obrigatorio e validado contra as equipes do treinador). Lista metas de todos
  os atletas das suas equipes. Atualiza progresso dessas metas.
- **Regra de atualizacao:** so o treinador que criou a meta (ou o proprio
  atleta dono) pode atualizar/cancelar. Treinador nao pode alterar metas de
  outros treinadores.

## Endpoints

| Metodo | Rota            | Permissao                                   |
|--------|-----------------|---------------------------------------------|
| POST   | `/goals`        | atleta (para si) ou treinador (para atleta) |
| GET    | `/goals`        | atleta (proprias) ou treinador (equipes)    |
| GET    | `/goals/{id}`   | proprietario (dono ou treinador que criou)  |
| PUT    | `/goals/{id}`   | dono ou treinador que criou                 |
| DELETE | `/goals/{id}`   | dono ou treinador que criou (cancela)       |

## Filtros (GET /goals)

- `status`: `active`, `completed`, `cancelled` (opcional)
- `athlete_id`: treinador filtra por um atleta (opcional)

## Computados na resposta

- `progress_percentage`: `min(100, floor(current_value / target_value * 100))`,
  limitado entre 0 e 100.
- `athlete_name`: nome do atleta (via `Goal.athlete.user.name`), carregado com
  `joinedload` para o frontend exibir no card.

## Validacoes

- `target_value > 0` (obrigatorio)
- `current_value >= 0` e nao pode ultrapassar o alvo sem concluir
- `status` somente em `{active, completed, cancelled}`
- Treinador nao pode ignorar o proprio perfil: atleta da meta deve pertencer a
  uma equipe do treinador, caso contrario `403`.

## Frontend

- Pagina `page-goals` dentro do container do app (nao dentro do header).
- Menu do usuario: item "Metas" abre via `openGoalsPage()`.
- Cards com titulo, atleta (para treinador), metrica, valores
  atual/alvo+unidade, prazo, barra de progresso colorida.
- Filtros por status no topo da pagina.
- Coach: select de atleta populado a partir das equipes via
  `/teams/{id}/athletes`.
- Formulario de criacao com selecao de atleta (treinador) ou sem (atleta).
- Atualizacao de progresso e cancelamento via botoes nos cards.
