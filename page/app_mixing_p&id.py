import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def main():
    st.set_page_config(
        page_title="Mixing P&ID",
        page_icon="⚗️",
        layout="wide"
    )
    
    st.title("Mixing System P&ID Dashboard")
    st.markdown("## Fluid Mixing and Blending Control")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Mixing Controls")
        mix_ratio_a = st.slider("Fluid A Ratio (%)", 0, 100, 60)
        mix_ratio_b = st.slider("Fluid B Ratio (%)", 0, 100, 40)
        mixing_speed = st.slider("Mixing Speed (RPM)", 0, 1000, 500)
        st.button("Start Mixing", type="primary")
        st.button("Stop Mixing", type="secondary")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Mixing P&ID Diagram")
        # Placeholder for P&ID diagram
        st.image("https://via.placeholder.com/600x400/F59E0B/FFFFFF?text=Mixing+P%26ID", 
                use_column_width=True)
        
        # Real-time data display
        st.subheader("Mixing Parameters")
        metric1, metric2, metric3 = st.columns(3)
        with metric1:
            st.metric("Mix Temperature", f"{np.random.uniform(22, 28):.1f} °C", "+1.2")
        with metric2:
            st.metric("Mix Density", f"{np.random.uniform(0.95, 1.05):.3f} g/mL", "-0.02")
        with metric3:
            st.metric("Mix Quality", f"{np.random.uniform(85, 95):.1f} %", "+2.5")
    
    with col2:
        st.subheader("Mixing System Status")
        status_col1, status_col2 = st.columns(2)
        
        with status_col1:
            st.success("Mixer: Running")
            st.warning("Fluid A: 60%")
            st.info("Fluid B: 40%")
            
        with status_col2:
            st.error("Contamination: 0%")
            st.success("Homogeneity: 92%")
            st.warning("Viscosity: Normal")
        
        # Mixing quality trend
        st.subheader("Mixing Quality Trend")
        time = np.arange(0, 24, 0.1)
        quality = 90 + 3 * np.sin(time * 0.3)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time, y=quality, mode='lines', name='Mixing Quality'))
        fig.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
        
        # Ratio display
        st.subheader("Current Ratios")
        ratios = pd.DataFrame({
            'Fluid': ['Fluid A', 'Fluid B'],
            'Ratio': [mix_ratio_a, mix_ratio_b]
        })
        st.bar_chart(ratios.set_index('Fluid'))

if __name__ == "__main__":
    main()
