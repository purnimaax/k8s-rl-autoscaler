import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time

# --- CONFIGURATION ---
PROMETHEUS_URL = "http://localhost:9090"
REFRESH_RATE = 2  # seconds

st.set_page_config(page_title="K8s AI Autoscaler", layout="wide")
st.title("🤖 Self-Healing K8s Cluster (AI Agent View)")

# 1. CREATE CONTAINERS (The "Slots")
# We create these ONCE so we can just update them later
kpi1, kpi2 = st.columns(2)
with kpi1:
    cpu_metric_slot = st.empty() # Slot for CPU
with kpi2:
    replica_metric_slot = st.empty() # Slot for Replicas

chart_slot = st.empty() # Slot for the Graph

def get_prometheus_data(query, step='10s'):
    """Fetch range vectors from Prometheus"""
    try:
        end_time = time.time()
        start_time = end_time - 600  # Last 10 mins
        
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query_range",
            params={
                'query': query,
                'start': start_time,
                'end': end_time,
                'step': step
            }
        )
        data = response.json()
        
        if 'data' not in data or 'result' not in data['data']:
            return pd.DataFrame()
            
        results = data['data']['result']
        if not results:
            return pd.DataFrame()
        
        values = results[0]['values']
        df = pd.DataFrame(values, columns=['time', 'value'])
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df['value'] = df['value'].astype(float)
        return df
    except Exception as e:
        print(f"Prometheus Error: {e}")
        return pd.DataFrame()

# --- MAIN LOOP ---
while True:
    # 1. Get Metrics
    # CPU Usage
    cpu_query = 'avg(rate(container_cpu_usage_seconds_total{pod=~"cpu-eater.*", container!="POD"}[1m])) * 100'
    cpu_df = get_prometheus_data(cpu_query)

    # Replica Count
    # We use a simple query to count running pods
    replica_query = 'count(kube_pod_info{pod=~"cpu-eater.*"})' 
    # Fallback if kube_pod_info is missing: count 'up' metric
    if cpu_df.empty:
        replica_df = pd.DataFrame()
    else:
        replica_df = get_prometheus_data('sum(up{pod=~"cpu-eater.*"})')

    # 2. Update KPIs (Write into the pre-made SLOTS)
    current_cpu = cpu_df['value'].iloc[-1] if not cpu_df.empty else 0
    current_replicas = replica_df['value'].iloc[-1] if not replica_df.empty else 0

    # UPDATE THE SLOTS
    cpu_metric_slot.metric(label="🔥 Average CPU Load", value=f"{current_cpu:.1f}%")
    replica_metric_slot.metric(label="📦 Active Replicas", value=f"{int(current_replicas)}")

    # 3. Draw Dual-Axis Chart
    fig = go.Figure()

    if not cpu_df.empty:
        fig.add_trace(go.Scatter(
            x=cpu_df['time'], y=cpu_df['value'],
            name="CPU Load (%)",
            line=dict(color='firebrick', width=3)
        ))

    if not replica_df.empty:
        fig.add_trace(go.Scatter(
            x=replica_df['time'], y=replica_df['value'],
            name="Replicas",
            line=dict(color='royalblue', width=2, dash='dot'),
            yaxis="y2"
        ))

    fig.update_layout(
        title="Real-Time System Dynamics",
        xaxis_title="Time",
        yaxis=dict(title="CPU Load (%)", range=[0, 100]),
        yaxis2=dict(title="Replica Count", overlaying="y", side="right", range=[0, 10]),
        height=500,
        legend=dict(x=0, y=1.1, orientation="h")
    )

    # Write to chart slot with unique key
    chart_slot.plotly_chart(fig, use_container_width=True, key=str(time.time()))

    time.sleep(REFRESH_RATE)