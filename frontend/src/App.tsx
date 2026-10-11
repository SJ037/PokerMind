import { ChangeEvent, useMemo, useState } from 'react'
import { analyzeHand } from './api/client'
import type { AnalyzeResponse } from './types/game'

const CARD_REGEX = /^[2-9TJQKA][cdhs]$/i
const RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
const SUITS = ['s', 'h', 'd', 'c']
const DECK = SUITS.flatMap((suit) => RANKS.map((rank) => `${rank}${suit}`))
type ActiveSlot = 'h0' | 'h1' | 'b0' | 'b1' | 'b2' | 'b3' | 'b4'
type Position = 'ip' | 'oop'

const SUIT_SYMBOL: Record<string, string> = {
  s: '♠',
  h: '♥',
  d: '♦',
  c: '♣',
}

function parseCardsInput(value: string): string[] {
  return value
    .split(/\s+/)
    .filter(Boolean)
    .map((card) => `${card[0]?.toUpperCase() ?? ''}${card[1]?.toLowerCase() ?? ''}`)
}

function formatPct(value: number): string {
  return `${(value * 100).toFixed(2)}%`
}

function streetFromBoard(boardCards: string[]): 'flop' | 'turn' | 'river' {
  if (boardCards.length === 3) {
    return 'flop'
  }
  if (boardCards.length === 4) {
    return 'turn'
  }
  return 'river'
}

function cardSuitClass(card: string): string {
  const suit = card[1]?.toLowerCase()
  if (suit === 'h' || suit === 'd') {
    return 'redSuit'
  }
  return 'blackSuit'
}

export function App() {
  const [heroCards, setHeroCards] = useState('As Kh')
  const [boardCards, setBoardCards] = useState('7s 8s 2d')
  const [pot, setPot] = useState(120)
  const [toCall, setToCall] = useState(40)
  const [heroStack, setHeroStack] = useState(900)
  const [oppStack, setOppStack] = useState(880)
  const [simulationTrials, setSimulationTrials] = useState(15000)
  const [position, setPosition] = useState<Position>('ip')
  const [activeSlot, setActiveSlot] = useState<ActiveSlot>('h0')
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const heroList = useMemo(() => parseCardsInput(heroCards), [heroCards])
  const boardList = useMemo(() => parseCardsInput(boardCards), [boardCards])
  const heroSlots = useMemo(() => [heroList[0] ?? '', heroList[1] ?? ''], [heroList])
  const boardSlots = useMemo(
    () => [boardList[0] ?? '', boardList[1] ?? '', boardList[2] ?? '', boardList[3] ?? '', boardList[4] ?? ''],
    [boardList],
  )
  const inferredStreet = useMemo(() => streetFromBoard(boardList), [boardList])

  const validationIssues = useMemo(() => {
    const issues: string[] = []
    if (heroList.length !== 2) {
      issues.push('Hero cards must contain exactly 2 cards.')
    }
    if (boardList.length < 3 || boardList.length > 5) {
      issues.push('Board must contain 3, 4, or 5 cards for flop/turn/river analysis.')
    }

    const allCards = [...heroList, ...boardList]
    const invalid = allCards.filter((card) => !CARD_REGEX.test(card))
    if (invalid.length > 0) {
      issues.push(`Invalid card format: ${invalid.join(', ')} (use As, Kh, 7d, 2c).`)
    }

    if (new Set(allCards).size !== allCards.length) {
      issues.push('Duplicate cards detected between hero and board.')
    }

    if (pot < 0 || toCall < 0 || heroStack < 0 || oppStack < 0) {
      issues.push('Pot, call amount, and stacks must be non-negative.')
    }

    if (toCall > heroStack) {
      issues.push('Amount to call cannot exceed hero stack.')
    }

    if (simulationTrials < 200 || simulationTrials > 100000) {
      issues.push('Simulation trials must be between 200 and 100000.')
    }
    return issues
  }, [heroList, boardList, pot, toCall, heroStack, oppStack, simulationTrials])

  const payload = useMemo(
    () => ({
      hero_cards: heroList,
      board_cards: boardList,
      pot,
      amount_to_call: toCall,
      hero_stack: heroStack,
      opponent_stack: oppStack,
      street: inferredStreet,
      position,
      opponent_id: 'villain-1',
      min_raise_to: Math.max(toCall * 2, 1),
      simulation_trials: simulationTrials,
      seed: 42,
    }),
    [heroList, boardList, pot, toCall, heroStack, oppStack, simulationTrials, inferredStreet, position],
  )

  const onTextChange = (setter: (value: string) => void) => (event: ChangeEvent<HTMLInputElement>) => {
    setter(event.target.value)
  }

  const onNumberChange = (setter: (value: number) => void) => (event: ChangeEvent<HTMLInputElement>) => {
    setter(Number(event.target.value))
  }

  const syncFromSlots = (nextHeroSlots: string[], nextBoardSlots: string[]) => {
    setHeroCards(nextHeroSlots.filter(Boolean).join(' '))
    setBoardCards(nextBoardSlots.filter(Boolean).join(' '))
    setError(null)
  }

  const setCardInActiveSlot = (card: string) => {
    const nextHeroSlots = [...heroSlots]
    const nextBoardSlots = [...boardSlots]

    for (let i = 0; i < nextHeroSlots.length; i += 1) {
      if (nextHeroSlots[i] === card) {
        nextHeroSlots[i] = ''
      }
    }
    for (let i = 0; i < nextBoardSlots.length; i += 1) {
      if (nextBoardSlots[i] === card) {
        nextBoardSlots[i] = ''
      }
    }

    if (activeSlot.startsWith('h')) {
      const idx = Number(activeSlot[1])
      nextHeroSlots[idx] = card
    } else {
      const idx = Number(activeSlot[1])
      nextBoardSlots[idx] = card
    }

    syncFromSlots(nextHeroSlots, nextBoardSlots)
  }

  const clearActiveSlot = () => {
    const nextHeroSlots = [...heroSlots]
    const nextBoardSlots = [...boardSlots]
    if (activeSlot.startsWith('h')) {
      nextHeroSlots[Number(activeSlot[1])] = ''
    } else {
      nextBoardSlots[Number(activeSlot[1])] = ''
    }
    syncFromSlots(nextHeroSlots, nextBoardSlots)
  }

  const clearAllCards = () => {
    setHeroCards('')
    setBoardCards('')
    setResult(null)
    setError(null)
  }

  const runAnalysis = async () => {
    if (validationIssues.length > 0) {
      setError('Please fix validation issues before running analysis.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = await analyzeHand(payload)
      setResult(data)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const drawRandomCards = (count: number, excludedCards: string[]): string[] => {
    const excluded = new Set(excludedCards.filter(Boolean))
    const available = DECK.filter((card) => !excluded.has(card))
    const picked: string[] = []
    while (picked.length < count && available.length > 0) {
      const idx = Math.floor(Math.random() * available.length)
      const [card] = available.splice(idx, 1)
      picked.push(card)
    }
    return picked
  }

  const randomizeHero = () => {
    const nextHero = drawRandomCards(2, boardSlots)
    syncFromSlots(nextHero, [...boardSlots])
    setResult(null)
  }

  const randomizeFlop = () => {
    const keepTurnRiver = [boardSlots[3], boardSlots[4]].filter(Boolean)
    const flop = drawRandomCards(3, [...heroSlots, ...keepTurnRiver])
    const nextBoard = [flop[0] ?? '', flop[1] ?? '', flop[2] ?? '', boardSlots[3], boardSlots[4]]
    syncFromSlots([...heroSlots], nextBoard)
    setResult(null)
  }

  const randomizeTurn = () => {
    const flop = [boardSlots[0], boardSlots[1], boardSlots[2]]
    const exclusions = [...heroSlots, ...flop, boardSlots[4]]
    const turn = drawRandomCards(1, exclusions)[0] ?? ''
    const nextBoard = [...boardSlots]
    nextBoard[3] = turn
    syncFromSlots([...heroSlots], nextBoard)
    setResult(null)
  }

  const randomizeRiver = () => {
    const exclusions = [...heroSlots, boardSlots[0], boardSlots[1], boardSlots[2], boardSlots[3]]
    const river = drawRandomCards(1, exclusions)[0] ?? ''
    const nextBoard = [...boardSlots]
    nextBoard[4] = river
    syncFromSlots([...heroSlots], nextBoard)
    setResult(null)
  }

  const recommended = result?.decision_report.recommended_action
  const actions = result?.decision_report.alternatives ?? []
  const topRangeCombos = result?.top_range_combos?.slice(0, 8) ?? []
  const bestPossibleHand = result?.best_possible_hand

  return (
    <main className="workstationRoot">
      <header className="appHeader">
        <div className="wordmarkBlock">
          <h1>PokerMind</h1>
        </div>
      </header>

      <section className="workbenchGrid">
        <section className="pane leftPane">
          <div className="sectionHeader">
            <h2>Hand State</h2>
            <span className="sectionHint">Cards, stacks, and betting state</span>
          </div>

          <div className="tableSurface">
            <div>
              <p className="labelTiny">Board</p>
              <div className="tableCardsRow">
                {boardSlots.map((card, idx) => (
                  <button
                    key={`board-slot-${idx}`}
                    type="button"
                    className={`tableCard ${!card ? 'emptyCard' : ''} ${card ? cardSuitClass(card) : ''}`}
                    onClick={() => setActiveSlot((`b${idx}` as ActiveSlot))}
                    title={`Board slot ${idx + 1}`}
                  >
                    {card ? (
                      <>
                        <span>{card[0].toUpperCase()}</span>
                        <span>{SUIT_SYMBOL[card[1].toLowerCase()]}</span>
                      </>
                    ) : (
                      <span>--</span>
                    )}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <p className="labelTiny">Hero</p>
              <div className="tableCardsRow">
                {heroSlots.map((card, idx) => (
                  <button
                    key={`hero-slot-${idx}`}
                    type="button"
                    className={`tableCard ${!card ? 'emptyCard' : ''} ${card ? cardSuitClass(card) : ''}`}
                    onClick={() => setActiveSlot((`h${idx}` as ActiveSlot))}
                    title={`Hero slot ${idx + 1}`}
                  >
                    {card ? (
                      <>
                        <span>{card[0].toUpperCase()}</span>
                        <span>{SUIT_SYMBOL[card[1].toLowerCase()]}</span>
                      </>
                    ) : (
                      <span>--</span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="subSection">
            <p className="subSectionTitle">Card Selector</p>
            <div className="slotGrid">
              <button
                type="button"
                className={`slotChip ${activeSlot === 'h0' ? 'activeSlot' : ''}`}
                onClick={() => setActiveSlot('h0')}
              >
                Hero 1: {heroSlots[0] || '--'}
              </button>
              <button
                type="button"
                className={`slotChip ${activeSlot === 'h1' ? 'activeSlot' : ''}`}
                onClick={() => setActiveSlot('h1')}
              >
                Hero 2: {heroSlots[1] || '--'}
              </button>
              <button
                type="button"
                className={`slotChip ${activeSlot === 'b0' ? 'activeSlot' : ''}`}
                onClick={() => setActiveSlot('b0')}
              >
                Flop 1: {boardSlots[0] || '--'}
              </button>
              <button
                type="button"
                className={`slotChip ${activeSlot === 'b1' ? 'activeSlot' : ''}`}
                onClick={() => setActiveSlot('b1')}
              >
                Flop 2: {boardSlots[1] || '--'}
              </button>
              <button
                type="button"
                className={`slotChip ${activeSlot === 'b2' ? 'activeSlot' : ''}`}
                onClick={() => setActiveSlot('b2')}
              >
                Flop 3: {boardSlots[2] || '--'}
              </button>
              <button
                type="button"
                className={`slotChip ${activeSlot === 'b3' ? 'activeSlot' : ''}`}
                onClick={() => setActiveSlot('b3')}
              >
                Turn: {boardSlots[3] || '--'}
              </button>
              <button
                type="button"
                className={`slotChip ${activeSlot === 'b4' ? 'activeSlot' : ''}`}
                onClick={() => setActiveSlot('b4')}
              >
                River: {boardSlots[4] || '--'}
              </button>
            </div>

            <p className="labelTiny">
              Active slot: {activeSlot.startsWith('h') ? 'Hero' : 'Board'} {Number(activeSlot[1]) + 1}
            </p>

            <div className="deckGrid">
              {SUITS.map((suit) => (
                <div key={suit} className="suitRow">
                  {RANKS.map((rank) => {
                    const card = `${rank}${suit}`
                    const isUsed = heroList.includes(card) || boardList.includes(card)
                    const isActiveValue =
                      (activeSlot.startsWith('h') && heroSlots[Number(activeSlot[1])] === card) ||
                      (!activeSlot.startsWith('h') && boardSlots[Number(activeSlot[1])] === card)
                    return (
                      <button
                        key={card}
                        type="button"
                        className={`cardBtn ${isUsed ? 'usedCard' : ''} ${isActiveValue ? 'selectedCard' : ''} ${cardSuitClass(card)}`}
                        onClick={() => setCardInActiveSlot(card)}
                      >
                        <span>{card[0]}</span>
                        <span>{SUIT_SYMBOL[suit]}</span>
                      </button>
                    )
                  })}
                </div>
              ))}
            </div>

            <div className="pickerActions">
              <button type="button" className="secondaryBtn" onClick={clearActiveSlot}>
                Clear active slot
              </button>
              <button type="button" className="secondaryBtn" onClick={clearAllCards}>
                Clear all cards
              </button>
            </div>

            <div className="pickerActions">
              <button type="button" className="secondaryBtn" onClick={randomizeHero}>
                Random hero
              </button>
              <button type="button" className="secondaryBtn" onClick={randomizeFlop}>
                Random flop
              </button>
              <button type="button" className="secondaryBtn" onClick={randomizeTurn}>
                Random turn
              </button>
              <button type="button" className="secondaryBtn" onClick={randomizeRiver}>
                Random river
              </button>
            </div>
          </div>

          <div className="subSection">
            <p className="subSectionTitle">State Inputs</p>
            <div className="formGrid">
              <label>
                Hero cards
                <input value={heroCards} onChange={onTextChange(setHeroCards)} placeholder="As Kh" />
              </label>
              <label>
                Board cards
                <input value={boardCards} onChange={onTextChange(setBoardCards)} placeholder="7s 8s 2d" />
              </label>
              <label>
                Pot size
                <input type="number" value={pot} onChange={onNumberChange(setPot)} />
              </label>
              <label>
                Amount to call
                <input type="number" value={toCall} onChange={onNumberChange(setToCall)} />
              </label>
              <label>
                Hero stack
                <input type="number" value={heroStack} onChange={onNumberChange(setHeroStack)} />
              </label>
              <label>
                Opponent stack
                <input type="number" value={oppStack} onChange={onNumberChange(setOppStack)} />
              </label>
              <label>
                Position
                <select value={position} onChange={(event) => setPosition(event.target.value as Position)}>
                  <option value="ip">In Position</option>
                  <option value="oop">Out of Position</option>
                </select>
              </label>
              <label>
                Simulation trials
                <input
                  type="number"
                  min={200}
                  max={100000}
                  step={500}
                  value={simulationTrials}
                  onChange={onNumberChange(setSimulationTrials)}
                />
              </label>
            </div>

          </div>

          {validationIssues.length > 0 ? (
            <div className="issueBox">
              <h3>Input issues</h3>
              <ul>
                {validationIssues.map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>

        <section className="pane centerPane">
          <div className="sectionHeader">
            <h2>Decision Analysis</h2>
            <span className="sectionHint">Action comparison and recommendation</span>
          </div>

          <div className="analysisToolbar">
            <button type="button" className="primaryBtn" onClick={runAnalysis} disabled={loading || validationIssues.length > 0}>
              {loading ? 'Running analysis…' : 'Run analysis'}
            </button>
            <div className="stateSummary">
              <span>Street: {inferredStreet.toUpperCase()}</span>
              <span>Pot: {pot}</span>
              <span>To Call: {toCall}</span>
              <span>Position: {position.toUpperCase()}</span>
            </div>
          </div>

          {error ? <p className="errorText">{error}</p> : null}

          {!result ? (
            <div className="emptyState">Run analysis to generate recommendation, EV comparisons, and equity metrics.</div>
          ) : (
            <>
              <div className="recommendationRow">
                <div>
                  <p className="labelTiny">Recommended action</p>
                  <p className="recommendationAction">
                    {recommended?.action.toUpperCase()}
                    {recommended && recommended.amount > 0 ? ` ${recommended.amount}` : ''}
                  </p>
                </div>
                <div className="monoValue">Adj EV {(recommended?.adjusted_ev ?? recommended?.ev ?? 0).toFixed(2)}</div>
              </div>

              <table className="evTable">
                <thead>
                  <tr>
                    <th>Action</th>
                    <th className="num">Raw EV</th>
                    <th className="num">Adjusted EV</th>
                    <th className="num">Penalty</th>
                  </tr>
                </thead>
                <tbody>
                  {actions.map((row) => {
                    const adjusted = row.adjusted_ev ?? row.ev
                    const isBest = row.action === recommended?.action && row.amount === recommended?.amount
                    return (
                      <tr key={`${row.action}-${row.amount}`} className={isBest ? 'bestRow' : ''}>
                        <td>
                          {row.action.toUpperCase()}
                          {row.amount > 0 ? ` ${row.amount}` : ''}
                        </td>
                        <td className="num monoValue">{(row.raw_ev ?? row.ev).toFixed(2)}</td>
                        <td className={`num monoValue ${adjusted >= 0 ? 'pos' : 'neg'}`}>{adjusted.toFixed(2)}</td>
                        <td className="num monoValue">{(row.safeguard_penalty ?? 0).toFixed(2)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>

            </>
          )}
        </section>

        <section className="pane rightPane">
          <div className="sectionHeader">
            <h2>Simulation</h2>
            <span className="sectionHint">Probabilities, uncertainty, and assumptions</span>
          </div>

          {!result ? (
            <div className="emptyState">Results appear here after running analysis.</div>
          ) : (
            <>
              <div className="statsTable">
                <div><span>Win probability</span><strong className="monoValue">{formatPct(result.decision_report.equity.win_rate)}</strong></div>
                <div><span>Tie probability</span><strong className="monoValue">{formatPct(result.decision_report.equity.tie_rate)}</strong></div>
                <div><span>Loss probability</span><strong className="monoValue">{formatPct(result.decision_report.equity.loss_rate)}</strong></div>
                <div><span>Equity</span><strong className="monoValue">{formatPct(result.decision_report.equity.equity)}</strong></div>
                <div><span>Std error</span><strong className="monoValue">{formatPct(result.decision_report.equity.std_error)}</strong></div>
                <div><span>Trials</span><strong className="monoValue">{result.decision_report.equity.trials}</strong></div>
              </div>

              <div className="probBars">
                <div className="barRow">
                  <span>W</span>
                  <div className="barTrack"><div className="barFill winBar" style={{ width: `${result.decision_report.equity.win_rate * 100}%` }} /></div>
                  <span className="monoValue">{formatPct(result.decision_report.equity.win_rate)}</span>
                </div>
                <div className="barRow">
                  <span>T</span>
                  <div className="barTrack"><div className="barFill tieBar" style={{ width: `${result.decision_report.equity.tie_rate * 100}%` }} /></div>
                  <span className="monoValue">{formatPct(result.decision_report.equity.tie_rate)}</span>
                </div>
                <div className="barRow">
                  <span>L</span>
                  <div className="barTrack"><div className="barFill lossBar" style={{ width: `${result.decision_report.equity.loss_rate * 100}%` }} /></div>
                  <span className="monoValue">{formatPct(result.decision_report.equity.loss_rate)}</span>
                </div>
              </div>

              <div className="subSection">
                <p className="subSectionTitle">Simulation settings</p>
                <p className="monoValue">Trials: {simulationTrials}</p>
                <p className="monoValue">Seed: 42</p>
              </div>

              {topRangeCombos.length > 0 ? (
                <div className="subSection">
                  <p className="subSectionTitle">Top range combos</p>
                  {bestPossibleHand ? (
                    <p>
                      Best possible: <span className="monoValue">{bestPossibleHand.hand_category}</span>{' '}
                      (<span className="monoValue">{formatPct(bestPossibleHand.probability)}</span>) · top combo{' '}
                      <span className="monoValue">{bestPossibleHand.best_combo}</span>{' '}
                      (<span className="monoValue">{formatPct(bestPossibleHand.best_combo_probability)}</span>)
                    </p>
                  ) : null}
                  <ul className="rangeList">
                    {topRangeCombos.map((item) => (
                      <li key={`${item.combo}-${item.strength_rank ?? ''}`}>
                        <span>
                          <span className="monoValue">{item.combo}</span>
                          {item.hand_category ? ` · ${item.hand_category}` : ''}
                        </span>
                        <span className="monoValue">{formatPct(item.weight)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </>
          )}
        </section>
      </section>

    </main>
  )
}
