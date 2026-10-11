# PokerMind Decision Math Contract

This document defines the EV convention used by PokerMind so fold/call/raise/all-in values are comparable.

## Decision-state convention

- EV is measured from the **current decision point**.
- Chips invested before this decision are sunk costs.
- `EV_fold = 0` by definition.
- `pot_at_decision` includes chips already in the pot before hero acts.
- `amount_to_call` is the additional amount hero must invest to continue.

## Call EV (simplified one-step model)

When hero calls and no future betting is modeled:

\[
EV_{call} = E(P + C) - C
\]

- `E`: hero equity vs modeled opponent range
- `P`: pot at decision point
- `C`: hero call amount

## Raise EV branch decomposition

For a raise amount `R`:

\[
EV_{raise} = p_f V_f + p_c V_c + p_r V_r
\]

Where:

- `V_f = P`
- `V_c = E_{called}(P + 2R - C) - R`
- `V_r = -R`

And:

- `p_f, p_c, p_r` are opponent fold/call/reraise probabilities.
- For all-in actions, reraise probability is forced to zero and mass is normalized over fold/call.

## Recommendation layers

PokerMind reports three layers separately:

1. **Legality layer**: legal actions only (stack/effective-stack/min-raise constrained)
2. **Raw EV layer**: branch EV from formulas above, no safeguard penalties
3. **Safeguard layer**: conservative penalties and confidence margin applied after raw EV

The API includes both `raw_ev` and `adjusted_ev` to keep these layers auditable.

## Scope note

Current recommendations use a continuation-aware approximation on flop/turn:

- A future-street pressure model estimates expected barrel frequency, future call costs, and equity realization discount.
- These terms are applied to call and raise-called branches.
- Full game-tree solving is still not implemented; this remains an approximation.
