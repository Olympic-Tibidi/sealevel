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

def load_data(data):
    
    with MemoryFile(data) as memfile:
        with memfile.open() as src:
            # Define the geographic coordinates of your terminal's updated bounding box
            geo_bounds = (-122.90612, 47.05128, -122.89835, 47.05930)  # Adjusted coordinates
            
            # Convert geographic coordinates to the raster's coordinate system
            raster_bounds = transform_bounds('EPSG:4326', src.crs, *geo_bounds, densify_pts=21)
            
            # Crop the raster using the converted bounding box
            window = src.window(*raster_bounds)
            terminal_elevation = src.read(1, window=window)
        
            # Manually set NoData value if it's not being recognized
            nodata_value = src.nodata if src.nodata else -3.402823e+38
            elevation_data = np.where(terminal_elevation == nodata_value, np.nan, terminal_elevation)
            elevation_data = elevation_data[:, ::-1]
            # Filter to ignore extreme values by defining a sensible elevation range
            min_elevation = np.nanmin(elevation_data[elevation_data > -1000])
            max_elevation = np.nanmax(elevation_data)
            return elevation_data,min_elevation,max_elevation


elevation_data,min_elevation,max_elevation=load_data( download_blob_to_memory(target_bucket, "terminal.tif"))
# Define tidal levels adjusted from NAVD88
mllw = -4.43  # MLLW in feet above NAVD88
mhhw = mllw + 14.56  # MHHW in feet above MLLW
maxtide=mllw+18.4
max_tide_level = st.slider('Max Tide Level', float(np.nanmin(elevation_data)), float(np.nanmax(elevation_data)), step=0.1)+mllw
    # Create the plot using Plotly


fig = go.Figure(data=[go.Surface(z=elevation_data, cmin=min_elevation, cmax=max_elevation, colorscale='Earth')])

# Add MLLW and MHHW planes
fig.add_trace(go.Surface(z=np.full(elevation_data.shape, mllw), showscale=False, opacity=1, colorscale=[[0, 'blue'], [1, 'blue']]))
fig.add_trace(go.Surface(z=np.full(elevation_data.shape, mhhw), showscale=False, opacity=0.5, colorscale=[[0, 'red'], [1, 'red']]))
fig.add_trace(go.Surface(z=np.full(elevation_data.shape, maxtide), showscale=False, opacity=0.5, colorscale=[[0, 'green'], [1, 'green']]))

# Update layout to adjust view and axis
fig.update_layout(
    title='Marine Terminal Elevation with Tidal Levels',
    autosize=True,
    scene=dict(
        zaxis=dict(title='Elevation (feet)', range=[-7, max_elevation + 10]),
        camera=dict(eye=dict(x=1.87, y=0.88, z=-0.64))
    ),
    margin=dict(l=65, r=50, b=65, t=90)
)
#fig.write_html('marine_terminal_elevation_with_tides.html')
fig.show()
# Dynamically adjust the max tide level

if 'max_tide_plane' in st.session_state:
    st.session_state.fig.data[1].z = np.full_like(elevation_data, max_tide_level)
else:
    max_tide_plane = go.Surface(z=np.full_like(elevation_data, max_tide_level), showscale=False, opacity=0.5, colorscale=[[0, 'blue'], [1, 'blue']])
    st.session_state.fig.add_trace(max_tide_plane)
    st.session_state.max_tide_plane = max_tide_plane

st.plotly_chart(st.session_state.fig)
