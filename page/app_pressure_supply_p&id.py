import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def main():
    st.set_page_config(
        page_title="Pressure Supply P&ID",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("Pressure Supply P&ID Dashboard")
    st.markdown("## Real-time Monitoring and Control")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Control Panel")
        pressure_setpoint = st.slider("Pressure Setpoint (bar)", 0.0, 10.0, 5.0)
        valve_position = st.slider("Valve Position (%)", 0, 100, 50)
        st.button("Emergency Stop", type="secondary")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("P&ID Diagram")
        # Placeholder for P&ID diagram
        st.image("https://via.placeholder.com/600x400/4A90E2/FFFFFF?text=Pressure+Supply+P%26ID", 
                use_column_width=True)
        
        # Real-time data display
        st.subheader("Real-time Parameters")
        metric1, metric2, metric3 = st.columns(3)
        with metric1:
            st.metric("Supply Pressure", f"{np.random.uniform(4.8, 5.2):.2f} bar", "±0.1")
        with metric2:
            st.metric("Flow Rate", f"{np.random.uniform(45, 55):.1f} L/min", "-2.1")
        with metric3:
            st.metric("Temperature", f"{np.random.uniform(20, 25):.1f} °C", "+0.5")
    
    with col2:
        st.subheader("System Status")
        status_col1, status_col2 = st.columns(2)
        
        with status_col1:
            st.success("Pump: Running")
            st.warning("Valve: 50% Open")
            st.info("Filter: Clean")
            
        with status_col2:
            st.error("Alarms: 0")
            st.success("Safety: OK")
            st.warning("Maintenance: Due in 30 days")
        
        # Pressure trend
        st.subheader("Pressure Trend")
        time = np.arange(0, 24, 0.1)
        pressure = 5 + 0.5 * np.sin(time)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time, y=pressure, mode='lines', name='Pressure'))
        fig.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
