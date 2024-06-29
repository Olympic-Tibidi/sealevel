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

def download_blob_to_memory(bucket_name, source_blob_name):
    """Downloads a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    byte_stream = blob.download_as_bytes()
    return byte_stream
st.title("Marine Terminal Elevation Viewer")
file_name = 'terminal.tif'
data = download_blob_to_memory(target_bucket, file_name)
max_tide_ = st.slider("Select Maximum Tide Level (feet)", float(-4.47), float(30.0), float(18.4))

# Use rasterio to open the file
with MemoryFile(data) as memfile:
    with memfile.open() as src:
        # Define geographic and raster bounds as before
        geo_bounds = (-122.90612, 47.05128, -122.89835, 47.05930)
        raster_bounds = transform_bounds('EPSG:4326', src.crs, *geo_bounds, densify_pts=21)
        window = src.window(*raster_bounds)
        elevation_data = src.read(1, window=window, masked=True)
        elevation_data = np.where(elevation_data.mask, np.nan, elevation_data.data)
        min_elevation = np.nanmin(elevation_data[elevation_data > -1000])
        max_elevation = np.nanmax(elevation_data)
        # Plotting code
        mllw = -4.470
        mhhw = mllw + 14.56
        max_tide=max_tide_+mllw
        fig = go.Figure(data=[go.Surface(z=elevation_data, cmin=min_elevation, cmax=max_elevation, colorscale='Earth')])
        fig.add_trace(go.Surface(z=np.full(elevation_data.shape, mllw), showscale=False, opacity=0.5, colorscale=[[0, 'blue'], [1, 'blue']]))
        fig.add_trace(go.Surface(z=np.full(elevation_data.shape, mhhw), showscale=False, opacity=0.5, colorscale=[[0, 'red'], [1, 'red']]))
        fig.add_trace(go.Surface(z=np.full(elevation_data.shape, max_tide), showscale=False, opacity=0.5, colorscale=[[0, 'green'], [1, 'green']]))
        fig.update_layout(title='Marine Terminal Elevation with Tidal Levels',
                      autosize=True,
                      scene=dict(zaxis=dict(title='Elevation (feet)', range=[-7, max_elevation + 10]),
                                 camera=dict(eye=dict(x=1.87, y=0.88, z=-0.64))),
                      margin=dict(l=65, r=50, b=65, t=90))
        st.plotly_chart(fig)
