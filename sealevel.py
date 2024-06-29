import streamlit as st
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from rasterio.io import MemoryFile
import plotly.graph_objects as go
from google.cloud import storage

# Configuration and constants
TARGET_BUCKET = "new_suzano_spare"
TIF_FILE = "terminal.tif"

# Streamlit page configuration
st.set_page_config(layout="wide")

@st.cache(allow_output_mutation=True)
def load_data():
    """Loads data from Google Cloud Storage and processes it."""
    # Connect to Google Cloud Storage
    client = storage.Client()
    bucket = client.get_bucket(TARGET_BUCKET)
    blob = bucket.blob(TIF_FILE)
    content = blob.download_as_bytes()

    # Load the raster file from in-memory data
    with MemoryFile(content) as memfile:
        with memfile.open() as src:
            geo_bounds = (-122.90612, 47.05128, -122.89835, 47.05930)
            raster_bounds = transform_bounds('EPSG:4326', src.crs, *geo_bounds, densify_pts=21)
            window = src.window(*raster_bounds)
            elevation_data = src.read(1, window=window, masked=True)
            elevation_data = np.where(elevation_data == src.nodata, np.nan, elevation_data)

    return elevation_data[:, ::-1]  # Flip if necessary

# Load elevation data
elevation_data = load_data()
min_elevation, max_elevation = np.nanmin(elevation_data), np.nanmax(elevation_data)

# UI for tidal adjustments
mllw = st.slider('MLLW Level', -10.0, 10.0, -4.43)
mhhw = mllw + 14.56
max_tide = st.slider('Max Tide Level', -10.0, 30.0, 14.0)

# Create the plot
fig = go.Figure(data=[
    go.Surface(z=elevation_data, cmin=min_elevation, cmax=max_elevation, colorscale='Earth')
])
fig.add_trace(go.Surface(z=np.full(elevation_data.shape, mllw), showscale=False, opacity=0.5, colorscale=[[0, 'blue'], [1, 'blue']]))
fig.add_trace(go.Surface(z=np.full(elevation_data.shape, mhhw), showscale=False, opacity=0.5, colorscale=[[0, 'red'], [1, 'red']]))
fig.add_trace(go.Surface(z=np.full(elevation_data.shape, max_tide), showscale=False, opacity=0.5, colorscale=[[0, 'green'], [1, 'green']]))

# Layout adjustments
fig.update_layout(
    title='Marine Terminal Elevation with Tidal Levels',
    autosize=True,
    scene=dict(zaxis=dict(title='Elevation (feet)', range=[-7, max_elevation + 10])),
    margin=dict(l=65, r=50, b=65, t=90)
)

# Display the plot
st.plotly_chart(fig, use_container_width=True)
