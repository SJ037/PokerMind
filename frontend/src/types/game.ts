export type AnalyzeRequest = {
  hero_cards: string[]
  board_cards: string[]
  pot: number
  amount_to_call: number
  hero_stack: number
  opponent_stack: number
  street: 'flop' | 'turn' | 'river'
  position: 'ip' | 'oop'
  opponent_id: string
  min_raise_to: number
  simulation_trials: number
  seed?: number
}

type FutureTerms = {
  streets_left: number
  realization_factor: number
  expected_future_cost: number
  barrel_probability: number
  bet_fraction: number
}

type BranchDetails = {
  raw_response_probs?: { fold: number; call: number; raise: number }
  adjusted_response_probs?: { fold: number; call: number; raise: number }
  branch_values?: { fold: number; call: number; raise: number }
  base_call_ev?: number
  future_terms?: FutureTerms
}

type ActionSensitivity = {
  fold_prob_minus_10pp_ev: number
  fold_prob_plus_10pp_ev: number
}

export type ActionEvaluation = {
  action: string
  amount: number
  ev: number
  raw_ev?: number
  adjusted_ev?: number
  safeguard_penalty?: number
  safeguard_breakdown?: {
    risk_penalty: number
    confidence_penalty: number
    weak_hand_penalty: number
    board_texture_penalty: number
  }
  branch_details?: BranchDetails
  sensitivity?: ActionSensitivity | null
  assumptions?: string[]
}

type EstimatorSnapshot = {
  alpha: number
  beta: number
  mean: number
  effective_n: number
}

type OpponentProfileSnapshot = {
  opponent_id: string
  archetype: string
  fold_vs_raise: EstimatorSnapshot
  raise_frequency: EstimatorSnapshot
  cbet_frequency: EstimatorSnapshot
}

type RangeComboWeight = {
  combo: string
  weight: number
  strength_rank?: number
  hand_category?: string
}

type BestPossibleHand = {
  hand_category: string
  probability: number
  best_combo: string
  best_combo_probability: number
}

export type AnalyzeResponse = {
  decision_report: {
    recommended_action: ActionEvaluation
    alternatives: ActionEvaluation[]
    decision_layers?: {
      legality: string
      raw_ev: string
      safeguards: string
    }
    decision_controls?: {
      confidence_margin: number
      note: string
    }
    equity: {
      equity: number
      win_rate: number
      tie_rate: number
      loss_rate: number
      std_error: number
      trials: number
    }
  }
  opponent_profile?: OpponentProfileSnapshot
  top_range_combos?: RangeComboWeight[]
  best_possible_hand?: BestPossibleHand
  assumptions: string[]
}
