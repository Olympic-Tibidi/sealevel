import streamlit as st
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from pyproj import Transformer
from rasterio.io import MemoryFile
import plotly.graph_objects as go
from google.cloud import storage

target_bucket = "new_suzano_spare"

def download_blob_to_memory(bucket_name, source_blob_name):
    """Downloads a blob from the bucket to memory."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    byte_stream = blob.download_as_bytes()
    return byte_stream

def load_elevation_data(data):
    """Load and preprocess elevation data from an in-memory file."""
    with MemoryFile(data) as memfile:
        with memfile.open() as src:
            geo_bounds = (-122.90612, 47.05128, -122.89835, 47.05930)
            raster_bounds = transform_bounds('EPSG:4326', src.crs, *geo_bounds, densify_pts=21)
            window = src.window(*raster_bounds)
            elevation_data = src.read(1, window=window)
            nodata = src.nodata if src.nodata else -3.402823e+38
            elevation_data = np.where(elevation_data == nodata, np.nan, elevation_data)
    return elevation_data

# Load data once and handle transformation for display
if 'elevation_data' not in st.session_state:
    data = download_blob_to_memory(target_bucket, "terminal.tif")
    elevation_data, lons, lats = load_elevation_data(data)
    st.session_state.elevation_data = elevation_data
    st.session_state.lons = lons
    st.session_state.lats = lats

# Slider for max tide level
max_tide = st.slider('Max Tide Level', -3.0, 20.0, 0.1) - 4.43  # Adjusted for MLLW

# Update or create the Plotly figure
if 'fig' not in st.session_state:
    st.session_state.fig = go.Figure()
    st.session_state.fig.add_trace(go.Surface(z=st.session_state.elevation_data, x=st.session_state.lons, y=st.session_state.lats, colorscale='Earth', name='Elevation'))
    st.session_state.fig.update_layout(
        title='Marine Terminal Elevation with Tidal Levels',
        autosize=True,
        scene=dict(zaxis=dict(title='Elevation (feet)')),
        margin=dict(l=65, r=50, b=65, t=90)
    )

# Add or update the max tide level surface
st.session_state.fig.for_each_trace(
    lambda trace: trace.update(z=np.full(st.session_state.elevation_data.shape, max_tide)) if trace.name == 'Max Tide' else ()
)

# Plot the figure
st.plotly_chart(st.session_state.fig)
