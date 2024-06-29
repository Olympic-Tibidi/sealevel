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
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    byte_stream = blob.download_as_bytes()
    return byte_stream

def load_elevation_data(data):
    with MemoryFile(data) as memfile:
        with memfile.open() as src:
            geo_bounds = (-122.90612, 47.05128, -122.89835, 47.05930)
            raster_bounds = transform_bounds('EPSG:4326', src.crs, *geo_bounds, densify_pts=21)
            window = src.window(*raster_bounds)
            terminal_elevation = src.read(1, window=window)
            nodata_value = src.nodata if src.nodata else -3.402823e+38
            elevation_data = np.where(terminal_elevation == nodata_value, np.nan, terminal_elevation)
            transformer = Transformer.from_crs(src.crs, 'EPSG:4326', always_xy=True)
            cols, rows = np.meshgrid(np.arange(elevation_data.shape[1]), np.arange(elevation_data.shape[0]))
            xs, ys = src.xy(rows.flatten(), cols.flatten(), offset='center')
            lon, lat = transformer.transform(xs, ys)
            return elevation_data, np.array(lon).reshape(rows.shape), np.array(lat).reshape(rows.shape)

if 'elevation_data' not in st.session_state:
    data = download_blob_to_memory(target_bucket, "terminal.tif")
    elevation_data, lon, lat = load_elevation_data(data)
    st.session_state.elevation_data = elevation_data
    st.session_state.lon = lon
    st.session_state.lat = lat
    st.session_state.fig = go.Figure(data=[go.Surface(z=elevation_data, x=lon, y=lat, colorscale='Earth')])
    st.session_state.fig.update_layout(title='Marine Terminal Elevation', autosize=True, width=1200, height=800,
                                       scene=dict(zaxis=dict(title='Elevation (feet)'), xaxis_title='Longitude', yaxis_title='Latitude'))

# Dynamically adjust the max tide level
max_tide_level = st.slider('Max Tide Level', float(np.nanmin(elevation_data)), float(np.nanmax(elevation_data)), step=0.1)
if 'max_tide_plane' in st.session_state:
    st.session_state.fig.data[1].z = np.full_like(elevation_data, max_tide_level)
else:
    max_tide_plane = go.Surface(z=np.full_like(elevation_data, max_tide_level), showscale=False, opacity=0.5, colorscale=[[0, 'blue'], [1, 'blue']])
    st.session_state.fig.add_trace(max_tide_plane)
    st.session_state.max_tide_plane = max_tide_plane

st.plotly_chart(st.session_state.fig)
