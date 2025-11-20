import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def main():
    st.set_page_config(
        page_title="Pressure Return P&ID",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("Pressure Return P&ID Dashboard")
    st.markdown("## Return Line Monitoring System")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Return Line Controls")
        backpressure_setpoint = st.slider("Backpressure Setpoint (bar)", 0.0, 5.0, 2.0)
        return_flow_limit = st.slider("Return Flow Limit (L/min)", 0, 100, 60)
        st.checkbox("Enable Recirculation")
        st.button("Purge System", type="secondary")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Return P&ID Diagram")
        # Placeholder for P&ID diagram
        st.image("https://via.placeholder.com/600x400/34D399/FFFFFF?text=Pressure+Return+P%26ID", 
                use_column_width=True)
        
        # Real-time data display
        st.subheader("Return Line Parameters")
        metric1, metric2, metric3 = st.columns(3)
        with metric1:
            st.metric("Return Pressure", f"{np.random.uniform(1.8, 2.2):.2f} bar", "-0.1")
        with metric2:
            st.metric("Return Flow", f"{np.random.uniform(55, 65):.1f} L/min", "+3.2")
        with metric3:
            st.metric("Fluid Level", f"{np.random.uniform(75, 85):.1f} %", "+2.1")
    
    with col2:
        st.subheader("Return System Status")
        status_col1, status_col2 = st.columns(2)
        
        with status_col1:
            st.success("Tank Level: Normal")
            st.warning("Filter: 85% Clean")
            st.info("Cooler: Active")
            
        with status_col2:
            st.error("Leaks: 0")
            st.success("Pressure Relief: OK")
            st.warning("Temperature: Normal")
        
        # Return flow trend
        st.subheader("Return Flow Trend")
        time = np.arange(0, 24, 0.1)
        flow = 60 + 5 * np.sin(time * 0.5)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time, y=flow, mode='lines', name='Return Flow'))
        fig.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
