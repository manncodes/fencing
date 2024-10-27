# Fencing Simulator Architecture

## System Architecture Diagram

```mermaid
flowchart TB
    subgraph Core ["Core Components"]
        FencingBout --> Fencer
        Fencer --> FencingAction
        FencingAction --> ActionProperties
    end

    subgraph Data ["Data Management"]
        ActionDatabase --> ActionProperties
        DefenseDatabase --> DefenseProperties
        DistanceManager
    end

    subgraph Presentation ["Presentation Layer"]
        EnhancedFencingBout --> BoutPresenter
        EnhancedFencingBout --> FencingBout
    end

    subgraph Enums ["Enumerations"]
        DistanceType
        ActionType
        DefenseType
        BladePosition
    end

    Fencer --> ActionDatabase
    Fencer --> DefenseDatabase
    Fencer --> DistanceManager
    FencingBout --> DistanceType
    FencingAction --> ActionType
    ActionProperties --> DefenseType
    Fencer --> BladePosition

    style Core fill:#f9f,stroke:#333,stroke-width:4px
    style Data fill:#bbf,stroke:#333,stroke-width:4px
    style Presentation fill:#bfb,stroke:#333,stroke-width:4px
    style Enums fill:#fbb,stroke:#333,stroke-width:4px
```

## Class Diagram

```mermaid
classDiagram
    class FencingBout {
        -Fencer fencer1
        -Fencer fencer2
        -DistanceType distance
        -Fencer current_fencer
        -Fencer opponent_fencer
        +simulate_bout()
        +simulate_round()
        -_update_distance()
        -_calculate_modified_success_probability()
    }

    class EnhancedFencingBout {
        -BoutPresenter presenter
        -float start_time
        -int points_to_win
        +simulate_bout()
        +simulate_round()
    }

    class BoutPresenter {
        -list bout_log
        +draw_piste()
        +show_bout_header()
        +show_score()
        +show_action()
        +show_distance_change()
        +show_bout_summary()
    }

    class Fencer {
        -string name
        -float skill_level
        -int score
        -BladePosition blade_position
        -bool has_preparation
        -bool has_priority
        -Dict available_actions
        -Dict available_defenses
        +choose_action()
        -_calculate_action_weight()
    }

    class FencingAction {
        -ActionType action_type
        -Fencer fencer
        -ActionProperties properties
        -DistanceType distance
        +can_execute()
        +get_success_probability()
    }

    class ActionDatabase {
        +get_all_actions()
    }

    class DefenseDatabase {
        +get_all_defenses()
    }

    class DistanceManager {
        +get_distance_properties()
    }

    FencingBout *-- Fencer
    EnhancedFencingBout --|> FencingBout
    EnhancedFencingBout *-- BoutPresenter
    Fencer *-- FencingAction
    Fencer ..> ActionDatabase
    Fencer ..> DefenseDatabase
    Fencer ..> DistanceManager
    FencingAction ..> ActionProperties
    ActionDatabase ..> ActionProperties
    DefenseDatabase ..> DefenseProperties
```

## Component Descriptions

### Core Components
- **FencingBout**: Main simulation controller
- **Fencer**: Represents a fencer with their properties and actions
- **FencingAction**: Represents specific fencing actions and their execution

### Data Management
- **ActionDatabase**: Repository of all possible actions
- **DefenseDatabase**: Repository of all possible defenses
- **DistanceManager**: Manages distance relationships and valid actions

### Presentation Layer
- **EnhancedFencingBout**: Extends FencingBout with visual presentation
- **BoutPresenter**: Handles visual output and statistics

### Enumerations
- **DistanceType**: Possible distances between fencers
- **ActionType**: Types of actions available
- **DefenseType**: Types of defenses available
- **BladePosition**: Possible blade positions

## Directory Structure
TODO: Update and modularize directory structure
```
fencing_simulator/
├── README.md
├── ARCHITECTURE.md
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── bout.py
│   │   ├── fencer.py
│   │   └── action.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── action_database.py
│   │   ├── defense_database.py
│   │   └── distance_manager.py
│   └── presentation/
│       ├── __init__.py
│       ├── enhanced_bout.py
│       └── presenter.py
└── tests/
    ├── __init__.py
    ├── test_bout.py
    ├── test_fencer.py
    └── test_action.py
```