from ai_agent import Agent 
import numpy as np
import gymnasium as gym 
import matplotlib.pyplot as plt
import traceback
import sys
import startups_AI_game as sg 
import startups_RL_environment as sr
import json
import time  # Add to imports at top
from datetime import datetime

def plotLearning(x, scores, eps_history, filename):
    print("Creating plot...")
    try:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot scores
        ax1.plot(x, scores, 'b-', alpha=0.7, label='Score')
        ax1.set_xlabel('Episode')
        ax1.set_ylabel('Score')
        ax1.set_title('Training Scores')
        ax1.grid(True)
        ax1.legend()
        
        # Plot epsilon values
        ax2.plot(x, eps_history, 'r-', alpha=0.7, label='Epsilon')
        ax2.set_xlabel('Episode')
        ax2.set_ylabel('Epsilon')
        ax2.set_title('Epsilon Decay')
        ax2.grid(True)
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Plot saved as {filename}")
        plt.show()
    except Exception as e:
        print(f"Error in plotting: {e}")
        traceback.print_exc()

print("Script starting...")

def save_game_history(episode_num, scores, player_list, company_list):
    """Save game results to a JSON file"""
    game_record = {
        "episode": episode_num,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "final_scores": {},
        "company_states": {}
    }
    
    # Record final scores for each player
    for player in player_list:
        game_record["final_scores"][player._name] = player._score
        
    # Record final company states
    for company in company_list:
        company_state = {
            "total_shares": company._total_shares,
            "share_distribution": {}
        }
        for player in player_list:
            share_count = sum(1 for share in player._shares if share._company == company._name)
            company_state["share_distribution"][player._name] = share_count
        game_record["company_states"][company._name] = company_state

    # Save to file
    filename = f"game_history/game_{episode_num}.json"
    os.makedirs("game_history", exist_ok=True)
    with open(filename, 'w') as f:
        json.dump(game_record, f, indent=2)
    print(f"Game {episode_num} history saved to {filename}")

def log_player_actions(player, action_type, action, phase):
    """Log player actions to a file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = (f"{timestamp} - Player: {player._name}, "
                f"Phase: {phase}, "
                f"Action: {action_type}, "
                f"Details: {action}\n")
    
    with open("player_actions.log", 'a') as f:
        f.write(log_entry)

def record_game_history(game_history, episode_num, score, runtime, player_list, company_list):
    """Add a game record to the running game history"""
    game_record = {
        "episode": episode_num,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "episode_score": score,
        "runtime_seconds": runtime,
    }
    
    # Record scores for each player
    for player in player_list:
        game_record[f"player_{player._name}_score"] = player._score
        
    # Record share distribution for each company
    for company in company_list:
        for player in player_list:
            share_count = sum(1 for share in player._shares if share._company == company._name)
            game_record[f"{company._name}_{player._name}_shares"] = share_count
    
    game_history.append(game_record)

def record_action(action_history, episode, step, player, phase, action_type, action):
    """Record a player action to the action history"""
    action_record = {
        "episode": episode,
        "step": step,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "player": player._name,
        "phase": str(phase),
        "action_type": action_type,
        "action": str(action)
    }
    action_history.append(action_record)

if __name__ == '__main__':
    print("Main block entered")
    default_companies = [["Giraffe Beer", 5],["Bowwow Games",6],["Flamingo Soft",7],["Octo Coffee", 8],["Hippo Powertech", 9],["Elephant Mars Travel", 10]]
    player_actions_pick_up = ["pickup_deck", "pickup_market"]
    player_actions_put_down = ["putdown_shares", "putdown_market"]
    
    try:
        print("Creating environment...")
        env = sr.StartupsEnv(total_players=4, num_humans=0, default_company_list=default_companies)
        print(f"Environment created successfully. Action space: {env.action_space}, Observation space: {env.observation_space}")
        
       
        print("Creating agent...")
        # make input_dims match the observation space without hardcoding
        agent = Agent(alpha=0.0005, gamma=0.99, n_actions=env.action_space.n, epsilon=1.0, batch_size=64, input_dims=env.observation_space.shape[0], epsilon_dec=0.996, epsilon_end=0.01, mem_size=1000000, fname='startup_model4.keras')
        print("Agent created successfully")

        scores = []
        eps_history = []
        num_episodes = 100

        game_history = []
        action_history = []

        for i in range(num_episodes):
            print(f"Starting episode {i}")
            done = False
            score = 0
            episode_start_time = time.time()
            
            try:
                observation, info = env.reset()
                print(f"Episode {i} - Initial observation shape: {observation.shape}")
            except Exception as e:
                print(f"Error during env.reset(): {e}")
                traceback.print_exc()
                continue
            
            step_count = 0
            rl_actions_taken = 0
            max_steps = 50

            while not done and step_count < max_steps:
                try:
                    current_phase = env.state_controller.get_current_phase()
                    print(f"Step {step_count}, Phase: {current_phase}")

                    if current_phase in (sr.TurnPhase.RL_PUTDOWN, sr.TurnPhase.RL_PICKUP):
                        action = agent.choose_action(observation, env)
                        print(f"RL agent choosing action {action}")
                        rl_actions_taken += 1

                        observation_, reward, terminated, truncated, info = env.step(action)
                        done = terminated or truncated
                        
                        if 'invalid_action' in info and info['invalid_action']:
                            print(f"Invalid action taken: {action}")

                        agent.remember(observation, action, reward, observation_, done)
                        observation = observation_
                        score += reward

                        if agent.memory.mem_cntr > agent.batch_size:
                            agent.learn()

                        print(f"Action {action}, Reward: {reward}, Score: {score}")
                        
                        record_action(action_history, i, step_count, env.agent_player, 
                                    current_phase, 
                                    "PICKUP" if current_phase == sr.TurnPhase.RL_PICKUP else "PUTDOWN",
                                    env.action_mapping[action])
                        
                    else:
                        # Not RL agent's turn - step anyway to advance game state
                        # Pass a dummy action (0) since other players will be handled internally
                        observation_, reward, terminated, truncated, info = env.step(0)
                        done = terminated or truncated
                        observation = observation_
                        print(f"Other players' turn, game state advanced")
                        
                        # Record non-RL player actions
                        for player in env.player_list:
                            if player != env.agent_player:
                                # Record pickup action
                                pickup_action = sg.pickup_strategy(player, env.market, env.deck, env.player_list)
                                if pickup_action:
                                    record_action(action_history, i, step_count, player,
                                                "OTHER_PLAYERS", "PICKUP", pickup_action)
                                
                                # Record putdown action
                                putdown_action = sg.putdown_strategy(player, env.market, env.deck, env.player_list)
                                if putdown_action:
                                    record_action(action_history, i, step_count, player,
                                                "OTHER_PLAYERS", "PUTDOWN", putdown_action)
                
                    step_count += 1
                        
                except Exception as e:
                    print(f"Error during step {step_count} of episode {i}: {e}")
                    traceback.print_exc()
                    break
            
            if step_count >= max_steps:
                print(f"Episode {i} exceeded {max_steps} steps, ending...")
        
            eps_history.append(agent.epsilon)
            scores.append(score)

            avg_score = np.mean(scores[max(0, i-100):i+1])
            print(f'episode {i}, score {score:.2f}, average score {avg_score:.2f}, epsilon {agent.epsilon:.3f}')
            
            if i % 100 == 0 and i > 0:
                try:
                    agent.save_model()
                    print(f"Model saved at episode {i}")
                except Exception as e:
                    print(f"Error saving model: {e}")

            episode_runtime = time.time() - episode_start_time
            record_game_history(game_history, i, score, episode_runtime, 
                              env.player_list, env.company_list)
        
        # Final model save
        try:
            agent.save_model()
            print("Final model saved")
        except Exception as e:
            print(f"Error saving final model: {e}")

        print("Training completed, creating plot...")
        filename = 'startups1000.png'
        x = [i+1 for i in range(len(scores))]
        plotLearning(x, scores, eps_history, filename)
        print("Script completed successfully")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        traceback.print_exc()
        sys.exit(1)

# After training completes, save both histories
print("Saving complete game and action histories...")
games_df = pd.DataFrame(game_history)
actions_df = pd.DataFrame(action_history)

games_df.to_csv('game_history.csv', index=False)
actions_df.to_csv('action_history.csv', index=False)
print(f"Saved {len(game_history)} episodes with {len(action_history)} total actions")

print("Script finished")