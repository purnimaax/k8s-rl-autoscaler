import gymnasium as gym
from gymnasium import spaces
import numpy as np
import requests
import time
from kubernetes import client, config

class K8sEnv(gym.Env):
    """
    Custom Environment that follows gymnasium interface.
    It connects an RL Agent to a Kubernetes Cluster.
    """
    def __init__(self):
        super(K8sEnv, self).__init__()

        # Define Action Space: {0: Scale Down, 1: Hold, 2: Scale Up}
        self.action_space = spaces.Discrete(3)

        # Define Observation Space: [CPU Usage %]
        # We assume CPU usage will be between 0 and 200% (just a safe upper bound)
        self.observation_space = spaces.Box(low=0, high=200, shape=(1,), dtype=np.float32)

        # Connect to Kubernetes
        config.load_kube_config() # Uses your local .kube/config (Minikube)
        self.apps_v1 = client.AppsV1Api()
        self.deployment_name = "cpu-eater"
        self.namespace = "default"

        # Prometheus Config
        self.prometheus_url = "http://localhost:9090"

    def _get_replica_count(self):
        """Fetch current number of pods from K8s"""
        deployment = self.apps_v1.read_namespaced_deployment(self.deployment_name, self.namespace)
        return deployment.spec.replicas

    def _scale_deployment(self, replicas):
        """Send command to K8s to update replica count"""
        # Safety bounds: Don't go below 1 or above 10 pods
        replicas = max(1, min(10, replicas))
        
        body = {"spec": {"replicas": replicas}}
        self.apps_v1.patch_namespaced_deployment_scale(
            self.deployment_name, self.namespace, body
        )
        print(f" -> Scaling to {replicas} replicas...")

    def _get_cpu_usage(self):
        """Query Prometheus for the current CPU load"""
        # We query the average CPU usage over the last 1 minute
        query = 'avg(rate(container_cpu_usage_seconds_total{pod=~"cpu-eater.*"}[1m]))'
        try:
            response = requests.get(self.prometheus_url + '/api/v1/query', params={'query': query})
            result = response.json()['data']['result']
            if result:
                cpu_value = float(result[0]['value'][1])
                return cpu_value * 100  # Convert to percentage
            return 0.0
        except Exception as e:
            print(f"Error querying Prometheus: {e}")
            return 0.0

    def step(self, action):
        """
        The Agent takes an action (0, 1, or 2).
        We execute it, wait, and return the new state and reward.
        """
        current_replicas = self._get_replica_count()
        
        # 1. Execute Action
        if action == 0:   # Scale Down
            self._scale_deployment(current_replicas - 1)
        elif action == 2: # Scale Up
            self._scale_deployment(current_replicas + 1)
        # Action 1 is "Do Nothing", so we skip

        # 2. Wait for the cluster to react (Simulation speed)
        # In real life, pods take seconds to boot. We wait 2s here to let metrics stabilize.
        time.sleep(2)

        # 3. Get New State (Observation)
        cpu_usage = self._get_cpu_usage()
        observation = np.array([cpu_usage], dtype=np.float32)

        # 4. Calculate Reward (The "Score")
        # Ideal CPU target is 50%. 
        # - We penalize deviation from 50% (Stability)
        # - We penalize having too many replicas (Cost)
        
        dist_from_target = abs(cpu_usage - 50)
        reward = -dist_from_target - (0.5 * current_replicas)

        # 5. Check if done (optional, we usually run indefinitely)
        terminated = False
        truncated = False
        info = {"replicas": current_replicas, "cpu": cpu_usage}

        return observation, reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        """Reset the environment to a clean state"""
        super().reset(seed=seed)
        self._scale_deployment(1) # Reset to 1 pod
        time.sleep(2)
        return np.array([0.0], dtype=np.float32), {}