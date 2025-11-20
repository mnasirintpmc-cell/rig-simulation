
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

def main():
    st.set_page_config(
        page_title="DGS Simulation",
        page_icon="🎮",
        layout="wide"
    )
    
    st.title("DGS Simulation Dashboard")
    st.markdown("## Dynamic Gas System Simulation and Monitoring")
    
    # Sidebar for simulation controls
    with st.sidebar:
        st.header("Simulation Controls")
        simulation_speed = st.select_slider("Simulation Speed", 
                                          options=['0.5x', '1x', '2x', '5x', '10x'], 
                                          value='1x')
        
        gas_type = st.selectbox("Gas Type", 
                               ['Nitrogen', 'Helium', 'Argon', 'Air', 'Custom'])
        
        pressure_range = st.slider("Pressure Range (bar)", 0.0, 100.0, (10.0, 50.0))
        temperature_setpoint = st.slider("Temperature (°C)", -50.0, 150.0, 25.0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.button("Start Simulation", type="primary")
        with col2:
            st.button("Pause Simulation", type="secondary")
        
        st.button("Reset Simulation", type="secondary")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("DGS System Overview")
        # Placeholder for system diagram
        st.image("https://via.placeholder.com/600x400/8B5CF6/FFFFFF?text=DGS+Simulation+System", 
                use_column_width=True)
        
        # Simulation metrics
        st.subheader("Simulation Parameters")
        sim_col1, sim_col2, sim_col3, sim_col4 = st.columns(4)
        with sim_col1:
            st.metric("System Pressure", f"{np.random.uniform(28, 32):.1f} bar", "+0.5")
        with sim_col2:
            st.metric("Gas Flow", f"{np.random.uniform(45, 55):.1f} m³/h", "-1.2")
        with sim_col3:
            st.metric("Temperature", f"{np.random.uniform(23, 27):.1f} °C", "+0.8")
        with sim_col4:
            st.metric("Density", f"{np.random.uniform(1.1, 1.3):.2f} kg/m³", "-0.05")
    
    with col2:
        st.subheader("Simulation Status")
        status_col1, status_col2 = st.columns(2)
        
        with status_col1:
            st.success("Status: Running")
            st.warning("Speed: 1x")
            st.info("Gas: Nitrogen")
            
        with status_col2:
            st.error("Warnings: 0")
            st.success("Stability: 98%")
            st.warning("Time: 02:15:33")
        
        # Real-time pressure simulation
        st.subheader("Pressure Simulation")
        time = np.arange(0, 10, 0.1)
        pressure = 30 + 2 * np.sin(time * 2) + 0.5 * np.random.normal(size=len(time))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time, y=pressure, mode='lines', name='Pressure'))
        fig.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    # Additional simulation data
    st.subheader("Simulation Data Log")
    
    # Generate sample simulation data
    simulation_data = pd.DataFrame({
        'Time': pd.date_range(start='2024-01-01', periods=100, freq='S'),
        'Pressure (bar)': np.random.normal(30, 2, 100),
        'Flow (m³/h)': np.random.normal(50, 5, 100),
        'Temperature (°C)': np.random.normal(25, 2, 100)
    })
    
    st.dataframe(simulation_data.tail(10), use_container_width=True)
    
    # Simulation charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("Pressure vs Flow")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=simulation_data['Flow (m³/h)'], 
                               y=simulation_data['Pressure (bar)'],
                               mode='markers', name='Data Points'))
        fig.update_layout(xaxis_title='Flow (m³/h)', yaxis_title='Pressure (bar)')
        st.plotly_chart(fig, use_container_width=True)
    
    with chart_col2:
        st.subheader("Temperature Trend")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=simulation_data['Time'], 
                               y=simulation_data['Temperature (°C)'],
                               mode='lines', name='Temperature'))
        fig.update_layout(xaxis_title='Time', yaxis_title='Temperature (°C)')
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
