import streamlit as st
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from rasterio.io import MemoryFile
import plotly.graph_objects as go
from google.cloud import storage
target_bucket="new_suzano_spare"
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
            return elevation_data[:, ::-1]  # Return flipped data if needed

# Initialize the elevation data and the figure in Streamlit's state if not already loaded
if 'elevation_data' not in st.session_state:
    data = download_blob_to_memory(target_bucket, "terminal.tif")
    st.session_state.elevation_data = load_elevation_data(data)

# Setup the interactive components and the plot
mllw = -4.03

mhhw = mllw + 14.56
max_tide=st.slider('MLLW Level', -3.0, 20.0,0.1)+mllw

# Create or update the Plotly figure
if 'fig' not in st.session_state:
    st.session_state.fig = go.Figure()
    st.session_state.fig.add_trace(go.Surface(z=st.session_state.elevation_data, colorscale='Earth', name='Elevation'))
    st.session_state.fig.update_layout(
        title='Marine Terminal Elevation with Tidal Levels',
        autosize=True,
        scene=dict(zaxis=dict(title='Elevation (feet)')),
        margin=dict(l=65, r=50, b=65, t=90)
    )

# Update the tidal planes dynamically
st.session_state.fig.data = [st.session_state.fig.data[0]]  # Keep only the elevation data
st.session_state.fig.add_trace(go.Surface(z=np.full(st.session_state.elevation_data.shape, mllw), showscale=False, opacity=0.5, colorscale=[[0, 'blue'], [1, 'blue']], name='MLLW'))
st.session_state.fig.add_trace(go.Surface(z=np.full(st.session_state.elevation_data.shape, mhhw), showscale=False, opacity=0.5, colorscale=[[0, 'red'], [1, 'red']], name='MHHW'))
st.session_state.fig.add_trace(go.Surface(z=np.full(st.session_state.elevation_data.shape, max_tide), showscale=False, opacity=0.5, colorscale=[[0, 'red'], [1, 'red']], name='MHHW'))

st.plotly_chart(st.session_state.fig)
