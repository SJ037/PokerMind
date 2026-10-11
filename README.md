# PokerMind

PokerMind is a research-oriented, heads-up no-limit Texas Hold'em analysis platform.

## Core release implemented here

- Manual hand-state analysis API
- Correct card/deck model with collision checks
- Seven-card hand evaluation with kickers/ties
- Weighted opponent ranges with Bayesian action updates
- Monte Carlo equity with uncertainty estimation
- Pot odds and EV comparison for fold/call/raise candidates
- Adaptive opponent profile updates (Beta-Bernoulli tendencies)
- Minimal React dashboard for interactive analysis

## Architecture

- `backend/app/poker`: cards, evaluator, rules, pots
- `backend/app/simulation`: weighted sampling + Monte Carlo equity
- `backend/app/modeling`: ranges + opponent Bayesian updates
- `backend/app/strategy`: EV and recommendation logic
- `backend/app/api`: FastAPI endpoints
- `backend/tests`: unit and property-style tests
- `frontend`: Vite + React + TypeScript UI

## Quick start

### Backend

```bash
cd /Users/shauryajain/Desktop/Code/PokerMind
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn backend.app.main:app --reload --port 8000
```

### Frontend

```bash
cd /Users/shauryajain/Desktop/Code/PokerMind/frontend
npm install
npm run dev
```

Set `VITE_API_BASE_URL` if backend is not `http://127.0.0.1:8000`.

## Key endpoints

- `POST /api/equity`
- `POST /api/ranges/update`
- `POST /api/analyze`
- `GET /api/opponents`
- `GET /api/opponents/{opponent_id}`
- `POST /api/opponents/observe`

## Notes

- First release targets heads-up post-flop decision support.
- Recommendations are model estimates, not guarantees.
- Persisted opponent stats are stored in SQLite (`pokermind.db`).
- Decision-state EV conventions and branch formulas are documented in `docs/decision_math.md`.
