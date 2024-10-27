import asyncio
import websockets
import json
import random
from sim import EnhancedFencingBout, Fencer, DistanceManager, ActionDatabase, DistanceType


class ActionHistory:

    def __init__(self):
        self.actions = []
        self.max_history = 20

    def add_action(self, action_str):
        self.actions.append(action_str)
        if len(self.actions) > self.max_history:
            self.actions.pop(0)


def get_valid_actions(fencer, distance):
    """Get all valid actions for current distance with their properties"""
    distance_props = fencer.distance_properties[distance]
    valid_actions = []

    for action_type in distance_props["valid_actions"]:
        if action_type in fencer.available_actions:
            action_props = fencer.available_actions[action_type]
            valid_actions.append({
                'name': action_props.name,
                'execution_time': action_props.execution_time,
                'success_rate': action_props.base_success_rate,
                'preparation_required': action_props.preparation_required,
                'description': action_props.description
            })

    return valid_actions


def get_distance_transitions(distance: DistanceType):
    """Get possible distance transitions"""
    transitions = {
        DistanceType.OUT_OF_DISTANCE: [DistanceType.LONG],
        DistanceType.LONG: [DistanceType.OUT_OF_DISTANCE, DistanceType.MEDIUM],
        DistanceType.MEDIUM: [DistanceType.LONG, DistanceType.LUNGE],
        DistanceType.LUNGE: [DistanceType.MEDIUM, DistanceType.SHORT],
        DistanceType.SHORT: [DistanceType.LUNGE, DistanceType.INFIGHTING],
        DistanceType.INFIGHTING: [DistanceType.SHORT]
    }
    return [t.name for t in transitions[distance]]


async def send_bout_state(websocket,
                          bout,
                          history,
                          current_action=None,
                          action_details=None):
    """Send enhanced bout state to the websocket client"""
    distance_manager = DistanceManager()
    distance_props = distance_manager.get_distance_properties()[bout.distance]

    state = {
        'distance': bout.distance.name,
        'fencer1': {
            'name': bout.fencer1.name,
            'score': bout.fencer1.score,
            'blade_position': bout.fencer1.blade_position.name,
            'has_priority': bout.fencer1.has_priority,
            'has_preparation': bout.fencer1.has_preparation,
            'skill_level': bout.fencer1.skill_level,
            'valid_actions': get_valid_actions(bout.fencer1, bout.distance)
        },
        'fencer2': {
            'name': bout.fencer2.name,
            'score': bout.fencer2.score,
            'blade_position': bout.fencer2.blade_position.name,
            'has_priority': bout.fencer2.has_priority,
            'has_preparation': bout.fencer2.has_preparation,
            'skill_level': bout.fencer2.skill_level,
            'valid_actions': get_valid_actions(bout.fencer2, bout.distance)
        },
        'current_action':
        current_action.action_type.value if current_action else None,
        'last_action_details': action_details if action_details else {},
        'rounds': bout.rounds,
        'action_history': history.actions,
        'distance_info': {
            'description': distance_props['description'],
            'range':
            list(distance_props['range']),  # Convert tuple to list for JSON
            'preparation_allowed': distance_props['preparation_allowed'],
            'possible_transitions': get_distance_transitions(bout.distance)
        }
    }

    try:
        await websocket.send(json.dumps(state))
        print(
            f"Sent state update - Round: {bout.rounds}, Distance: {bout.distance.name}"
        )
    except Exception as e:
        print(f"Error sending state: {e}")


async def handle_client(websocket, path):
    """Handle individual client connection"""
    print("New client connected")
    try:
        fencer1 = Fencer("🤺 Alice", skill_level=0.7)
        fencer2 = Fencer("🤺 Bob", skill_level=0.6)
        bout = EnhancedFencingBout(fencer1, fencer2)
        history = ActionHistory()

        # Define distance modifiers (from FencingBout._calculate_modified_success_probability)
        distance_modifiers = {
            DistanceType.OUT_OF_DISTANCE: 0.1,
            DistanceType.LONG: 0.5,
            DistanceType.MEDIUM: 1.0,
            DistanceType.LUNGE: 0.9,
            DistanceType.SHORT: 0.8,
            DistanceType.INFIGHTING: 0.7
        }

        while True:
            # Update bout state
            old_distance = bout.distance

            # Simulate one round and get the action
            action = bout.current_fencer.choose_action(
                bout.distance, bout.opponent_fencer.blade_position)

            if action:
                success_prob = bout._calculate_modified_success_probability(
                    action)
                roll = random.random()
                success = roll <= success_prob

                action_details = {
                    'execution_time': action.properties.execution_time,
                    'success_rate': action.properties.base_success_rate,
                    'distance_modifier': distance_modifiers[
                        bout.distance],  # Use local distance_modifiers
                    'final_probability': success_prob,
                    'roll': roll,
                    'success': success
                }

                history.add_action(
                    f"Round {bout.rounds}: {bout.current_fencer.name} "
                    f"attempts {action.action_type.value} - "
                    f"{'SUCCESS' if success else 'MISS'}")

                if success:
                    bout.current_fencer.score += 1
            else:
                action_details = None
                history.add_action(f"Round {bout.rounds}: Repositioning")

            # Send update to client
            await send_bout_state(websocket, bout, history, action,
                                  action_details)

            # Update round and swap fencers
            bout.rounds += 1
            bout.current_fencer, bout.opponent_fencer = bout.opponent_fencer, bout.current_fencer

            # Update distance
            if random.random() < 0.3:  # 30% chance to change distance
                possible_distances = get_distance_transitions(bout.distance)
                if possible_distances:
                    bout.distance = DistanceType[random.choice(
                        possible_distances)]

            # Add delay between rounds
            await asyncio.sleep(1)

            # Check for win condition
            if bout.fencer1.score >= 5 or bout.fencer2.score >= 5:
                winner = bout.fencer1 if bout.fencer1.score >= 5 else bout.fencer2
                history.add_action(f"Bout ended - Winner: {winner.name}")
                await send_bout_state(websocket, bout, history)
                break

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    except Exception as e:
        print(f"Error in handle_client: {e}")
        print(f"Exception details: {str(e)}")


async def start_server():
    """Start the WebSocket server"""
    try:
        async with websockets.serve(handle_client, "localhost", 8765):
            print("WebSocket server started on ws://localhost:8765")
            await asyncio.Future()  # run forever
    except Exception as e:
        print(f"Error starting server: {e}")


def run_server():
    """Run the server"""
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")


if __name__ == "__main__":
    run_server()
