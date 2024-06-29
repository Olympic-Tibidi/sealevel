import streamlit as st
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from pyproj import Transformer
from rasterio.io import MemoryFile
import plotly.graph_objects as go
from google.cloud import storage

TARGET_BUCKET = "new_suzano_spare"

@st.cache(allow_output_mutation=True)
def load_elevation_data():
    """Load and process the elevation data from Google Cloud Storage."""
    client = storage.Client()
    bucket = client.bucket(TARGET_BUCKET)
    blob = bucket.blob("terminal.tif")
    content = blob.download_as_bytes()

    with MemoryFile(content) as memfile:
        with memfile.open() as src:
            geo_bounds = (-122.90612, 47.05128, -122.89835, 47.05930)
            raster_bounds = transform_bounds('EPSG:4326', src.crs, *geo_bounds, densify_pts=21)
            window = src.window(*raster_bounds)
            elevation_data = src.read(1, window=window)
            nodata = src.nodata if src.nodata else -3.402823e+38
            elevation_data = np.where(elevation_data == nodata, np.nan, elevation_data)
            return elevation_data

elevation_data = load_elevation_data()

mllw = -4.43
mhhw = mllw + 14.56
max_tide = st.slider('Max Tide Level', -3.0, 20.0, 0.1) + mllw

if 'fig' not in st.session_state:
    st.session_state.fig = go.Figure()
    st.session_state.fig.add_trace(go.Surface(z=elevation_data, colorscale='Earth', name='Elevation'))
    st.session_state.fig.add_trace(go.Surface(z=np.full(elevation_data.shape, mllw), showscale=False, opacity=1, colorscale=[[0, 'blue'], [1, 'blue']], name='MLLW'))
    st.session_state.fig.add_trace(go.Surface(z=np.full(elevation_data.shape, mhhw), showscale=False, opacity=0.5, colorscale=[[0, 'red'], [1, 'red']], name='MHHW'))
    st.session_state.fig.add_trace(go.Surface(z=np.full(elevation_data.shape, max_tide), showscale=False, opacity=0.5, colorscale=[[0, 'green'], [1, 'green']], name='Max Tide'))

    st.session_state.fig.update_layout(
        title='Marine Terminal Elevation with Tidal Levels',
        autosize=True,
        scene=dict(zaxis=dict(title='Elevation (feet)', range=[-10, np.nanmax(elevation_data) + 10])),
        margin=dict(l=65, r=50, b=65, t=90)
    )

st.plotly_chart(st.session_state.fig, use_container_width=True)
