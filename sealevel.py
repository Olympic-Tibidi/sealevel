import streamlit as st
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from rasterio.io import MemoryFile
import plotly.graph_objects as go
from google.cloud import storage
import io
import csv

target_bucket="new_suzano_spare"
utc_difference=7

def load_elevation_data(data):
    with MemoryFile(data) as memfile:
        with memfile.open() as src:
            geo_bounds = (-122.90612, 47.05128, -122.89835, 47.05930)
            raster_bounds = transform_bounds('EPSG:4326', src.crs, *geo_bounds, densify_pts=21)
            window = src.window(*raster_bounds)
            elevation_data = src.read(1, window=window, masked=True)
            elevation_data = np.where(elevation_data.mask, np.nan, elevation_data.data)
    return elevation_data

# Initialize session state for elevation data and plot
if 'elevation_data' not in st.session_state or 'fig' not in st.session_state:
    # Assuming 'data' is loaded from your GCS or other source
    data = download_blob_to_memory('your-bucket-name', 'terminal.tif')
    st.session_state.elevation_data = load_elevation_data(data)
    
    # Create the initial plot with static elevation data
    st.session_state.fig = go.Figure(data=[
        go.Surface(z=st.session_state.elevation_data, colorscale='Earth', name='Elevation')
    ])
    st.session_state.fig.update_layout(
        title='Marine Terminal Elevation with Tidal Levels',
        autosize=True,
        scene=dict(
            zaxis=dict(title='Elevation (feet)', range=[-7, np.nanmax(st.session_state.elevation_data) + 10]),
            camera=dict(eye=dict(x=1.87, y=0.88, z=-0.64))
        ),
        margin=dict(l=65, r=50, b=65, t=90)
    )

# Slider to adjust maximum tide level
max_tide = st.slider('Adjust Max Tide Level', -10.0, 30.0, -4.03)

# Update the plot with new max tide level
st.session_state.fig.for_each_trace(
    lambda trace: trace.update(z=np.full(st.session_state.elevation_data.shape, max_tide)) if trace.name == 'Max Tide' else (),
)

# Add or update max tide plane
if 'Max Tide' not in [trace.name for trace in st.session_state.fig.data]:
    st.session_state.fig.add_trace(go.Surface(
        z=np.full(st.session_state.elevation_data.shape, max_tide),
        showscale=False, opacity=0.5, colorscale=[[0, 'green'], [1, 'green']], name='Max Tide'
    ))
else:
    st.session_state.fig.update_traces(
        selector=dict(name='Max Tide'),
        z=np.full(st.session_state.elevation_data.shape, max_tide)
    )

st.plotly_chart(st.session_state.fig)
