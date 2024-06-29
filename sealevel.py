import streamlit as st
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from pyproj import Transformer
from rasterio.io import MemoryFile
import plotly.graph_objects as go
from google.cloud import storage

# Setup your credentials for Google Cloud Storage

storage_client = storage.Client()
@st.cache(allow_output_mutation=True)
def load_data():
    """ Load data from Google Cloud Storage and return processed elevation data. """
    bucket = storage_client.bucket('new_suzano_spare')
    blob = bucket.blob('path/to/your/terminal.tif')
    content = blob.download_as_bytes()
    with MemoryFile(content) as memfile:
        with memfile.open() as src:
            geo_bounds = (-122.90612, 47.05128, -122.89835, 47.05930)
            raster_bounds = transform_bounds('EPSG:4326', src.crs, *geo_bounds, densify_pts=21)
            window = src.window(*raster_bounds)
            data = src.read(1, window=window)
            nodata = src.nodata
            data = np.where(data == nodata, np.nan, data)
            transformer = Transformer.from_crs(src.crs, 'EPSG:4326', always_xy=True)
            width, height = data.shape
            lon, lat = np.meshgrid(np.linspace(geo_bounds[0], geo_bounds[2], width), 
                                   np.linspace(geo_bounds[1], geo_bounds[3], height))
            lon, lat = transformer.transform(lon, lat)
            return data, lon, lat

if 'elevation_data' not in st.session_state:
    data, lon, lat = load_data()
    st.session_state.elevation_data = data
    st.session_state.lon = lon
    st.session_state.lat = lat

mllw = -4.43
mhhw = mllw + 14.56
max_tide = st.slider('Max Tide Level', -3.0, 20.0, 0.1) - 4.43

fig = go.Figure(data=[go.Surface(z=st.session_state.elevation_data, x=st.session_state.lon, y=st.session_state.lat, colorscale='Earth')])
#fig.add_trace(go.Surface(z=np.full(st.session_state.elevation_data.shape, mllw), showscale=False, opacity=0.5, colorscale=[[0, 'blue'], [1, 'blue']], name='MLLW'))
#fig.add_trace(go.Surface(z=np.full(st.session_state.elevation_data.shape, mhhw), showscale=False, opacity=0.5, colorscale=[[0, 'red'], [1, 'red']], name='MHHW'))
#fig.add_trace(go.Surface(z=np.full(st.session_state.elevation_data.shape, max_tide), showscale=False, opacity=0.5, colorscale=[[0, 'green'], [1, 'green']], name='Max Tide'))
if st.checkbox("Show MLLW"):
    fig.add_trace(go.Surface(z=np.full(st.session_state.elevation_data.shape, mllw),x=st.session_state.lon, y=st.session_state.lat, showscale=False, opacity=0.5, colorscale=[[0, 'blue'], [1, 'blue']], name='MLLW'))
fig.update_layout(title='Marine Terminal Elevation with Tidal Levels', autosize=False, scene=dict(zaxis=dict(title='Elevation (feet)')), margin=dict(l=65, r=50, b=65, t=90))

st.plotly_chart(fig, use_container_width=True)
