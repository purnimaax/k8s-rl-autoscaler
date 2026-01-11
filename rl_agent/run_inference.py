from stable_baselines3 import PPO
from custom_env import K8sEnv
import time

# 1. Load the Environment
env = K8sEnv()

# 2. Load the Trained Brain
# We use the zip file you just created
model = PPO.load("k8s_autoscaler_agent")

print("---------------------------------------")
print("AI AGENT ACTIVATED: Monitoring Cluster...")
print("---------------------------------------")

obs, _ = env.reset()

# Run forever
while True:
    # Ask the AI what to do based on current observation
    action, _states = model.predict(obs)
    
    # Execute the action
    obs, rewards, terminated, truncated, info = env.step(action)
    
    # Print what's happening
    cpu = obs[0]
    replicas = info['replicas']
    
    # Translate Action to English
    action_name = ["Scale Down", "Hold", "Scale Up"][action]
    
    print(f"Current CPU: {cpu:.2f}% | Replicas: {replicas} | AI Decision: {action} ({action_name})")