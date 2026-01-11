# Self-Healing Kubernetes Cluster with Reinforcement Learning

### 🚀 Project Overview
A closed-loop infrastructure system that autonomously scales Kubernetes resources based on real-time traffic patterns. Unlike traditional autoscalers (HPA) that react to thresholds, this project uses a **Proximal Policy Optimization (PPO)** Reinforcement Learning agent to optimize for both **performance** (CPU latency) and **cost** (pod count).

### 🏗️ Architecture
* **Infrastructure:** Minikube (Kubernetes), Docker
* **Observability:** Prometheus (Real-time metrics scraping)
* **RL Engine:** Stable Baselines3 (PPO Algorithm), OpenAI Gymnasium (Custom Environment)
* **Application:** Python Flask (Simulated CPU-intensive workloads)

### 🧠 How It Works
1.  **Observe:** Prometheus scrapes real-time CPU usage from the Flask application.
2.  **Decide:** The RL Agent (trained via PPO) analyzes the state and selects an action: `Scale Up`, `Scale Down`, or `Hold`.
3.  **Act:** The agent interacts directly with the Kubernetes API to patch the Deployment.
4.  **Learn:** The agent receives a reward based on a custom function balancing application stability vs. resource cost.

### 🛠️ Installation & Usage

**1. Prerequisites**
* Docker & Minikube
* Python 3.9+
* Helm

**2. Setup Infrastructure**
```bash
# Start Minikube
minikube start

# Deploy App & Prometheus
kubectl apply -f app-deployment.yaml
helm install prometheus prometheus-community/prometheus