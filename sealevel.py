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
            geo_bounds = (-122.90612, 47.05128, -122.89835, 47.05930)  # Adjusted coordinates
    
            # Convert geographic coordinates to the raster's coordinate system
            raster_bounds = transform_bounds('EPSG:4326', src.crs, *geo_bounds, densify_pts=21)
            
            # Crop the raster using the converted bounding box
            window = src.window(*raster_bounds)
            terminal_elevation = src.read(1, window=window)
        
            # Manually set NoData value if it's not being recognized
            nodata_value = src.nodata if src.nodata else -3.402823e+38
            elevation_data = np.where(terminal_elevation == nodata_value, np.nan, terminal_elevation)
        
            # Transformation from raster CRS to geographic coordinates (WGS84)
            transformer = Transformer.from_crs(src.crs, 'EPSG:4326', always_xy=True)
        
            # Generate geographic coordinates for each pixel
            cols, rows = np.meshgrid(np.arange(elevation_data.shape[1]), np.arange(elevation_data.shape[0]))
            flat_rows, flat_cols = rows.ravel(), cols.ravel()  # Flatten the arrays
            xs, ys = src.xy(flat_rows, flat_cols, offset='center')  # Get center coordinates of each pixel
            lon, lat = transformer.transform(xs, ys)  # Transform to geographic coordinates
            lon, lat = np.array(lon), np.array(lat)  # Convert to numpy arrays
            lon, lat = lon.reshape(rows.shape), lat.reshape(rows.shape)  # Reshape back to the original shape
        
            # Define tidal levels adjusted from NAVD88
            mllw = -4.470  # MLLW in feet above NAVD88
            mhhw = mllw + 14.56  # MHHW in feet above MLLW
            maxtide=mllw+18.4
            return elevation_data,lon,lat

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
    st.session_state.fig.add_trace(go.Surface(z=np.full(elevation_data.shape, mllw), showscale=False, opacity=1, colorscale=[[0, 'blue'], [1, 'blue']]))
    st.session_state.fig.add_trace(go.Surface(z=np.full(elevation_data.shape, mhhw), showscale=False, opacity=0.5, colorscale=[[0, 'red'], [1, 'red']]))
    st.session_state.fig.add_trace(go.Surface(z=np.full(elevation_data.shape, maxtide), showscale=False, opacity=0.5, colorscale=[[0, 'green'], [1, 'green']]))
    st.session_state.fig.update_layout(
         title='Marine Terminal Elevation with Tidal Levels',
    autosize=False,  # Disable autosizing to set custom width and height
    width=1200,  # Set the width of the figure
    height=800,  # Set the height of the figure
    scene=dict(zaxis=dict(title='Elevation (feet)')),
    margin=dict(l=65, r=50, b=65, t=90)
)
# Add or update the max tide level surface
st.session_state.fig.for_each_trace(
    lambda trace: trace.update(z=np.full(st.session_state.elevation_data.shape, max_tide)) if trace.name == 'Max Tide' else ()
)

# Plot the figure
st.plotly_chart(st.session_state.fig)
