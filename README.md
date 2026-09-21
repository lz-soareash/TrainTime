# TrainTime

Plataforma esportiva para atletas e treinadores.

## Objetivo

Permitir que atletas acompanhem seus treinos pelo celular e que treinadores gerenciem atletas, equipes, treinos, avaliacoes, desempenho e escalacoes.

## Esportes

- Volei
- Basquete

Novos esportes poderao ser adicionados no futuro.

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI |
| Banco | SQLite (migravel para PostgreSQL) |

## Como Executar

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

A API estara disponivel em: `http://localhost:8000`
Documentacao automatica: `http://localhost:8000/docs`

### Frontend

O frontend e servido automaticamente pelo FastAPI na raiz: `http://localhost:8000`

### Testes

```bash
cd backend
pytest tests/ -v
```

## Estrutura

```
TrainTime/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── routes/
│   │   └── database/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── pages/
│   ├── components/
│   ├── css/
│   ├── js/
│   └── assets/
├── docs/
├── README.md
└── .gitignore
```

## Fase Atual

**FASE 1** - Fundacao, arquitetura e estrutura inicial

### Implementado

- Estrutura do projeto
- Backend com FastAPI
- Banco de dados SQLite com SQLAlchemy
- Modelos: User, Sport, Position, SportAttribute, Athlete, Coach, Team
- API: health, sports, positions, attributes
- Dados iniciais: Volei e Basquete com posicoes e atributos
- Frontend responsivo mobile-first
- Identidade visual
- Testes basicos
- Documentacao

### Planejado (Fases futuras)

- Autenticacao completa
- Sistema de treinos
- Acompanhamento de desempenho
- Avaliacoes de treinadores
- Escalacoes
- Integracao com IA (modulo opcional)
- Suporte a mais esportes
