from stable_baselines3 import PPO
from custom_env import K8sEnv
import time

# 1. Initialize the Custom Environment
print("Initializing Kubernetes Environment...")
env = K8sEnv()

# 2. Define the RL Model (PPO is a standard, robust algorithm)
model = PPO("MlpPolicy", env, verbose=1, n_steps=20, batch_size=20)

# 3. Train the Agent
print("---------------------------------------")
print("STARTING TRAINING: The agent will now mess with your cluster.")
print("Watch your K8s dashboard or 'kubectl get pods' to see it in action!")
print("---------------------------------------")

# We train for 50 timesteps (about 1-2 hours of simulation time for 1000, but faster here)
model.learn(total_timesteps=20)

# 4. Save the brain
model.save("k8s_autoscaler_agent")
print("Training Complete! Model saved.")