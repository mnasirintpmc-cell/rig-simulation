import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def main():
    st.set_page_config(
        page_title="Separation Seal P&ID",
        page_icon="🔒",
        layout="wide"
    )
    
    st.title("Separation Seal P&ID Dashboard")
    st.markdown("## Seal System Monitoring and Control")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Seal Controls")
        seal_pressure = st.slider("Seal Pressure (bar)", 0.0, 10.0, 3.5)
        barrier_fluid_level = st.slider("Barrier Fluid Level (%)", 0, 100, 80)
        st.checkbox("Auto Purge", value=True)
        st.button("Test Seal", type="secondary")
        st.button("Emergency Seal", type="primary")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Separation Seal P&ID Diagram")
        # Placeholder for P&ID diagram
        st.image("https://via.placeholder.com/600x400/EF4444/FFFFFF?text=Separation+Seal+P%26ID", 
                use_column_width=True)
        
        # Real-time data display
        st.subheader("Seal System Parameters")
        metric1, metric2, metric3 = st.columns(3)
        with metric1:
            st.metric("Seal Pressure", f"{np.random.uniform(3.4, 3.6):.2f} bar", "-0.05")
        with metric2:
            st.metric("Leakage Rate", f"{np.random.uniform(0.1, 0.5):.2f} mL/hr", "+0.1")
        with metric3:
            st.metric("Seal Temp", f"{np.random.uniform(35, 45):.1f} °C", "+2.3")
    
    with col2:
        st.subheader("Seal System Status")
        status_col1, status_col2 = st.columns(2)
        
        with status_col1:
            st.success("Primary Seal: OK")
            st.warning("Secondary Seal: OK")
            st.info("Barrier Fluid: Normal")
            
        with status_col2:
            st.error("Leak Detection: None")
            st.success("Pressure Balance: OK")
            st.warning("Wear Level: 15%")
        
        # Seal pressure trend
        st.subheader("Seal Pressure Trend")
        time = np.arange(0, 24, 0.1)
        pressure = 3.5 + 0.2 * np.sin(time * 0.4)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time, y=pressure, mode='lines', name='Seal Pressure'))
        fig.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
        
        # Seal health indicator
        st.subheader("Seal Health")
        health = 85  # Example health percentage
        st.progress(health / 100)
        st.write(f"Overall Seal Health: {health}%")

if __name__ == "__main__":
    main()
