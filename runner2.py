
from ai_agent import Agent 
import numpy as np
import gymnasium as gym 
import matplotlib.pyplot as plt
import traceback
import sys
import s1_game_optimise_for_RL as sg 
import RL_environment2 as sr
import pandas as pd
from datetime import datetime
import time

#sys.stdout = open("C:\\Users\\jezkn\\OneDrive\\Documents\\Startups\\startups_output.txt", "w")   # overwrite each run

def plotLearning(x, scores, eps_history, filename):
    #print("Creating plot...")
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
        #print(f"Plot saved as {filename}")
        #plt.show()
    except Exception as e:
        #print(f"Error in plotting: {e}")
        traceback.print_exc()

#print("Script starting...")

learn_interval = 8  # Learn every 4 steps
global_step_count = 0  # Track total steps across all episodes

#import cProfile, pstats

#with cProfile.Profile() as pr:
    # call your main training function here

if __name__ == '__main__':
    #print("Main block entered")
    default_companies = [["Giraffe Beer", 5],["Bowwow Games",6],["Flamingo Soft",7],["Octo Coffee", 8],["Hippo Powertech", 9],["Elephant Mars Travel", 10]]
    player_actions_pick_up = ["pickup_deck", "pickup_market"]
    player_actions_put_down = ["putdown_shares", "putdown_market"]
    
    try:
        #print("Creating environment...")
        env = sr.StartupsEnv(total_players=4, num_humans=0, default_company_list=default_companies)
        #print(f"Environment created successfully. Action space: {env.action_space}, Observation space: {env.observation_space}")
        
    
        #print("Creating agent...")
        # make input_dims match the observation space without hardcoding
        agent = Agent(alpha=0.0001, gamma=0.99, n_actions=env.action_space.n, epsilon=1.0, batch_size=128, input_dims=env.observation_space.shape[0], epsilon_dec=0.9995, epsilon_end=0.05, mem_size=1000000, fname='C:\\Users\\jezkn\\OneDrive\\Documents\\Startups\\StartupsGame\\startup_modelqcheck2.keras')
        #print("Agent created successfully")
        initial_weights = agent.q_eval.get_weights()[0].copy()

        game_history = []
        action_history = []

        scores = []
        eps_history = []
        num_episodes = 50000

        for i in range(num_episodes):
            #print(f"Starting episode {i}")
            done = False
            score = 0
            episode_start_time = time.time()  # Add this line
            
            try:
                observation, info = env.reset()
                #print(f"Episode {i} - Initial observation shape: {observation.shape}")
            except Exception as e:
                #print(f"Error during env.reset(): {e}")
                traceback.print_exc()
                continue
            
            step_count = 0
            rl_actions_taken = 0
            max_steps = 50

            while not done and step_count < max_steps:
                try:
                    current_phase = env.state_controller.get_current_phase()
                    #print(f"Step {step_count}, Phase: {current_phase}")

                    if current_phase in (sr.TurnPhase.RL_PUTDOWN, sr.TurnPhase.RL_PICKUP):
                        action = agent.choose_action(observation, env)
                        #print(f"RL agent choosing action {action}")
                        rl_actions_taken += 1

                        observation_, reward, terminated, truncated, info = env.step(action)
                        done = terminated or truncated
                        
                        if 'invalid_action' in info and info['invalid_action']:
                            pass
                            #print(f"Invalid action taken: {action}")

                        agent.remember(observation, action, reward, observation_, done)
                        observation = observation_
                        score += reward

                        global_step_count += 1
                        if (global_step_count % learn_interval == 0 and 
                            agent.memory.mem_cntr > agent.batch_size):
                            agent.learn()

                        #print(f"Action {action}, Reward: {reward}, Score: {score}")
                        
                    else:
                        # Not RL agent's turn - step anyway to advance game state
                        # Pass a dummy action (0) since other players will be handled internally
                        observation_, reward, terminated, truncated, info = env.step(0)
                        done = terminated or truncated
                        observation = observation_
                        #print(f"Other players' turn, game state advanced")

                    step_count += 1
                        
                except Exception as e:
                    #print(f"Error during step {step_count} of episode {i}: {e}")
                    traceback.print_exc()
                    break
            
            if step_count >= max_steps:
                pass
                #print(f"Episode {i} exceeded {max_steps} steps, ending...")

            episode_runtime = time.time() - episode_start_time
            game_history.append({
                'episode': i,
                'score': score,
                'runtime': episode_runtime,
                'steps': step_count,
                'rl_actions': rl_actions_taken,
                'epsilon': agent.epsilon,
                'rl_rank': env._calculate_player_rank()+1,
                'rl_coins': env._get_coins_for_score()
            })
            eps_history.append(agent.epsilon)
            scores.append(score)
            """
            # collect states you saw in this episode
            states = np.array(episode_states)   # assuming you track them in a list
            if len(states) > 0:
                # (optional) sample states to avoid too many
                sampled_states = states if len(states) < 50 else np.array(random.sample(list(states), 50))

                q_values = agent.q_eval.predict(sampled_states, verbose=0)
                q_mean = float(np.mean(q_values))
                q_max = float(np.max(q_values))
                q_min = float(np.min(q_values))
                q_std = float(np.std(q_values))
            else:
                q_mean = q_max = q_min = q_std = 0.0

            # compute weight change magnitude if you're tracking that
            weight_change = np.linalg.norm(np.subtract(
                agent.q_eval.get_weights()[0].flatten(),
                prev_weights[0].flatten()
            )) if 'prev_weights' in locals() else 0.0
            prev_weights = agent.q_eval.get_weights()
            
            # add to your game history log
            game_history.append({
                "episode": episode,
                "weight_change": weight_change,
                "q_min": q_min,
                "q_max": q_max,
                "q_std": q_std,
                "epsilon": agent.epsilon,
                "memory_counter": agent.memory.mem_cntr,
                "reward": episode_reward   # if you're already tracking rewards
            })
            """
            avg_score = np.mean(scores[max(0, i-100):i+1])
            #print(f'episode {i}, score {score:.2f}, average score {avg_score:.2f}, epsilon {agent.epsilon:.3f}')
            
            if i % 100 == 0 and i > 0:
                try:
                    agent.save_model()
                    #print(f"Model saved at episode {i}")

                    current_weights = agent.q_eval.get_weights()[0]
                    weight_change = np.mean(np.abs(current_weights - initial_weights))
                    print(f"Episode {i}: Weight change magnitude: {weight_change:.6f}")
                    
                    # Check Q-values for a dummy state
                    dummy_state = np.zeros((1, env.observation_space.shape[0]))
                    q_values = agent.q_eval.predict(dummy_state, verbose=0)[0]
                    print(f"Q-values: min={q_values.min():.3f}, max={q_values.max():.3f}, std={q_values.std():.3f}")
                    print(f"Memory counter: {agent.memory.mem_cntr}, Epsilon: {agent.epsilon:.4f}")
                except Exception as e:
                    pass
                    #print(f"Error saving model: {e}")

        # Final model save
        try:
            agent.save_model()
            #print("Final model saved")
        except Exception as e:
            pass
            #print(f"Error saving final model: {e}")

        # After training loop, before plotting
        #print("Saving game history...")
        pd.DataFrame(game_history).to_csv('C:\\Users\\jezkn\\OneDrive\\Documents\\Startups\\game_history.csv', index=False)
        #print(f"Saved history for {len(game_history)} episodes")

        #print("Training completed, creating plot...")
        filename = 'C:\\Users\\jezkn\\OneDrive\\Documents\\Startups\\startups_plot.png'
        x = [i+1 for i in range(len(scores))]
        plotLearning(x, scores, eps_history, filename)
        #print("Script completed successfully")
        
    except Exception as e:
        #print(f"Error occurred: {e}")
        traceback.print_exc()
        sys.exit(1)

print("Script finished")

#stats = pstats.Stats(pr)
#stats.sort_stats("time").print_stats(20)  # top 20 slowest