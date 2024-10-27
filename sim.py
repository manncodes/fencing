import os
import random
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple

from colorama import Back, Fore, Style, init


# Core Enums
class DistanceType(Enum):
    OUT_OF_DISTANCE = "Out of Distance"  # >3m
    LONG = "Long Distance"  # 2-3m
    MEDIUM = "Medium Distance"  # 1.5-2m
    LUNGE = "Lunge Distance"  # 1-1.5m
    SHORT = "Short Distance"  # 0.5-1m
    INFIGHTING = "Infighting"  # <0.5m


class ActionType(Enum):
    # Preparation Actions
    ADVANCE = "Advance"
    RETREAT = "Retreat"
    BALANCE_BREAK = "Balance Break"

    # Simple Attacks
    DIRECT_THRUST = "Direct Thrust"
    DISENGAGE = "Disengage"
    CUT_OVER = "Cut Over"
    COUNTER_DISENGAGE = "Counter Disengage"

    # Compound Attacks
    ONE_TWO = "One-Two"
    DOUBLE_DISENGAGE = "Double Disengage"
    ONE_TWO_THREE = "One-Two-Three"
    FEINT_DISENGAGE = "Feint Disengage"
    BEAT_DIRECT = "Beat Direct"

    # Counter Attacks
    STOP_THRUST = "Stop Thrust"
    TIME_THRUST = "Time Thrust"
    POINT_IN_LINE = "Point in Line"

    # Blade Actions
    BEAT = "Beat"
    PRESSURE = "Pressure"
    BIND = "Bind"
    ENVELOPMENT = "Envelopment"


class DefenseType(Enum):
    # Simple Parries
    PARRY_1 = "Prime"
    PARRY_2 = "Seconde"
    PARRY_3 = "Tierce"
    PARRY_4 = "Quarte"
    PARRY_5 = "Quinte"
    PARRY_6 = "Sixte"
    PARRY_7 = "Septime"
    PARRY_8 = "Octave"

    # Circular Parries
    COUNTER_SIXTE = "Counter of Sixte"
    COUNTER_QUARTE = "Counter of Quarte"
    COUNTER_SEPTIME = "Counter of Septime"
    COUNTER_OCTAVE = "Counter of Octave"

    # Semi-circular Parries
    SEMI_CIRCULAR_2_TO_6 = "Semi-circular 2 to 6"
    SEMI_CIRCULAR_4_TO_8 = "Semi-circular 4 to 8"
    SEMI_CIRCULAR_6_TO_7 = "Semi-circular 6 to 7"

    # Compound Parries
    DOUBLE_PARRY = "Double Parry"
    CIRCLE_CHANGE = "Circle Change"
    BEAT_PARRY = "Beat Parry"


class BladePosition(Enum):
    SIXTE = "Sixte"
    QUARTE = "Quarte"
    SEPTIME = "Septime"
    OCTAVE = "Octave"
    PRIME = "Prime"
    SECONDE = "Seconde"
    TIERCE = "Tierce"
    QUINTE = "Quinte"


@dataclass
class ActionProperties:
    name: str
    execution_time: float
    base_success_rate: float
    valid_distances: Set[DistanceType]
    vulnerable_to: Set[DefenseType]
    effective_against: Set[DefenseType]
    preparation_required: bool
    priority: bool
    description: str


@dataclass
class DefenseProperties:
    name: str
    execution_time: float
    base_success_rate: float
    effective_against: Set[ActionType]
    follow_up_actions: Set[ActionType]
    description: str


class ActionDatabase:
    """Central repository for all action definitions and their properties"""

    @staticmethod
    def get_all_actions() -> Dict[ActionType, ActionProperties]:
        actions = {}

        # Simple Attacks
        actions[ActionType.DIRECT_THRUST] = ActionProperties(
            name="Direct Thrust",
            execution_time=0.2,
            base_success_rate=0.7,
            valid_distances={DistanceType.LUNGE, DistanceType.SHORT},
            vulnerable_to={DefenseType.PARRY_4, DefenseType.PARRY_6},
            effective_against={DefenseType.COUNTER_SIXTE},
            preparation_required=False,
            priority=True,
            description="Straight attack to target")

        actions[ActionType.DISENGAGE] = ActionProperties(
            name="Disengage",
            execution_time=0.3,
            base_success_rate=0.65,
            valid_distances={DistanceType.LUNGE, DistanceType.SHORT},
            vulnerable_to={
                DefenseType.COUNTER_SIXTE, DefenseType.COUNTER_QUARTE
            },
            effective_against={DefenseType.PARRY_4, DefenseType.PARRY_6},
            preparation_required=False,
            priority=True,
            description="Attack around opponent's blade")

        # Compound Attacks
        actions[ActionType.ONE_TWO] = ActionProperties(
            name="One-Two",
            execution_time=0.4,
            base_success_rate=0.6,
            valid_distances={DistanceType.MEDIUM, DistanceType.LUNGE},
            vulnerable_to={
                DefenseType.DOUBLE_PARRY, DefenseType.CIRCLE_CHANGE
            },
            effective_against={DefenseType.PARRY_4, DefenseType.PARRY_6},
            preparation_required=True,
            priority=True,
            description="Feint direct, disengage attack")

        # Counter Attacks
        actions[ActionType.STOP_THRUST] = ActionProperties(
            name="Stop Thrust",
            execution_time=0.3,
            base_success_rate=0.6,
            valid_distances={DistanceType.MEDIUM, DistanceType.LUNGE},
            vulnerable_to={DefenseType.PARRY_4, DefenseType.PARRY_6},
            effective_against={DefenseType.COUNTER_SIXTE},
            preparation_required=False,
            priority=True,
            description="Counter-attack to stop opponent's attack")

        actions[ActionType.CUT_OVER] = ActionProperties(
            name="Cut Over",
            execution_time=0.25,
            base_success_rate=0.65,
            valid_distances={DistanceType.LUNGE, DistanceType.SHORT},
            vulnerable_to={DefenseType.PARRY_4, DefenseType.PARRY_6},
            effective_against={DefenseType.COUNTER_SIXTE},
            preparation_required=False,
            priority=True,
            description="Attack over opponent's blade")

        actions[ActionType.COUNTER_DISENGAGE] = ActionProperties(
            name="Counter Disengage",
            execution_time=0.35,
            base_success_rate=0.6,
            valid_distances={DistanceType.LUNGE, DistanceType.SHORT},
            vulnerable_to={
                DefenseType.COUNTER_SIXTE, DefenseType.COUNTER_QUARTE
            },
            effective_against={DefenseType.PARRY_4, DefenseType.PARRY_6},
            preparation_required=False,
            priority=True,
            description="Counter-attack around opponent's blade")

        actions[ActionType.DOUBLE_DISENGAGE] = ActionProperties(
            name="Double Disengage",
            execution_time=0.45,
            base_success_rate=0.55,
            valid_distances={DistanceType.MEDIUM, DistanceType.LUNGE},
            vulnerable_to={
                DefenseType.DOUBLE_PARRY, DefenseType.CIRCLE_CHANGE
            },
            effective_against={DefenseType.PARRY_4, DefenseType.PARRY_6},
            preparation_required=True,
            priority=True,
            description="Double feint disengage attack")

        actions[ActionType.ONE_TWO_THREE] = ActionProperties(
            name="One-Two-Three",
            execution_time=0.5,
            base_success_rate=0.5,
            valid_distances={DistanceType.MEDIUM, DistanceType.LUNGE},
            vulnerable_to={
                DefenseType.DOUBLE_PARRY, DefenseType.CIRCLE_CHANGE
            },
            effective_against={DefenseType.PARRY_4, DefenseType.PARRY_6},
            preparation_required=True,
            priority=True,
            description="Triple feint disengage attack")

        actions[ActionType.FEINT_DISENGAGE] = ActionProperties(
            name="Feint Disengage",
            execution_time=0.4,
            base_success_rate=0.6,
            valid_distances={DistanceType.MEDIUM, DistanceType.LUNGE},
            vulnerable_to={
                DefenseType.DOUBLE_PARRY, DefenseType.CIRCLE_CHANGE
            },
            effective_against={DefenseType.PARRY_4, DefenseType.PARRY_6},
            preparation_required=True,
            priority=True,
            description="Feint attack followed by disengage")

        actions[ActionType.BEAT_DIRECT] = ActionProperties(
            name="Beat Direct",
            execution_time=0.35,
            base_success_rate=0.65,
            valid_distances={DistanceType.MEDIUM, DistanceType.LUNGE},
            vulnerable_to={
                DefenseType.DOUBLE_PARRY, DefenseType.CIRCLE_CHANGE
            },
            effective_against={DefenseType.PARRY_4, DefenseType.PARRY_6},
            preparation_required=True,
            priority=True,
            description="Beat opponent's blade followed by direct attack")

        actions[ActionType.TIME_THRUST] = ActionProperties(
            name="Time Thrust",
            execution_time=0.3,
            base_success_rate=0.6,
            valid_distances={DistanceType.MEDIUM, DistanceType.LUNGE},
            vulnerable_to={DefenseType.PARRY_4, DefenseType.PARRY_6},
            effective_against={DefenseType.COUNTER_SIXTE},
            preparation_required=False,
            priority=True,
            description="Counter-attack timed to opponent's action")

        actions[ActionType.POINT_IN_LINE] = ActionProperties(
            name="Point in Line",
            execution_time=0.2,
            base_success_rate=0.7,
            valid_distances={DistanceType.LONG, DistanceType.MEDIUM},
            vulnerable_to={DefenseType.PARRY_4, DefenseType.PARRY_6},
            effective_against={DefenseType.COUNTER_SIXTE},
            preparation_required=False,
            priority=True,
            description="Extended arm position to intercept opponent")

        actions[ActionType.BEAT] = ActionProperties(
            name="Beat",
            execution_time=0.2,
            base_success_rate=0.75,
            valid_distances={DistanceType.MEDIUM, DistanceType.LUNGE},
            vulnerable_to={DefenseType.PARRY_4, DefenseType.PARRY_6},
            effective_against={DefenseType.COUNTER_SIXTE},
            preparation_required=False,
            priority=True,
            description="Beat opponent's blade to create opening")

        actions[ActionType.PRESSURE] = ActionProperties(
            name="Pressure",
            execution_time=0.25,
            base_success_rate=0.7,
            valid_distances={DistanceType.MEDIUM, DistanceType.LUNGE},
            vulnerable_to={DefenseType.PARRY_4, DefenseType.PARRY_6},
            effective_against={DefenseType.COUNTER_SIXTE},
            preparation_required=False,
            priority=True,
            description="Apply pressure to opponent's blade")

        actions[ActionType.BIND] = ActionProperties(
            name="Bind",
            execution_time=0.3,
            base_success_rate=0.65,
            valid_distances={DistanceType.MEDIUM, DistanceType.LUNGE},
            vulnerable_to={DefenseType.PARRY_4, DefenseType.PARRY_6},
            effective_against={DefenseType.COUNTER_SIXTE},
            preparation_required=False,
            priority=True,
            description="Bind opponent's blade to control it")

        actions[ActionType.ENVELOPMENT] = ActionProperties(
            name="Envelopment",
            execution_time=0.35,
            base_success_rate=0.6,
            valid_distances={DistanceType.MEDIUM, DistanceType.LUNGE},
            vulnerable_to={DefenseType.PARRY_4, DefenseType.PARRY_6},
            effective_against={DefenseType.COUNTER_SIXTE},
            preparation_required=False,
            priority=True,
            description="Circular movement to control opponent's blade")

        return actions


class DefenseDatabase:
    """Central repository for all defense definitions and their properties"""

    @staticmethod
    def get_all_defenses() -> Dict[DefenseType, DefenseProperties]:
        defenses = {}

        # Simple Parries
        defenses[DefenseType.PARRY_1] = DefenseProperties(
            name="Prime",
            execution_time=0.2,
            base_success_rate=0.65,
            effective_against={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description="Low inside line parry")

        defenses[DefenseType.PARRY_2] = DefenseProperties(
            name="Seconde",
            execution_time=0.2,
            base_success_rate=0.65,
            effective_against={ActionType.DIRECT_THRUST, ActionType.CUT_OVER},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description="Low outside line parry")

        defenses[DefenseType.PARRY_3] = DefenseProperties(
            name="Tierce",
            execution_time=0.2,
            base_success_rate=0.65,
            effective_against={ActionType.DIRECT_THRUST, ActionType.CUT_OVER},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description="High outside line parry")

        defenses[DefenseType.PARRY_4] = DefenseProperties(
            name="Quarte",
            execution_time=0.2,
            base_success_rate=0.65,
            effective_against={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description="Inside high line parry")

        defenses[DefenseType.PARRY_5] = DefenseProperties(
            name="Quinte",
            execution_time=0.2,
            base_success_rate=0.65,
            effective_against={ActionType.DIRECT_THRUST, ActionType.CUT_OVER},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description="Head parry")

        defenses[DefenseType.PARRY_6] = DefenseProperties(
            name="Sixte",
            execution_time=0.2,
            base_success_rate=0.65,
            effective_against={ActionType.DIRECT_THRUST, ActionType.CUT_OVER},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description="Outside high line parry")

        defenses[DefenseType.PARRY_7] = DefenseProperties(
            name="Septime",
            execution_time=0.2,
            base_success_rate=0.65,
            effective_against={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description="Low inside line parry")

        defenses[DefenseType.PARRY_8] = DefenseProperties(
            name="Octave",
            execution_time=0.2,
            base_success_rate=0.65,
            effective_against={ActionType.DIRECT_THRUST, ActionType.CUT_OVER},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description="Low outside line parry")

        # Circular Parries
        defenses[DefenseType.COUNTER_SIXTE] = DefenseProperties(
            name="Counter of Sixte",
            execution_time=0.3,
            base_success_rate=0.6,
            effective_against={ActionType.DISENGAGE, ActionType.CUT_OVER},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description="Circular parry in high outside line")

        defenses[DefenseType.COUNTER_QUARTE] = DefenseProperties(
            name="Counter of Quarte",
            execution_time=0.3,
            base_success_rate=0.6,
            effective_against={ActionType.DISENGAGE, ActionType.CUT_OVER},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description="Circular parry in high inside line")

        defenses[DefenseType.COUNTER_SEPTIME] = DefenseProperties(
            name="Counter of Septime",
            execution_time=0.3,
            base_success_rate=0.6,
            effective_against={ActionType.DISENGAGE, ActionType.CUT_OVER},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description="Circular parry in low inside line")

        defenses[DefenseType.COUNTER_OCTAVE] = DefenseProperties(
            name="Counter of Octave",
            execution_time=0.3,
            base_success_rate=0.6,
            effective_against={ActionType.DISENGAGE, ActionType.CUT_OVER},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description="Circular parry in low outside line")

        # Semi-circular Parries
        defenses[DefenseType.SEMI_CIRCULAR_2_TO_6] = DefenseProperties(
            name="Semi-circular 2 to 6",
            execution_time=0.3,
            base_success_rate=0.6,
            effective_against={ActionType.DISENGAGE, ActionType.CUT_OVER},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description=
            "Semi-circular parry from low outside to high outside line")

        defenses[DefenseType.SEMI_CIRCULAR_4_TO_8] = DefenseProperties(
            name="Semi-circular 4 to 8",
            execution_time=0.3,
            base_success_rate=0.6,
            effective_against={ActionType.DISENGAGE, ActionType.CUT_OVER},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description=
            "Semi-circular parry from high inside to low outside line")

        defenses[DefenseType.SEMI_CIRCULAR_6_TO_7] = DefenseProperties(
            name="Semi-circular 6 to 7",
            execution_time=0.3,
            base_success_rate=0.6,
            effective_against={ActionType.DISENGAGE, ActionType.CUT_OVER},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description=
            "Semi-circular parry from high outside to low inside line")

        # Compound Parries
        defenses[DefenseType.DOUBLE_PARRY] = DefenseProperties(
            name="Double Parry",
            execution_time=0.4,
            base_success_rate=0.55,
            effective_against={
                ActionType.ONE_TWO, ActionType.DOUBLE_DISENGAGE
            },
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description="Two consecutive parries to counter compound attacks")

        defenses[DefenseType.CIRCLE_CHANGE] = DefenseProperties(
            name="Circle Change",
            execution_time=0.4,
            base_success_rate=0.55,
            effective_against={
                ActionType.ONE_TWO, ActionType.DOUBLE_DISENGAGE
            },
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description="Circular parry to counter compound attacks")

        defenses[DefenseType.BEAT_PARRY] = DefenseProperties(
            name="Beat Parry",
            execution_time=0.3,
            base_success_rate=0.6,
            effective_against={ActionType.BEAT, ActionType.PRESSURE},
            follow_up_actions={ActionType.DIRECT_THRUST, ActionType.DISENGAGE},
            description="Parry with a beat to counter blade actions")

        return defenses


class DistanceManager:
    """Manages distance relationships and valid actions"""

    @staticmethod
    def get_distance_properties() -> Dict[DistanceType, Dict]:
        return {
            DistanceType.OUT_OF_DISTANCE: {
                "range": (3.0, float('inf')),
                "valid_actions":
                {ActionType.ADVANCE, ActionType.BALANCE_BREAK},
                "preparation_allowed": True,
                "description": "Beyond attack distance"
            },
            DistanceType.LONG: {
                "range": (2.0, 3.0),
                "valid_actions": {
                    ActionType.ADVANCE, ActionType.RETREAT,
                    ActionType.POINT_IN_LINE
                },
                "preparation_allowed": True,
                "description": "Long preparation distance"
            },
            DistanceType.MEDIUM: {
                "range": (1.5, 2.0),
                "valid_actions": {
                    ActionType.ADVANCE, ActionType.RETREAT, ActionType.ONE_TWO,
                    ActionType.DOUBLE_DISENGAGE
                },
                "preparation_allowed": True,
                "description": "Standard engagement distance"
            },
            DistanceType.LUNGE: {
                "range": (1.0, 1.5),
                "valid_actions": {
                    ActionType.DIRECT_THRUST, ActionType.DISENGAGE,
                    ActionType.CUT_OVER, ActionType.COUNTER_DISENGAGE
                },
                "preparation_allowed": False,
                "description": "Lunge attack distance"
            },
            DistanceType.SHORT: {
                "range": (0.5, 1.0),
                "valid_actions": {
                    ActionType.DIRECT_THRUST, ActionType.DISENGAGE,
                    ActionType.CUT_OVER, ActionType.COUNTER_DISENGAGE
                },
                "preparation_allowed": False,
                "description": "Short attack distance"
            },
            DistanceType.INFIGHTING: {
                "range": (0.0, 0.5),
                "valid_actions": {ActionType.BEAT, ActionType.PRESSURE},
                "preparation_allowed": False,
                "description": "Infighting distance"
            }
        }


class FencingAction:
    """Represents a specific fencing action being executed"""

    def __init__(self, action_type: ActionType, fencer,
                 distance: DistanceType):
        self.action_type = action_type
        self.fencer = fencer
        self.properties = ActionDatabase.get_all_actions()[action_type]
        self.distance = distance

    def can_execute(self) -> bool:
        return (self.distance in self.properties.valid_distances
                and (not self.properties.preparation_required
                     or self.fencer.has_preparation))

    def get_success_probability(self, opponent_blade: BladePosition) -> float:
        base_prob = self.properties.base_success_rate * self.fencer.skill_level

        # Adjust based on distance
        if self.distance == DistanceType.LUNGE:
            base_prob *= 0.9

        # Adjust based on blade position
        if opponent_blade == BladePosition.SIXTE and self.action_type == ActionType.DISENGAGE:
            base_prob *= 1.2

        return min(base_prob, 1.0)


class Fencer:

    def __init__(self, name: str, skill_level: float = 0.5):
        self.name = name
        self.skill_level = skill_level
        self.score = 0
        self.blade_position = BladePosition.SIXTE
        self.has_preparation = False
        self.has_priority = False

        # Load action and defense databases
        self.available_actions = ActionDatabase.get_all_actions()
        self.available_defenses = DefenseDatabase.get_all_defenses()
        self.distance_properties = DistanceManager.get_distance_properties()

    def choose_action(
            self, distance: DistanceType,
            opponent_blade: BladePosition) -> Optional[FencingAction]:
        # Get valid actions for current distance from DistanceManager
        distance_props = self.distance_properties[distance]
        valid_action_types = distance_props["valid_actions"]

        if not valid_action_types:
            return None

        # Weight each action based on situation
        weighted_actions = []
        for action_type in valid_action_types:
            # Get properties for this action
            if action_type not in self.available_actions:
                continue

            action = FencingAction(action_type, self, distance)
            if action.can_execute():
                success_prob = action.get_success_probability(opponent_blade)
                weight = self._calculate_action_weight(action, success_prob)
                weighted_actions.append((weight, action))

        if not weighted_actions:
            return None

        # Sort by weight and add some randomness to selection
        weighted_actions.sort(reverse=True)
        top_actions = weighted_actions[:3]  # Consider top 3 actions
        weights = [w for w, _ in top_actions]
        actions = [a for _, a in top_actions]

        # Choose randomly from top actions based on weights
        if actions:
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]
            chosen_action = random.choices(actions,
                                           weights=normalized_weights,
                                           k=1)[0]
            return chosen_action

        return None

    def _calculate_action_weight(self, action: FencingAction,
                                 base_probability: float) -> float:
        weight = base_probability

        # Consider tactical factors
        if not self.has_priority and action.properties.priority:
            weight *= 1.2
        if self.has_preparation and action.properties.preparation_required:
            weight *= 1.1

        # Add distance considerations
        if self.distance_properties[action.distance]["preparation_allowed"]:
            weight *= 1.1

        # Add blade position considerations
        if action.action_type in [ActionType.DISENGAGE, ActionType.CUT_OVER] and \
           self.blade_position in [BladePosition.QUARTE, BladePosition.SIXTE]:
            weight *= 1.2

        return weight * random.uniform(0.95,
                                       1.05)  # Slightly reduced randomness


class FencingBout:

    def __init__(self, fencer1: Fencer, fencer2: Fencer):
        self.fencer1 = fencer1
        self.fencer2 = fencer2
        self.distance = DistanceType.MEDIUM  # Start at medium distance instead of out of distance
        self.current_fencer = fencer1
        self.opponent_fencer = fencer2
        self.rounds = 0

    def simulate_bout(self):
        while self.fencer1.score < 5 and self.fencer2.score < 5:  # Changed to 5 points for quicker bouts
            self.simulate_round()
            self.rounds += 1
            print(f"\nRound {self.rounds}")
            print(f"Distance: {self.distance.value}")
            print(
                f"{self.fencer1.name} {self.fencer1.score} - {self.fencer2.name} {self.fencer2.score}"
            )

        winner = self.fencer1 if self.fencer1.score >= 5 else self.fencer2
        print(f"\n{'='*40}")
        print(f"The winner is {winner.name} with a score of {winner.score}")
        print(f"Bout completed in {self.rounds} rounds")
        print(f"{'='*40}")

    def simulate_round(self):
        # Update distance randomly based on current state
        self._update_distance()

        # Get action from current fencer
        action = self.current_fencer.choose_action(
            self.distance, self.opponent_fencer.blade_position)

        if action:
            # Calculate success probability with distance modifier
            success_prob = self._calculate_modified_success_probability(action)
            roll = random.random()

            print(
                f"{self.current_fencer.name} attempts {action.action_type.value}"
            )
            print(f"Success Probability: {success_prob:.2f}, Roll: {roll:.2f}")

            if roll <= success_prob:
                self.current_fencer.score += 1
                self.log_action(success=True, action=action)
            else:
                self.log_action(success=False, action=action)
        else:
            print(
                f"{self.current_fencer.name} unable to find valid action at {self.distance.value}"
            )

        # Swap fencers
        self.current_fencer, self.opponent_fencer = self.opponent_fencer, self.current_fencer

    def _update_distance(self):
        # Define possible distance transitions
        distance_transitions = {
            DistanceType.OUT_OF_DISTANCE: [DistanceType.LONG],
            DistanceType.LONG:
            [DistanceType.OUT_OF_DISTANCE, DistanceType.MEDIUM],
            DistanceType.MEDIUM: [DistanceType.LONG, DistanceType.LUNGE],
            DistanceType.LUNGE: [DistanceType.MEDIUM, DistanceType.SHORT],
            DistanceType.SHORT: [DistanceType.LUNGE, DistanceType.INFIGHTING],
            DistanceType.INFIGHTING: [DistanceType.SHORT]
        }

        # 30% chance to change distance each round
        if random.random() < 0.3:
            possible_distances = distance_transitions[self.distance]
            self.distance = random.choice(possible_distances)

    def _calculate_modified_success_probability(
            self, action: FencingAction) -> float:
        base_prob = action.get_success_probability(
            self.opponent_fencer.blade_position)

        # Modify based on distance
        distance_modifiers = {
            DistanceType.OUT_OF_DISTANCE: 0.1,
            DistanceType.LONG: 0.5,
            DistanceType.MEDIUM: 1.0,
            DistanceType.LUNGE: 0.9,
            DistanceType.SHORT: 0.8,
            DistanceType.INFIGHTING: 0.7
        }

        return min(base_prob * distance_modifiers[self.distance], 1.0)

    def log_action(self, success: bool, action: FencingAction):
        status = "scores" if success else "misses"
        print(
            f"{self.current_fencer.name} {status} with {action.action_type.value}"
        )
        print(
            f"Current Score: {self.fencer1.name} {self.fencer1.score} - {self.fencer2.name} {self.fencer2.score}"
        )
        print('-' * 40)


class BoutPresenter:
    """Handles the visual presentation of the fencing bout"""

    PISTE_WIDTH = 60

    # ASCII Art representations
    FENCER_RIGHT = "⚔️>}"
    FENCER_LEFT = "{<⚔️"
    PISTE_LINE = "─"

    # Color schemes
    COLORS = {
        'title': Fore.CYAN,
        'score': Fore.YELLOW,
        'success': Fore.GREEN,
        'failure': Fore.RED,
        'info': Fore.WHITE,
        'distance': Fore.MAGENTA,
        'piste': Fore.BLUE,
        'reset': Style.RESET_ALL
    }

    def __init__(self):
        init()  # Initialize colorama
        self.bout_log = []
        self._clear_screen()

    def _clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def draw_piste(self, distance: DistanceType, fencer1_name: str,
                   fencer2_name: str):
        """Draws an ASCII representation of the piste with fencers"""
        # Calculate fencer positions based on distance
        distance_spacing = {
            DistanceType.OUT_OF_DISTANCE: 40,
            DistanceType.LONG: 30,
            DistanceType.MEDIUM: 20,
            DistanceType.LUNGE: 15,
            DistanceType.SHORT: 10,
            DistanceType.INFIGHTING: 5
        }

        spacing = distance_spacing[distance]
        total_width = self.PISTE_WIDTH

        # Create the piste line
        piste = f"{self.COLORS['piste']}{self.PISTE_LINE * total_width}{self.COLORS['reset']}"

        # Add fencers to the piste
        left_pos = (total_width - spacing) // 2
        right_pos = (total_width + spacing) // 2

        fencer_line = " " * left_pos + self.FENCER_LEFT + " " * (
            spacing - 3) + self.FENCER_RIGHT

        # Print the visualization
        print("\n" + "═" * total_width)
        print(
            f"{self.COLORS['info']}{fencer1_name:<25} VS {fencer2_name:>25}{self.COLORS['reset']}"
        )
        print(piste)
        print(fencer_line)
        print(piste)
        print("═" * total_width + "\n")

    def show_bout_header(self, fencer1: Fencer, fencer2: Fencer,
                         points_to_win: int):
        """Displays the bout header with fencer information"""
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"{self.COLORS['title']}{'='*60}")
        print(f"FENCING BOUT - {current_time}")
        print(f"{'='*60}{self.COLORS['reset']}\n")

        print(
            f"{self.COLORS['info']}Fencer 1: {fencer1.name} (Skill: {fencer1.skill_level:.2f})"
        )
        print(f"Fencer 2: {fencer2.name} (Skill: {fencer2.skill_level:.2f})")
        print(f"Points to win: {points_to_win}{self.COLORS['reset']}\n")

    def show_score(self, fencer1: Fencer, fencer2: Fencer):
        """Displays the current score"""
        print(f"\n{self.COLORS['score']}SCORE:")
        print(
            f"{fencer1.name}: {'●' * fencer1.score}{'○' * (5 - fencer1.score)} [{fencer1.score}]"
        )
        print(
            f"{fencer2.name}: {'●' * fencer2.score}{'○' * (5 - fencer2.score)} [{fencer2.score}]"
        )
        print(f"{self.COLORS['reset']}")

    def show_action(self, fencer: Fencer, action: FencingAction, success: bool,
                    probability: float, roll: float):
        """Displays the current action and its result"""
        result_color = self.COLORS['success'] if success else self.COLORS[
            'failure']
        result_text = "SCORES!" if success else "MISSES..."

        print(
            f"{self.COLORS['info']}{fencer.name} attempts {action.action_type.value}"
        )
        print(f"Probability: {probability:.2f} | Roll: {roll:.2f}")
        print(f"{result_color}{result_text}{self.COLORS['reset']}")

        # Add to bout log
        self.bout_log.append({
            'time': datetime.now().strftime("%H:%M:%S"),
            'fencer': fencer.name,
            'action': action.action_type.value,
            'success': success,
            'probability': probability
        })

    def show_distance_change(self, old_distance: DistanceType,
                             new_distance: DistanceType):
        """Displays distance changes"""
        if old_distance != new_distance:
            print(
                f"\n{self.COLORS['distance']}Distance changed: {old_distance.value} → {new_distance.value}{self.COLORS['reset']}"
            )

    def show_bout_summary(self, winner: Fencer, rounds: int, duration: float):
        """Displays the bout summary with statistics"""
        self._clear_screen()
        print(f"{self.COLORS['title']}{'='*60}")
        print("BOUT SUMMARY")
        print(f"{'='*60}{self.COLORS['reset']}\n")

        print(f"{self.COLORS['success']}Winner: {winner.name}")
        print(f"{self.COLORS['info']}Total Rounds: {rounds}")
        print(f"Duration: {duration:.1f} seconds")

        # Calculate statistics
        action_counts = {}
        success_rates = {}

        for entry in self.bout_log:
            action = entry['action']
            if action not in action_counts:
                action_counts[action] = {'total': 0, 'success': 0}
            action_counts[action]['total'] += 1
            if entry['success']:
                action_counts[action]['success'] += 1

        print(
            f"\n{self.COLORS['title']}Action Statistics:{self.COLORS['reset']}"
        )
        for action, counts in action_counts.items():
            success_rate = (counts['success'] / counts['total']) * 100
            print(
                f"{action:20}: {counts['success']}/{counts['total']} ({success_rate:.1f}% success)"
            )

        print(f"{self.COLORS['reset']}\n{'='*60}")


class EnhancedFencingBout(FencingBout):
    """Enhanced version of FencingBout with better presentation"""

    def __init__(self,
                 fencer1: Fencer,
                 fencer2: Fencer,
                 points_to_win: int = 5):
        super().__init__(fencer1, fencer2)
        self.points_to_win = points_to_win
        self.presenter = BoutPresenter()
        self.start_time = time.time()

    def simulate_bout(self):
        self.presenter.show_bout_header(self.fencer1, self.fencer2,
                                        self.points_to_win)
        time.sleep(2)

        while self.fencer1.score < self.points_to_win and self.fencer2.score < self.points_to_win:
            self.presenter._clear_screen()
            self.simulate_round()
            self.presenter.show_score(self.fencer1, self.fencer2)
            time.sleep(1)

        winner = self.fencer1 if self.fencer1.score >= self.points_to_win else self.fencer2
        duration = time.time() - self.start_time
        self.presenter.show_bout_summary(winner, self.rounds, duration)

    def simulate_round(self):
        old_distance = self.distance
        self._update_distance()
        self.presenter.show_distance_change(old_distance, self.distance)

        self.presenter.draw_piste(self.distance, self.current_fencer.name,
                                  self.opponent_fencer.name)

        action = self.current_fencer.choose_action(
            self.distance, self.opponent_fencer.blade_position)

        if action:
            success_prob = self._calculate_modified_success_probability(action)
            roll = random.random()

            success = roll <= success_prob
            self.presenter.show_action(self.current_fencer, action, success,
                                       success_prob, roll)

            if success:
                self.current_fencer.score += 1

            time.sleep(1)
        else:
            print(f"{self.current_fencer.name} repositioning...")
            time.sleep(0.5)

        self.rounds += 1
        self.current_fencer, self.opponent_fencer = self.opponent_fencer, self.current_fencer


def main():
    # Create fencers with different skill levels
    fencer1 = Fencer("🤺 Alice", skill_level=0.7)
    fencer2 = Fencer("🤺 Bob", skill_level=0.6)

    bout = EnhancedFencingBout(fencer1, fencer2, points_to_win=5)
    bout.simulate_bout()


if __name__ == "__main__":
    main()
