from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from backend.app.poker.cards import parse_card

Street = Literal["flop", "turn", "river"]
Position = Literal["ip", "oop"]


class HandState(BaseModel):
    hero_cards: list[str] = Field(min_length=2, max_length=2)
    board_cards: list[str] = Field(default_factory=list, max_length=5)
    pot: int = Field(ge=0)
    amount_to_call: int = Field(ge=0)
    hero_stack: int = Field(ge=0)
    opponent_stack: int = Field(ge=0)
    street: Street
    position: Position
    opponent_id: str = Field(min_length=1)
    min_raise_to: int = Field(ge=0, default=0)
    simulation_trials: int = Field(default=15000, ge=200, le=100000)
    seed: int | None = None
    range_weights: dict[str, float] | None = None

    @model_validator(mode="after")
    def validate_cards(self) -> "HandState":
        cards = self.hero_cards + self.board_cards
        parsed: list[int] = []
        for card in cards:
            try:
                parsed.append(parse_card(card))
            except ValueError as exc:
                raise ValueError(f"Invalid card '{card}': use rank+suit like As, Kh, 7d") from exc

        if len(parsed) != len(set(parsed)):
            raise ValueError("Duplicate cards in hero/board")

        expected_board = {"flop": 3, "turn": 4, "river": 5}[self.street]
        if len(self.board_cards) != expected_board:
            raise ValueError(
                f"Street '{self.street}' requires exactly {expected_board} board cards"
            )

        if self.amount_to_call > self.hero_stack:
            raise ValueError("amount_to_call cannot exceed hero_stack")

        return self


class EquityRequest(BaseModel):
    hero_cards: list[str] = Field(min_length=2, max_length=2)
    board_cards: list[str] = Field(default_factory=list, max_length=5)
    trials: int = Field(default=15000, ge=200, le=100000)
    seed: int | None = None
    range_weights: dict[str, float] | None = None

    @model_validator(mode="after")
    def validate_cards(self) -> "EquityRequest":
        cards = self.hero_cards + self.board_cards
        parsed: list[int] = []
        for card in cards:
            try:
                parsed.append(parse_card(card))
            except ValueError as exc:
                raise ValueError(f"Invalid card '{card}': use rank+suit like As, Kh, 7d") from exc
        if len(parsed) != len(set(parsed)):
            raise ValueError("Duplicate cards in hero/board")
        return self


class RangeUpdateRequest(BaseModel):
    hero_cards: list[str] = Field(min_length=2, max_length=2)
    board_cards: list[str] = Field(default_factory=list, max_length=5)
    action: Literal["check", "call", "bet", "raise", "fold"]
    range_weights: dict[str, float] | None = None

    @model_validator(mode="after")
    def validate_cards(self) -> "RangeUpdateRequest":
        cards = self.hero_cards + self.board_cards
        parsed: list[int] = []
        for card in cards:
            try:
                parsed.append(parse_card(card))
            except ValueError as exc:
                raise ValueError(f"Invalid card '{card}': use rank+suit like As, Kh, 7d") from exc
        if len(parsed) != len(set(parsed)):
            raise ValueError("Duplicate cards in hero/board")
        if len(self.board_cards) not in {3, 4, 5}:
            raise ValueError("Range updates require 3, 4, or 5 board cards")
        return self


class OpponentObservationRequest(BaseModel):
    opponent_id: str = Field(min_length=1)
    archetype: str = "unknown"
    event: Literal["fold_vs_raise", "raise", "cbet"]
    success: bool
