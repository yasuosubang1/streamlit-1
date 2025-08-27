import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import json
from typing import Dict, List, Any
import io
import numpy as np
from datetime import datetime, timedelta
try:
    import openpyxl
except ImportError:
    st.warning("⚠️ openpyxl not installed. Excel export will not be available. Install with: pip install openpyxl")
    openpyxl = None

# Page configuration
st.set_page_config(
    page_title="Instance Application Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'overview'
if 'selected_filter' not in st.session_state:
    st.session_state.selected_filter = {}
if 'processing_errors' not in st.session_state:
    st.session_state.processing_errors = []

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 1rem;
        padding: 1rem;
        background: linear-gradient(90deg, #3498db, #2980b9);
        color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .subtitle {
        font-size: 1.2rem;
        color: #7f8c8d;
        text-align: center;
        margin-bottom: 2rem;
        font-style: italic;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #3498db;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .critical-service-alert {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .nav-button {
        background-color: #3498db;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        cursor: pointer;
        margin: 0.2rem;
    }
    .nav-button:hover {
        background-color: #2980b9;
    }
    .error-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 0.5rem;
        z-index: 1000;
        cursor: pointer;
    }
    .page-container {
        padding: 1rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def show_error_notification():
    """Show error notification icon with expandable details"""
    if st.session_state.processing_errors:
        with st.container():
            col1, col2 = st.columns([10, 1])
            with col2:
                if st.button("⚠️", help=f"{len(st.session_state.processing_errors)} error(s) occurred"):
                    with st.expander("Processing Errors", expanded=True):
                        for error in st.session_state.processing_errors:
                            st.error(error)
                        if st.button("Clear Errors"):
                            st.session_state.processing_errors = []
                            st.rerun()

def navigate_to_page(page_name, filter_data=None):
    """Navigate to a specific page with optional filter"""
    st.session_state.current_page = page_name
    if filter_data:
        st.session_state.selected_filter = filter_data
    st.rerun()

def create_navigation_bar():
    """Create navigation bar for different pages"""
    st.markdown("### 🧭 Navigation")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Application Overview", width='stretch'):
            navigate_to_page('overview')
    
    with col2:
        if st.button("🏢 Instance Details", width='stretch'):
            navigate_to_page('instance_details')
    
    with col3:
        if st.button("🔍 Filtered View", width='stretch'):
            navigate_to_page('filtered_view')
    
    with col4:
        if st.button("📋 Database Table", width='stretch'):
            navigate_to_page('data_table')
    
    st.markdown("---")

def load_and_validate_json(uploaded_file) -> Dict[str, Any]:
    """
    Load and validate JSON file structure.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Dict containing the parsed JSON data
        
    Raises:
        ValueError: If JSON structure is invalid
    """
    try:
        content = uploaded_file.read()
        if len(content) == 0:
            raise ValueError("File is empty")
            
        data = json.loads(content)
        
        # Basic validation
        required_fields = ['instance_id', 'instance_name', 'applications']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Validate field types
        if not isinstance(data['instance_id'], str) or not data['instance_id'].strip():
            raise ValueError("'instance_id' must be a non-empty string")
            
        if not isinstance(data['instance_name'], str) or not data['instance_name'].strip():
            raise ValueError("'instance_name' must be a non-empty string")
        
        if not isinstance(data['applications'], list):
            raise ValueError("'applications' must be a list")
            
        # Validate applications structure
        if len(data['applications']) == 0:
            raise ValueError("'applications' list is empty")
            
        for i, app in enumerate(data['applications']):
            if not isinstance(app, dict):
                raise ValueError(f"Application {i+1} must be an object")
            if 'name' not in app:
                raise ValueError(f"Application {i+1} missing 'name' field")
                
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format at line {e.lineno}: {e.msg}")
    except Exception as e:
        raise ValueError(f"Error processing file: {str(e)}")

def process_instance_data(uploaded_files):
    """
    Process multiple uploaded files and return a combined pandas DataFrame
    """
    all_dataframes = []
    
    for uploaded_file in uploaded_files:
        try:
            # Load and validate JSON
            data = load_and_validate_json(uploaded_file)
            
            # Extract instance information
            instance_id = data.get('instance_id', 'Unknown')
            instance_name = data.get('instance_name', 'Unknown')
            script_version = data.get('script_version', 'Unknown')
            
            # Process applications
            applications = data.get('applications', [])
            
            if not applications:
                st.session_state.processing_errors.append(
                    f"Error processing {uploaded_file.name}: Error processing file: 'applications' list is empty"
                )
                continue
            
            app_data = []
            for app in applications:
                app_info = {
                    'instance_id': instance_id,
                    'instance_name': instance_name,
                    'script_version': script_version,
                    'app_name': app.get('name', 'Unknown'),
                    'app_type': app.get('type', 'Unknown'),
                    'app_status': app.get('status', 'Unknown'),
                    'app_image': app.get('image', ''),
                    'ports': ', '.join(map(str, app.get('ports', []))),
                    'pids': ', '.join(map(str, app.get('pids', []))),
                    'process_name': app.get('process_name', ''),
                    'container_id': app.get('container_id', '')
                }
                app_data.append(app_info)
            
            if app_data:
                df = pd.DataFrame(app_data)
                all_dataframes.append(df)
                
        except Exception as e:
            st.session_state.processing_errors.append(
                f"Error processing {uploaded_file.name}: {str(e)}"
            )
            continue
    
    # Combine all dataframes
    if all_dataframes:
        return pd.concat(all_dataframes, ignore_index=True)
    else:
        return pd.DataFrame()

def create_summary_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate summary metrics from the processed data.
    
    Args:
        df: Processed DataFrame
        
    Returns:
        Dictionary containing summary metrics
    """
    # Calculate port statistics
    all_ports = []
    for ports_str in df['ports'].dropna():
        if ports_str:
            all_ports.extend([p.strip() for p in str(ports_str).split(',') if p.strip()])
    
    return {
        'total_instances': df['instance_id'].nunique(),
        'total_applications': len(df),
        'unique_app_types': df['app_type'].nunique(),
        'avg_apps_per_instance': round(len(df) / df['instance_id'].nunique(), 1) if df['instance_id'].nunique() > 0 else 0,
        'app_types': df['app_type'].value_counts().to_dict()
    }

def create_application_overview_page(df: pd.DataFrame):
    """
    Create the main Application Overview page with interactive visualizations
    """
    st.markdown("<div class='page-container'>", unsafe_allow_html=True)
    st.markdown("# 📊 Application Overview")
    st.markdown("Comprehensive overview of all applications across instances")
    
    if df.empty:
        st.warning("No data available for visualization.")
        return
    
    # Summary metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_instances = df['instance_id'].nunique()
        st.metric("Total Instances", total_instances)
    
    with col2:
        total_apps = len(df)
        st.metric("Total Applications", total_apps)
    
    with col3:
        app_types = df['app_type'].nunique()
        st.metric("App Types", app_types)
    
    with col4:
        avg_apps = round(total_apps / total_instances, 1) if total_instances > 0 else 0
        st.metric("Avg Apps/Instance", avg_apps)
    
    st.markdown("---")
    
    # Quick Actions Section
    st.markdown("### ⚡ Quick Actions")
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    
    with action_col1:
        if st.button("🔍 View All Data", key="view_all_data_btn", help="Go to complete database table"):
            st.session_state.current_page = 'data_table'
            st.rerun()
    
    with action_col2:
        if st.button("🏢 Instance Analysis", key="instance_analysis_btn", help="Detailed instance analysis"):
            st.session_state.current_page = 'instance_details'
            st.rerun()
    
    with action_col3:
        # Find most used app type for quick filter
        most_used_app_type = df['app_type'].value_counts().index[0] if not df['app_type'].value_counts().empty else None
        if most_used_app_type and st.button(f"🎯 View {most_used_app_type}", key="view_most_used_app_btn", help=f"Filter by {most_used_app_type} applications"):
            st.session_state.current_page = 'filtered_view'
            st.session_state.selected_filter = {'type': 'app_type', 'value': most_used_app_type}
            st.rerun()
    
    with action_col4:
        # Find instance with most apps for quick access
        busiest_instance = df.groupby('instance_name').size().idxmax() if not df.empty else None
        if busiest_instance and st.button(f"🏆 Busiest Instance", key="busiest_instance_btn", help=f"View {busiest_instance} (most applications)"):
            st.session_state.current_page = 'filtered_view'
            st.session_state.selected_filter = {'type': 'instance', 'value': busiest_instance}
            st.rerun()
    
    st.markdown("---")
    
    # Interactive visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Application Types Distribution")
        app_type_counts = df['app_type'].value_counts()
        
        fig_pie = px.pie(
            values=app_type_counts.values,
            names=app_type_counts.index,
            title="Click on a segment to filter applications",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(showlegend=True, height=400)
        
        # Display pie chart with click interaction
        pie_event = st.plotly_chart(fig_pie, width='stretch', key="app_type_pie", on_select="rerun")
        
        # Handle pie chart selection
        if pie_event.selection.points:
            selected_point = pie_event.selection.points[0]
            selected_app_type = selected_point["label"]
            st.session_state.current_page = 'filtered_view'
            st.session_state.selected_filter = {'type': 'app_type', 'value': selected_app_type}
    
    with col2:
        st.markdown("### 🏢 Applications per Instance")
        instance_app_counts = df.groupby('instance_name').size().reset_index(name='app_count')
        
        fig_bar = px.bar(
            instance_app_counts,
            x='instance_name',
            y='app_count',
            title="Click on a bar to view instance details",
            color='app_count',
            color_continuous_scale='Blues'
        )
        fig_bar.update_layout(height=400, xaxis_tickangle=-45)
        
        # Display bar chart with click interaction
        bar_event = st.plotly_chart(fig_bar, width='stretch', key="instance_bar", on_select="rerun")
        
        # Handle bar chart selection
        if bar_event.selection.points:
            selected_point = bar_event.selection.points[0]
            selected_instance = selected_point["x"]
            st.session_state.current_page = 'filtered_view'
            st.session_state.selected_filter = {'type': 'instance', 'value': selected_instance}
    
    # Additional visualizations
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔧 Application Status Overview")
        if 'app_status' in df.columns:
            status_counts = df['app_status'].value_counts()
            fig_status = px.bar(
                x=status_counts.index,
                y=status_counts.values,
                title="Application Status Distribution - Click to filter",
                color=status_counts.values,
                color_continuous_scale='RdYlGn'
            )
            fig_status.update_layout(height=300)
            
            # Display status chart
            st.plotly_chart(fig_status, width='stretch', key="status_bar")
        else:
            st.info("Status information not available")
    
    with col2:
        st.markdown("### 📈 Instance Utilization")
        instance_types = df.groupby('instance_name')['app_type'].nunique().reset_index(name='type_diversity')
        
        fig_scatter = px.scatter(
            instance_types,
            x='instance_name',
            y='type_diversity',
            size=[instance_app_counts[instance_app_counts['instance_name'] == name]['app_count'].iloc[0] for name in instance_types['instance_name']],
            title="Instance Diversity (Apps vs Types) - Click to view details",
            hover_data=['type_diversity']
        )
        fig_scatter.update_layout(height=300, xaxis_tickangle=-45)
        
        # Display scatter plot
        st.plotly_chart(fig_scatter, width='stretch', key="instance_scatter")
    
    # Additional innovative visualizations
    st.markdown("---")
    st.markdown("### 🚀 Advanced Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🌐 Port Usage Heatmap")
        if 'ports' in df.columns:
            # Extract port information
            port_data = []
            for _, row in df.iterrows():
                if pd.notna(row['ports']) and row['ports'] != '':
                    ports = str(row['ports']).split(',')
                    for port in ports:
                        port = port.strip()
                        if port and port.isdigit():
                            port_data.append({
                                'instance': row['instance_name'],
                                'port': int(port),
                                'app_type': row['app_type']
                            })
            
            if port_data:
                port_df = pd.DataFrame(port_data)
                port_usage = port_df.groupby(['instance', 'port']).size().reset_index(name='count')
                
                if len(port_usage) > 0:
                    # Create a simplified heatmap for top ports
                    top_ports = port_df['port'].value_counts().head(10).index
                    filtered_port_usage = port_usage[port_usage['port'].isin(top_ports)]
                    
                    if len(filtered_port_usage) > 0:
                        pivot_ports = filtered_port_usage.pivot(index='instance', columns='port', values='count').fillna(0)
                        
                        fig_heatmap = px.imshow(
                            pivot_ports.values,
                            x=pivot_ports.columns,
                            y=pivot_ports.index,
                            color_continuous_scale='Viridis',
                            title="Top 10 Ports Usage by Instance",
                            labels=dict(x="Port", y="Instance", color="Usage")
                        )
                        fig_heatmap.update_layout(height=300)
                        
                        # Display heatmap
                        st.plotly_chart(fig_heatmap, width='stretch', key="port_heatmap")
                    else:
                        st.info("No port usage data available for heatmap")
                else:
                    st.info("No valid port data found")
            else:
                st.info("No port information available")
        else:
            st.info("Port information not available in dataset")
    
    with col2:
        st.markdown("#### 🌳 Application Hierarchy")
        # Create treemap for application hierarchy
        if 'app_status' in df.columns:
            hierarchy_data = df.groupby(['instance_name', 'app_type', 'app_status']).size().reset_index(name='count')
        else:
            hierarchy_data = df.groupby(['instance_name', 'app_type']).size().reset_index(name='count')
            hierarchy_data['app_status'] = 'unknown'
        
        if not hierarchy_data.empty and len(hierarchy_data) > 0:
            fig_treemap = px.treemap(
                hierarchy_data,
                path=['instance_name', 'app_type', 'app_status'] if 'app_status' in df.columns else ['instance_name', 'app_type'],
                values='count',
                title="Application Hierarchy - Click to explore",
                color='count',
                color_continuous_scale='Viridis'
            )
            fig_treemap.update_layout(height=300)
            
            # Display treemap
            st.plotly_chart(fig_treemap, width='stretch', key="app_treemap")
        else:
            st.info("No hierarchy data available")
    
    st.markdown("</div>", unsafe_allow_html=True)

def create_visualizations(df: pd.DataFrame, metrics: Dict[str, Any]):
    """
    Create interactive visualizations using Plotly.
    
    Args:
        df: Processed DataFrame
        metrics: Summary metrics dictionary
    """
    st.subheader("📊 Data Visualizations")
    
    st.subheader("📱 Application Types Distribution")
    if metrics['app_types']:
        fig_types = px.pie(
            values=list(metrics['app_types'].values()),
            names=list(metrics['app_types'].keys()),
            title="Distribution by Application Type",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_types.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )
        st.plotly_chart(fig_types, width='stretch')
    else:
        st.info("No application type data available")



def create_port_heatmap(df: pd.DataFrame):
    """
    Create heatmap visualization for port usage across instances.
    
    Args:
        df: Processed DataFrame
    """
    st.subheader("🔥 Port Usage Heatmap")
    
    if df.empty:
        st.info("No data available for port heatmap")
        return
    
    # Extract port information
    port_data = []
    
    for idx, row in df.iterrows():
        if pd.notna(row['ports']) and row['ports'] != 'N/A':
            try:
                # Handle different port formats
                ports_str = str(row['ports'])
                if ',' in ports_str:
                    ports = [p.strip() for p in ports_str.split(',')]
                elif ':' in ports_str:
                    ports = [p.split(':')[0] for p in ports_str.split(',')]
                else:
                    ports = [ports_str]
                
                for port in ports:
                    if port.isdigit():
                        port_data.append({
                            'instance': row['instance_name'],
                            'port': int(port),
                            'app_name': row['app_name'],
                            'app_type': row['app_type'],
                            'status': row['app_status']
                        })
            except:
                continue
    
    if port_data:
        port_df = pd.DataFrame(port_data)
        
        # Create port usage matrix
        port_matrix = port_df.groupby(['instance', 'port']).size().reset_index(name='count')
        pivot_matrix = port_matrix.pivot(index='instance', columns='port', values='count').fillna(0)
        
        if not pivot_matrix.empty:
            # Create heatmap
            fig = px.imshow(
                pivot_matrix.values,
                labels=dict(x="Port", y="Instance", color="Usage Count"),
                x=pivot_matrix.columns,
                y=pivot_matrix.index,
                color_continuous_scale='Viridis',
                title="Port Usage Across Instances"
            )
            
            fig.update_layout(
                height=max(400, len(pivot_matrix.index) * 50),
                xaxis_title="Port Number",
                yaxis_title="Instance Name"
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # Port statistics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Port Statistics")
                port_stats = port_df['port'].value_counts().head(10)
                fig_port_stats = px.bar(
                    x=port_stats.index,
                    y=port_stats.values,
                    title="Top 10 Most Used Ports",
                    labels={'x': 'Port', 'y': 'Usage Count'}
                )
                st.plotly_chart(fig_port_stats, width='stretch')
            
            with col2:
                st.subheader("🏷️ Port by Application Type")
                port_type_df = port_df.groupby(['app_type', 'port']).size().reset_index(name='count')
                fig_port_type = px.sunburst(
                    port_type_df,
                    path=['app_type', 'port'],
                    values='count',
                    title="Port Usage by Application Type"
                )
                st.plotly_chart(fig_port_type, width='stretch')
        else:
            st.info("No port usage data available for heatmap")
    else:
        st.info("No valid port data found")

def create_instance_details_page(df: pd.DataFrame):
    """
    Create comprehensive instance details page
    """
    st.markdown("<div class='page-container'>", unsafe_allow_html=True)
    st.markdown("# 🏢 Instance Details")
    st.markdown("Comprehensive analysis of instances and their applications")
    
    if df.empty:
        st.warning("No data available for analysis.")
        return
    
    # Instance selector
    instances = df['instance_name'].unique()
    
    # Check if instance was selected from overview page
    default_instance = 'All Instances'
    if 'selected_instance_for_details' in st.session_state and st.session_state.selected_instance_for_details:
        if st.session_state.selected_instance_for_details in instances:
            default_instance = st.session_state.selected_instance_for_details
        # Clear the selection after using it
        st.session_state.selected_instance_for_details = None
    
    # Find the index of default_instance in the options list
    options = ['All Instances'] + list(instances)
    default_index = options.index(default_instance) if default_instance in options else 0
    
    selected_instance = st.selectbox(
        "Select Instance for Detailed Analysis:", 
        options,
        index=default_index
    )
    
    if selected_instance != 'All Instances':
        filtered_df = df[df['instance_name'] == selected_instance]
        st.markdown(f"### 📋 Analysis for: {selected_instance}")
        
        # Instance summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Applications", len(filtered_df))
        with col2:
            st.metric("Application Types", filtered_df['app_type'].nunique())
        with col3:
            if 'app_status' in filtered_df.columns:
                running_apps = len(filtered_df[filtered_df['app_status'] == 'running'])
                st.metric("Running Apps", running_apps)
            else:
                st.metric("Running Apps", "N/A")
        with col4:
            st.metric("Instance ID", filtered_df['instance_id'].iloc[0] if len(filtered_df) > 0 else "N/A")
        
        # Detailed visualizations for selected instance
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Application Types in this Instance")
            app_types = filtered_df['app_type'].value_counts()
            fig_pie = px.pie(
                values=app_types.values,
                names=app_types.index,
                title=f"Applications in {selected_instance}"
            )
            st.plotly_chart(fig_pie, width='stretch')
        
        with col2:
            st.markdown("#### Application Details")
            if 'ports' in filtered_df.columns:
                port_info = filtered_df[filtered_df['ports'] != '']['ports'].value_counts().head(10)
                if not port_info.empty:
                    fig_bar = px.bar(
                        x=port_info.index,
                        y=port_info.values,
                        title="Most Used Ports"
                    )
                    st.plotly_chart(fig_bar, width='stretch')
                else:
                    st.info("No port information available")
            else:
                st.info("Port information not available")
        
        # Application list for selected instance
        st.markdown("#### Applications in this Instance")
        display_cols = ['app_name', 'app_type', 'app_status', 'ports', 'app_image'] if 'app_status' in filtered_df.columns else ['app_name', 'app_type', 'ports', 'app_image']
        available_cols = [col for col in display_cols if col in filtered_df.columns]
        st.dataframe(filtered_df[available_cols], width='stretch')
        
    else:
        # All instances overview
        st.markdown("### 📊 All Instances Overview")
        
        # Instance summary table
        instance_summary = df.groupby('instance_name').agg({
            'app_name': 'count',
            'app_type': 'nunique',
            'instance_id': 'first'
        }).rename(columns={
            'app_name': 'total_apps',
            'app_type': 'app_types',
            'instance_id': 'instance_id'
        }).reset_index()
        
        st.markdown("#### Instance Summary")
        st.dataframe(instance_summary, width='stretch')
        
        # Visualizations for all instances
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Applications per Instance")
            fig_bar = px.bar(
                instance_summary,
                x='instance_name',
                y='total_apps',
                title="Total Applications per Instance",
                color='total_apps'
            )
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, width='stretch')
        
        with col2:
            st.markdown("#### Type Diversity per Instance")
            fig_bar2 = px.bar(
                instance_summary,
                x='instance_name',
                y='app_types',
                title="Application Type Diversity",
                color='app_types'
            )
            fig_bar2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar2, width='stretch')
    
    st.markdown("</div>", unsafe_allow_html=True)

def create_filtered_view_page(df: pd.DataFrame):
    """
    Create filtered view page based on user selection
    """
    st.markdown("<div class='page-container'>", unsafe_allow_html=True)
    st.markdown("# 🔍 Filtered View")
    
    if df.empty:
        st.warning("No data available for filtering.")
        return
    
    # Check if there's a filter from navigation
    if st.session_state.selected_filter:
        filter_type = st.session_state.selected_filter.get('type')
        filter_value = st.session_state.selected_filter.get('value')
        
        if filter_type == 'app_type':
            filtered_df = df[df['app_type'] == filter_value]
            st.markdown(f"### 🎯 Applications of type: **{filter_value}**")
            
        elif filter_type == 'instance':
            filtered_df = df[df['instance_name'] == filter_value]
            st.markdown(f"### 🏢 Applications in instance: **{filter_value}**")
            
        elif filter_type == 'app_status':
            if 'app_status' in df.columns:
                filtered_df = df[df['app_status'] == filter_value]
                st.markdown(f"### 🔧 Applications with status: **{filter_value}**")
            else:
                filtered_df = df
                st.warning(f"Status information not available. Showing all applications.")
            
        else:
            filtered_df = df
            st.markdown("### 📋 All Applications")
    else:
        filtered_df = df
        st.markdown("### 📋 All Applications")
    
    # Summary of filtered data
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Filtered Applications", len(filtered_df))
    with col2:
        st.metric("Instances Involved", filtered_df['instance_name'].nunique())
    with col3:
        st.metric("Application Types", filtered_df['app_type'].nunique())
    
    # Clear filter button
    if st.button("🔄 Clear Filter"):
        st.session_state.selected_filter = {}
        st.rerun()
    
    # Display filtered data
    if not filtered_df.empty:
        st.markdown("#### Filtered Applications Table")
        display_cols = ['instance_name', 'app_name', 'app_type', 'app_status', 'ports', 'app_image'] if 'app_status' in filtered_df.columns else ['instance_name', 'app_name', 'app_type', 'ports', 'app_image']
        available_cols = [col for col in display_cols if col in filtered_df.columns]
        st.dataframe(filtered_df[available_cols], width='stretch')
        
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"filtered_applications_{filter_value if 'filter_value' in locals() else 'all'}.csv",
                mime="text/csv"
            )
        
        with col2:
            json_data = filtered_df.to_json(orient='records', indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_data,
                file_name=f"filtered_applications_{filter_value if 'filter_value' in locals() else 'all'}.json",
                mime="application/json"
            )
    else:
        st.warning("No applications match the current filter.")
    
    st.markdown("</div>", unsafe_allow_html=True)

def create_data_table_page(df: pd.DataFrame):
    """
    Create comprehensive data table page
    """
    st.markdown("<div class='page-container'>", unsafe_allow_html=True)
    st.markdown("# 📋 Database Table")
    st.markdown("Complete application database with all details")
    
    if df.empty:
        st.warning("No data available in the database.")
        return
    
    # Search and filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("🔍 Search applications:", placeholder="Enter app name, type, or instance...")
    
    with col2:
        if 'app_type' in df.columns:
            app_type_filter = st.selectbox("Filter by App Type:", ['All'] + list(df['app_type'].unique()))
        else:
            app_type_filter = 'All'
    
    with col3:
        instance_filter = st.selectbox("Filter by Instance:", ['All'] + list(df['instance_name'].unique()))
    
    # Apply filters
    filtered_df = df.copy()
    
    if search_term:
        mask = (
            filtered_df['app_name'].str.contains(search_term, case=False, na=False) |
            filtered_df['app_type'].str.contains(search_term, case=False, na=False) |
            filtered_df['instance_name'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    if app_type_filter != 'All':
        filtered_df = filtered_df[filtered_df['app_type'] == app_type_filter]
    
    if instance_filter != 'All':
        filtered_df = filtered_df[filtered_df['instance_name'] == instance_filter]
    
    # Display results count
    st.markdown(f"**Showing {len(filtered_df)} of {len(df)} applications**")
    
    # Display the table
    if not filtered_df.empty:
        st.dataframe(filtered_df, width='stretch', height=600)
        
        # Export options
        st.markdown("### 📥 Export Options")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="application_database.csv",
                mime="text/csv",
                width='stretch'
            )
        
        with col2:
            json_data = filtered_df.to_json(orient='records', indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_data,
                file_name="application_database.json",
                mime="application/json",
                width='stretch'
            )
        
        with col3:
            # Summary statistics
            if st.button("📊 Show Summary Stats", width='stretch'):
                st.markdown("#### Summary Statistics")
                st.write(f"- Total Applications: {len(filtered_df)}")
                st.write(f"- Unique Instances: {filtered_df['instance_name'].nunique()}")
                st.write(f"- Application Types: {filtered_df['app_type'].nunique()}")
                if 'app_status' in filtered_df.columns:
                    st.write(f"- Running Applications: {len(filtered_df[filtered_df['app_status'] == 'running'])}")
    else:
        st.warning("No applications match the current filters.")
    
    st.markdown("</div>", unsafe_allow_html=True)

def create_instance_analysis(df: pd.DataFrame, metrics: Dict[str, Any]):
    """
    Create instance-focused analysis for management insights.
    
    Args:
        df: Processed DataFrame
        metrics: Calculated metrics dictionary
    """
    st.subheader("🏢 Instance Overview & Analysis")
    
    if df.empty:
        st.info("No data available for instance analysis")
        return
    
    # Instance summary
    instance_summary = df.groupby('instance_name').agg({
        'app_name': 'count',
        'app_type': 'nunique'
    }).rename(columns={
        'app_name': 'total_apps',
        'app_type': 'app_types'
    })
    
    # Display instance summary table
    st.subheader("📊 Instance Summary")
    st.dataframe(
        instance_summary,
        column_config={
            "total_apps": st.column_config.NumberColumn("Total Apps", format="%d"),
            "app_types": st.column_config.NumberColumn("App Types", format="%d")
        },
        width='stretch'
    )
    
    # Visualizations
    st.subheader("📈 Applications per Instance")
    fig_apps = px.bar(
        x=instance_summary.index,
        y=instance_summary['total_apps'],
        title="Total Applications by Instance",
        color=instance_summary['total_apps'],
        color_continuous_scale='Blues'
    )
    fig_apps.update_layout(showlegend=False, xaxis_title="Instance", yaxis_title="Applications")
    st.plotly_chart(fig_apps, width='stretch')
    
    # Application type distribution across instances
    st.subheader("🔄 Application Types Across Instances")
    app_type_matrix = df.groupby(['instance_name', 'app_type']).size().unstack(fill_value=0)
    
    if not app_type_matrix.empty:
        fig_matrix = px.imshow(
            app_type_matrix.values,
            labels=dict(x="Application Type", y="Instance", color="Count"),
            x=app_type_matrix.columns,
            y=app_type_matrix.index,
            color_continuous_scale='Viridis',
            title="Application Type Distribution Matrix"
        )
        fig_matrix.update_layout(height=max(400, len(app_type_matrix.index) * 50))
        st.plotly_chart(fig_matrix, width='stretch')


def create_treemap_visualization(df: pd.DataFrame):
    """
    Create treemap visualization for application hierarchy.
    
    Args:
        df: Processed DataFrame
    """
    st.subheader("🌳 Application Hierarchy Treemap")
    
    if df.empty:
        st.info("No data available for treemap")
        return
    
    # Create hierarchy data
    hierarchy_data = df.groupby(['instance_name', 'app_type', 'app_status']).size().reset_index(name='count')
    
    if not hierarchy_data.empty:
        fig = px.treemap(
            hierarchy_data,
            path=['instance_name', 'app_type', 'app_status'],
            values='count',
            title="Application Hierarchy: Instance → Type → Status",
            color='count',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(height=600)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No hierarchy data available")







def main():
    """
    Main application function with multi-page navigation
    """
    # Header
    st.markdown('<div class="main-header">📊 Application Dashboard</div>', unsafe_allow_html=True)
    
    # Show error notification if any
    show_error_notification()
    
    # Navigation bar
    create_navigation_bar()
    
    # File upload section (always visible)
    # Check if we have processed data to determine expander state
    has_data = 'processed_data' in st.session_state and st.session_state.processed_data is not None and not st.session_state.processed_data.empty
    with st.expander("📁 Upload Instance Data", expanded=not has_data):
        uploaded_files = st.file_uploader(
            "Choose JSON files",
            type="json",
            accept_multiple_files=True,
            help="Upload one or more JSON files containing instance and application data"
        )
        
        if uploaded_files:
            # Process files
            start_time = datetime.now()
            
            # Clear previous errors
            st.session_state.processing_errors = []
            
            # Process data
            combined_df = process_instance_data(uploaded_files)
            
            if not combined_df.empty:
                # Show processing time
                processing_time = (datetime.now() - start_time).total_seconds()
                st.success(f"✅ Successfully processed {len(uploaded_files)} files in {processing_time:.2f} seconds")
                
                # Store in session state
                st.session_state.processed_data = combined_df
                st.rerun()
            else:
                st.error("❌ No valid data found in uploaded files.")
    
    # Check if we have data to display
    if 'processed_data' in st.session_state and not st.session_state.processed_data.empty:
        df = st.session_state.processed_data
        
        # Route to appropriate page based on current_page
        if st.session_state.current_page == 'overview':
            create_application_overview_page(df)
            
        elif st.session_state.current_page == 'instance_details':
            create_instance_details_page(df)
            
        elif st.session_state.current_page == 'filtered_view':
            create_filtered_view_page(df)
            
        elif st.session_state.current_page == 'data_table':
            create_data_table_page(df)
            
        else:
            # Default to overview
            st.session_state.current_page = 'overview'
            create_application_overview_page(df)
            
    else:
        # No data available
        st.markdown("## 🚀 Welcome to Application Dashboard")
        st.markdown("""
        This dashboard provides comprehensive insights into your application instances and deployments.
        
        ### 📋 Features:
        - **📊 Application Overview**: Interactive visualizations and comprehensive metrics
        - **🏢 Instance Details**: Deep dive into individual instances and their applications
        - **🔍 Filtered View**: Dynamic filtering and focused analysis
        - **📋 Database Table**: Complete searchable application database
        
        ### 🚀 Getting Started:
        1. Upload your JSON files using the upload section above
        2. Navigate through different pages using the navigation bar
        3. Interact with visualizations to filter and explore your data
        4. Export filtered data for further analysis
        
        **👆 Please upload JSON files to begin your analysis.**
        """)
        
        # Show sample data structure
        with st.expander("📖 Expected JSON Format", expanded=False):
            st.code("""
{
  "instance_id": "i-1234567890abcdef0",
  "instance_name": "web-server-01",
  "script_version": "1.0.0",
  "applications": [
    {
      "name": "nginx",
      "type": "docker",
      "status": "running",
      "image": "nginx:latest",
      "ports": [80, 443],
      "pids": [1234, 5678],
      "process_name": "nginx",
      "container_id": "abc123def456"
    }
  ]
}
            """, language="json")

if __name__ == "__main__":
    main()