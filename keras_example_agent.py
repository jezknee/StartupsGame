
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1' 

import keras
from keras import layers, ops
import gymnasium as gym
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from collections import deque
import time

import startups_AI_game as sg 
import startups_RL_environment as sr

# Configuration parameters for the whole setup
seed = 42
gamma = 0.99  # Discount factor for past rewards
epsilon = 1.0  # Epsilon greedy parameter
epsilon_min = 0.1  # Minimum epsilon greedy parameter
epsilon_max = 1.0  # Maximum epsilon greedy parameter
epsilon_interval = (
    epsilon_max - epsilon_min
)  # Rate at which to reduce chance of random action being taken
batch_size = 32  # Size of batch taken from replay buffer
max_steps_per_episode = 10000
max_episodes = 10  # Limit training episodes, will run until solved if smaller than 1

default_companies = [["Giraffe Beer", 5],["Bowwow Games",6],["Flamingo Soft",7],["Octo Coffee", 8],["Hippo Powertech", 9],["Elephant Mars Travel", 10]]
player_actions_pick_up = ["pickup_deck", "pickup_market"]
player_actions_put_down = ["putdown_shares", "putdown_market"]

env = sr.StartupsEnv(total_players=4, num_humans=0, default_company_list=default_companies)
print(f"Environment created successfully. Action space: {env.action_space}, Observation space: {env.observation_space}")

num_actions = 4

def create_q_model():
    """Network defined by the Deepmind paper - modernized version"""
    return keras.Sequential([
        # Use explicit Input layer instead of input_shape parameter
        layers.Input(shape=(4, 84, 84)),
        
        # Transpose from (batch, channels, height, width) to (batch, height, width, channels)
        layers.Lambda(
            lambda tensor: ops.transpose(tensor, [0, 2, 3, 1]),
            output_shape=(84, 84, 4)
        ),
        
        # Convolutions on the frames on the screen
        layers.Conv2D(32, 8, strides=4, activation="relu"),
        layers.Conv2D(64, 4, strides=2, activation="relu"),
        layers.Conv2D(64, 3, strides=1, activation="relu"),
        layers.Flatten(),
        layers.Dense(512, activation="relu"),
        layers.Dense(num_actions, activation="linear"),
    ])

# The first model makes the predictions for Q-values which are used to make an action
model = create_q_model()
# Build a target model for the prediction of future rewards
model_target = create_q_model()

# Compile models for better performance
model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.00025, clipnorm=1.0))
model_target.compile(optimizer=keras.optimizers.Adam(learning_rate=0.00025, clipnorm=1.0))

# Experience replay buffers
action_history = []
state_history = []
state_next_history = []
rewards_history = []
done_history = []
episode_reward_history = []
running_reward = 0
episode_count = 0
frame_count = 0

# Tracking and logging variables
episode_rewards = []  # Track reward for each episode
episode_lengths = []  # Track length of each episode
episode_losses = []   # Track average loss per episode
recent_rewards = deque(maxlen=100)  # For running average
recent_10_rewards = deque(maxlen=10)  # For last 10 episodes average
training_start_time = time.time()
episode_start_time = time.time()

# Logging intervals
log_interval = 1  # Log every episode
plot_interval = 10  # Update plots every 10 episodes

# Number of frames to take random action and observe output
epsilon_random_frames = 50000
# Number of frames for exploration
epsilon_greedy_frames = 1000000.0
# Maximum replay length
max_memory_length = 100000
# Train the model after 4 actions
update_after_actions = 4
# How often to update the target network
update_target_network = 10000
# Using huber loss for stability
loss_function = keras.losses.Huber()

# Set random seeds for reproducibility
np.random.seed(seed)
tf.random.set_seed(seed)

def plot_training_progress(episode_rewards, recent_10_avg, recent_100_avg, episode_losses):
    """Plot training progress with multiple metrics"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Episode rewards
    ax1.plot(episode_rewards, alpha=0.3, color='blue', label='Episode Reward')
    if len(recent_10_avg) > 0:
        ax1.plot(recent_10_avg, color='red', linewidth=2, label='10-Episode Average')
    if len(recent_100_avg) > 0:
        ax1.plot(recent_100_avg, color='green', linewidth=2, label='100-Episode Average')
    ax1.set_xlabel('Episode')
    ax1.set_ylabel('Reward')
    ax1.set_title('Training Rewards Over Time')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Loss over time
    if len(episode_losses) > 0:
        ax2.plot(episode_losses, color='orange')
        ax2.set_xlabel('Episode')
        ax2.set_ylabel('Average Loss')
        ax2.set_title('Training Loss Over Time')
        ax2.grid(True, alpha=0.3)
    
    # Recent performance histogram
    if len(episode_rewards) > 0:
        recent_50 = episode_rewards[-50:] if len(episode_rewards) >= 50 else episode_rewards
        ax3.hist(recent_50, bins=20, alpha=0.7, color='purple')
        ax3.set_xlabel('Reward')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Recent Episode Rewards Distribution')
        ax3.grid(True, alpha=0.3)
    
    # Epsilon decay
    episodes = len(episode_rewards)
    if episodes > 0:
        epsilon_values = []
        temp_epsilon = epsilon_max
        for i in range(episodes):
            frames_so_far = i * (frame_count // max(episodes, 1))  # Approximate
            temp_epsilon -= epsilon_interval / epsilon_greedy_frames * frames_so_far
            temp_epsilon = max(temp_epsilon, epsilon_min)
            epsilon_values.append(temp_epsilon)
        
        ax4.plot(epsilon_values, color='red')
        ax4.set_xlabel('Episode')
        ax4.set_ylabel('Epsilon Value')
        ax4.set_title('Epsilon Decay Over Time')
        ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('training_progress.png', dpi=100, bbox_inches='tight')
    plt.show()
    plt.close()

def log_episode_stats(episode_num, reward, steps, epsilon_val, loss_avg, time_elapsed):
    """Log detailed episode statistics"""
    recent_10_avg = np.mean(list(recent_10_rewards)) if recent_10_rewards else 0
    recent_100_avg = np.mean(list(recent_rewards)) if recent_rewards else 0
    
    print(f"\n=== Episode {episode_num} Stats ===")
    print(f"Episode Reward: {reward:.2f}")
    print(f"Episode Length: {steps} steps")
    print(f"Epsilon: {epsilon_val:.4f}")
    print(f"Average Loss: {loss_avg:.6f}" if loss_avg > 0 else "Average Loss: N/A")
    print(f"Episode Time: {time_elapsed:.2f} seconds")
    print(f"Last 10 Episodes Avg: {recent_10_avg:.2f}")
    print(f"Last 100 Episodes Avg: {recent_100_avg:.2f}")
    print(f"Total Frames: {frame_count}")
    print("=" * 30)

while True:
    observation, _ = env.reset()
    state = np.array(observation)
    episode_reward = 0
    episode_loss = []
    episode_start_time = time.time()

    for timestep in range(1, max_steps_per_episode):
        frame_count += 1

        # Use epsilon-greedy for exploration
        if frame_count < epsilon_random_frames or epsilon > np.random.rand():
            # Take random action
            action = np.random.choice(num_actions)
        else:
            # Predict action Q-values from environment state
            state_tensor = ops.convert_to_tensor(state)
            state_tensor = ops.expand_dims(state_tensor, 0)
            action_probs = model(state_tensor, training=False)
            # Take best action
            action = int(ops.argmax(action_probs[0]))

        # Decay probability of taking random action
        epsilon -= epsilon_interval / epsilon_greedy_frames
        epsilon = max(epsilon, epsilon_min)

        # Apply the sampled action in our environment
        state_next, reward, done, _, _ = env.step(action)
        state_next = np.array(state_next)

        episode_reward += reward

        # Save actions and states in replay buffer
        action_history.append(action)
        state_history.append(state)
        state_next_history.append(state_next)
        done_history.append(done)
        rewards_history.append(reward)
        state = state_next

        # Update every fourth frame and once batch size is over 32
        if frame_count % update_after_actions == 0 and len(done_history) > batch_size:
            # Get indices of samples for replay buffers
            indices = np.random.choice(range(len(done_history)), size=batch_size)

            # Using list comprehension to sample from replay buffer
            state_sample = np.array([state_history[i] for i in indices])
            state_next_sample = np.array([state_next_history[i] for i in indices])
            rewards_sample = np.array([rewards_history[i] for i in indices])
            action_sample = np.array([action_history[i] for i in indices])
            done_sample = ops.convert_to_tensor(
                [float(done_history[i]) for i in indices]
            )

            # Build the updated Q-values for the sampled future states
            # Use the target model for stability
            future_rewards = model_target.predict(state_next_sample, verbose=0)
            # Q value = reward + discount factor * expected future reward
            updated_q_values = rewards_sample + gamma * ops.amax(
                future_rewards, axis=1
            )

            # If final frame set the last value to -1
            updated_q_values = updated_q_values * (1 - done_sample) - done_sample

            # Create a mask so we only calculate loss on the updated Q-values
            masks = ops.one_hot(action_sample, num_actions)

            with tf.GradientTape() as tape:
                # Train the model on the states and updated Q-values
                q_values = model(state_sample)

                # Apply the masks to the Q-values to get the Q-value for action taken
                q_action = ops.sum(ops.multiply(q_values, masks), axis=1)
                # Calculate loss between new Q-value and old Q-value
                loss = loss_function(updated_q_values, q_action)

            # Backpropagation
            grads = tape.gradient(loss, model.trainable_variables)
            model.optimizer.apply_gradients(zip(grads, model.trainable_variables))
            
            # Track loss for episode statistics
            episode_loss.append(float(loss))

        if frame_count % update_target_network == 0:
            # Update the target network with new weights
            model_target.set_weights(model.get_weights())
            # Log details
            template = "running reward: {:.2f} at episode {}, frame count {}"
            print(template.format(running_reward, episode_count, frame_count))

        # Limit the state and reward history
        if len(rewards_history) > max_memory_length:
            del rewards_history[:1]
            del state_history[:1]
            del state_next_history[:1]
            del action_history[:1]
            del done_history[:1]

        if done:
            break

    # Calculate episode statistics
    episode_time = time.time() - episode_start_time
    avg_loss = np.mean(episode_loss) if episode_loss else 0.0
    
    # Store episode metrics
    episode_rewards.append(episode_reward)
    episode_lengths.append(timestep)
    episode_losses.append(avg_loss)
    recent_rewards.append(episode_reward)
    recent_10_rewards.append(episode_reward)

    # Update running reward to check condition for solving
    episode_reward_history.append(episode_reward)
    if len(episode_reward_history) > 100:
        del episode_reward_history[:1]
    running_reward = np.mean(episode_reward_history)

    episode_count += 1
    
    # Log episode statistics
    if episode_count % log_interval == 0:
        log_episode_stats(episode_count, episode_reward, timestep, epsilon, avg_loss, episode_time)
    
    # Plot progress periodically
    if episode_count % plot_interval == 0 and episode_count > 0:
        recent_10_avg = [np.mean(list(recent_10_rewards)[:i+1]) for i in range(len(recent_10_rewards))]
        recent_100_avg = [np.mean(list(recent_rewards)[:i+1]) for i in range(len(recent_rewards))]
        plot_training_progress(episode_rewards, recent_10_avg, recent_100_avg, episode_losses)

    if running_reward > 40:  # Condition to consider the task solved
        print("Solved at episode {}!".format(episode_count))
        print(f"Final training time: {(time.time() - training_start_time)/60:.2f} minutes")
        # Final plot
        recent_10_avg = [np.mean(episode_rewards[max(0,i-9):i+1]) for i in range(len(episode_rewards))]
        recent_100_avg = [np.mean(episode_rewards[max(0,i-99):i+1]) for i in range(len(episode_rewards))]
        plot_training_progress(episode_rewards, recent_10_avg, recent_100_avg, episode_losses)
        break

    if (
        max_episodes > 0 and episode_count >= max_episodes
    ):  # Maximum number of episodes reached
        print("Stopped at episode {}!".format(episode_count))
        print(f"Total training time: {(time.time() - training_start_time)/60:.2f} minutes")
        # Final plot
        recent_10_avg = [np.mean(episode_rewards[max(0,i-9):i+1]) for i in range(len(episode_rewards))]
        recent_100_avg = [np.mean(episode_rewards[max(0,i-99):i+1]) for i in range(len(episode_rewards))]
        plot_training_progress(episode_rewards, recent_10_avg, recent_100_avg, episode_losses)
        break

# Print final statistics
print(f"\n=== Training Complete ===")
print(f"Total Episodes: {episode_count}")
print(f"Total Training Time: {(time.time() - training_start_time)/60:.2f} minutes")
print(f"Final Running Reward: {running_reward:.2f}")
if episode_rewards:
    print(f"Best Episode Reward: {max(episode_rewards):.2f}")
    print(f"Average Episode Length: {np.mean(episode_lengths):.1f} steps")
print("=" * 30)