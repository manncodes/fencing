import subprocess
import time
import webbrowser
import socket
import psutil
import os
from agent import FencingAgent
from websocket_fencing_env import WebSocketFencingEnv

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            return False
        except socket.error:
            return True

def kill_process_on_port(port):
    """Kill any process using the specified port"""
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    print(f"Killing process {proc.pid} using port {port}")
                    proc.kill()
                    time.sleep(1)
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def launch_server():
    """Launch the fencing server"""
    if is_port_in_use(8000):
        print("Port 8000 is in use. Attempting to kill existing process...")
        if not kill_process_on_port(8000):
            print("Could not free up port 8000. Please check running processes.")
            return None
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, 'render', 'fencing_server.py')
    
    try:
        process = subprocess.Popen(['python', server_path])
        time.sleep(2)  # Give server time to start
        return process
    except Exception as e:
        print(f"Error launching server: {e}")
        return None

def train_fencing_agents(num_episodes=1000, max_steps=1000, render=True):
    print("Launching server...")
    server_process = launch_server()
    
    if not server_process:
        print("Failed to launch server. Exiting...")
        return None, None
    
    try:
        if render:
            print("Opening simulator in browser...")
            webbrowser.open('http://localhost:8000')
            input("Press Enter when simulator is loaded...")
        
        # Create environments for both agents
        print("Creating environments...")
        left_env = WebSocketFencingEnv(controlled_fencer='left')
        right_env = WebSocketFencingEnv(controlled_fencer='right')
        
        # Create both agents
        print("Initializing agents...")
        left_agent = FencingAgent(
            state_dim=left_env.observation_space.shape[0],
            action_dim=left_env.action_space.n
        )
        right_agent = FencingAgent(
            state_dim=right_env.observation_space.shape[0],
            action_dim=right_env.action_space.n
        )
        
        # Training metrics
        episode_rewards = {'left': [], 'right': []}
        moving_avg_rewards = {'left': 0, 'right': 0}
        
        # Training loop
        for episode in range(num_episodes):
            print(f"\nEpisode {episode + 1}/{num_episodes}")
            
            # Reset both environments
            left_state = left_env.reset()
            right_state = right_env.reset()
            
            episode_reward = {'left': 0, 'right': 0}
            steps = 0
            episode_hits = {'left': 0, 'right': 0}
            
            while steps < max_steps:
                # Get actions from both agents
                left_action = left_agent.select_action(left_state)
                right_action = right_agent.select_action(right_state)
                
                # Execute actions
                left_next_state, left_reward, left_done, left_info = left_env.step(left_action)
                right_next_state, right_reward, right_done, right_info = right_env.step(right_action)
                
                # Store experiences
                left_agent.store_experience(left_state, left_action, left_reward, left_next_state, left_done)
                right_agent.store_experience(right_state, right_action, right_reward, right_next_state, right_done)
                
                # Train both agents
                left_loss = left_agent.train()
                right_loss = right_agent.train()
                
                # Check for hits
                if '_calculate_reward' in left_info and left_info['_calculate_reward'][1]:
                    print(f"\n🎯 LEFT AGENT scored at step {steps}!")
                    episode_hits['left'] += 1
                if '_calculate_reward' in right_info and right_info['_calculate_reward'][1]:
                    print(f"\n🎯 RIGHT AGENT scored at step {steps}!")
                    episode_hits['right'] += 1
                
                # Update states and rewards
                left_state = left_next_state
                right_state = right_next_state
                episode_reward['left'] += left_reward
                episode_reward['right'] += right_reward
                
                steps += 1
                
                # Optional delay for visualization
                if render:
                    time.sleep(0.1)
                
                # End episode if either agent is done
                if left_done or right_done:
                    break
            
            # Update target networks periodically
            if episode % 10 == 0:
                left_agent.update_target_network()
                right_agent.update_target_network()
            
            # Store and print metrics
            for side in ['left', 'right']:
                episode_rewards[side].append(episode_reward[side])
                moving_avg_rewards[side] = sum(episode_rewards[side][-100:]) / min(len(episode_rewards[side]), 100)
            
            print(f"\nEpisode Summary:")
            print(f"Steps completed: {steps}")
            print(f"Hits - Left: {episode_hits['left']}, Right: {episode_hits['right']}")
            print(f"\nLeft Agent:")
            print(f"Episode reward: {episode_reward['left']:.2f}")
            print(f"Moving avg reward: {moving_avg_rewards['left']:.2f}")
            print(f"Epsilon: {left_agent.epsilon:.3f}")
            print(f"\nRight Agent:")
            print(f"Episode reward: {episode_reward['right']:.2f}")
            print(f"Moving avg reward: {moving_avg_rewards['right']:.2f}")
            print(f"Epsilon: {right_agent.epsilon:.3f}")
            
            # Save models periodically
            if episode % 100 == 0:
                os.makedirs('models', exist_ok=True)
                left_agent.save(f'models/left_agent_episode_{episode}.pth')
                right_agent.save(f'models/right_agent_episode_{episode}.pth')
    
    except KeyboardInterrupt:
        print("\nTraining interrupted by user")
    
    finally:
        # Cleanup
        print("\nCleaning up...")
        left_env.close()
        right_env.close()
        if server_process:
            server_process.terminate()
            server_process.wait()
        
    return (left_agent, right_agent), (episode_rewards['left'], episode_rewards['right'])

if __name__ == "__main__":
    # Train both agents
    agents, rewards = train_fencing_agents(
        num_episodes=1000,
        max_steps=8,
        render=True
    )