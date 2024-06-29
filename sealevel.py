import streamlit as st
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from pyproj import Transformer
from rasterio.io import MemoryFile
import plotly.graph_objects as go
from google.cloud import storage

# Setup
target_bucket = "your_bucket_name"

# Download blob function
def download_blob_to_memory(bucket_name, source_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    byte_stream = blob.download_as_bytes()
    return byte_stream

# Load elevation data function
def load_elevation_data(data):
    with MemoryFile(data) as memfile:
        with memfile.open() as src:
            # Geographic and raster bounds
            geo_bounds = (-122.90612, 47.05128, -122.89835, 47.05930)
            raster_bounds = transform_bounds('EPSG:4326', src.crs, *geo_bounds, densify_pts=21)
            window = src.window(*raster_bounds)
            elevation_data = src.read(1, window=window)
            nodata = src.nodata if src.nodata else -3.402823e+38
            elevation_data = np.where(elevation_data == nodata, np.nan, elevation_data)
            return elevation_data

# Streamlit app
data = download_blob_to_memory(target_bucket, "terminal.tif")
elevation_data = load_elevation_data(data)
min_elev, max_elev = np.nanmin(elevation_data), np.nanmax(elevation_data)
fig = go.Figure(data=[go.Surface(z=elevation_data, colorscale='Earth', cmin=min_elev, cmax=max_elev)])
fig.update_layout(title='Elevation Plot', autosize=True)
st.plotly_chart(fig)
