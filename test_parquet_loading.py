#!/usr/bin/env python3
"""
Test script to verify Parquet file loading functionality.
"""

import io
import pandas as pd
import geopandas as gpd
from shapely import wkb, wkt
import numpy as np

def test_parquet_loading():
    """Test the Parquet loading logic from the main app."""
    
    # Create a simple test GeoDataFrame
    from shapely.geometry import Point, Polygon
    
    # Create some test geometries
    geometries = [
        Point(0, 0),
        Point(1, 1),
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        Point(2, 2)
    ]
    
    # Create test data
    data = {
        'id': [1, 2, 3, 4],
        'name': ['A', 'B', 'C', 'D'],
        'value': [10.5, 20.3, 15.7, 8.9]
    }
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(data, geometry=geometries, crs="EPSG:4326")
    
    print("Original GeoDataFrame:")
    print(gdf.head())
    print(f"Geometry column type: {type(gdf.geometry.iloc[0])}")
    
    # Save as Parquet
    buffer = io.BytesIO()
    gdf.to_parquet(buffer)
    buffer.seek(0)
    
    print("\nTesting Parquet loading...")
    
    # Test the loading logic from the app
    try:
        # Read with pandas first
        df = pd.read_parquet(buffer, engine='pyarrow')
        print(f"Loaded DataFrame shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        # Find geometry column
        geom_cols = [col for col in df.columns if 'geom' in col.lower()]
        print(f"Geometry columns found: {geom_cols}")
        
        if geom_cols:
            geom_col = geom_cols[0]
            print(f"Using geometry column: {geom_col}")
            print(f"Geometry column dtype: {df[geom_col].dtype}")
            
            # Try to create GeoDataFrame
            try:
                gdf_loaded = gpd.GeoDataFrame(df, geometry=geom_col)
                print("✓ Successfully created GeoDataFrame from Parquet")
                print(f"Loaded GeoDataFrame shape: {gdf_loaded.shape}")
                print(f"CRS: {gdf_loaded.crs}")
                
                # Test geometry conversion to string for display
                display_df = gdf_loaded.copy()
                if 'geometry' in display_df.columns:
                    display_df['geometry'] = display_df['geometry'].astype(str)
                print("✓ Successfully converted geometry to string for display")
                
            except Exception as e:
                print(f"✗ Failed to create GeoDataFrame: {e}")
                
                # Try WKB parsing
                try:
                    geom_series = df[geom_col]
                    print(f"Geometry series dtype: {geom_series.dtype}")
                    print(f"First geometry value type: {type(geom_series.iloc[0])}")
                    
                    if geom_series.dtype == 'object':
                        # Try to parse as WKT first
                        try:
                            geometries_parsed = geom_series.apply(lambda x: wkt.loads(x) if pd.notna(x) else None)
                            print("✓ Successfully parsed as WKT")
                        except:
                            # If WKT fails, try WKB
                            try:
                                geometries_parsed = geom_series.apply(lambda x: wkb.loads(x) if pd.notna(x) else None)
                                print("✓ Successfully parsed as WKB string")
                            except:
                                # If both fail, try to decode bytes
                                geometries_parsed = geom_series.apply(lambda x: wkb.loads(x.encode('latin-1')) if pd.notna(x) else None)
                                print("✓ Successfully parsed as WKB with latin-1 encoding")
                    else:
                        # Handle bytes directly - this is the most common case for Parquet files
                        try:
                            # First try direct WKB parsing
                            geometries_parsed = geom_series.apply(lambda x: wkb.loads(x) if pd.notna(x) else None)
                            print("✓ Successfully parsed as direct WKB")
                        except:
                            # If that fails, try different encodings
                            try:
                                geometries_parsed = geom_series.apply(lambda x: wkb.loads(bytes(x)) if pd.notna(x) else None)
                                print("✓ Successfully parsed as WKB with bytes() conversion")
                            except:
                                try:
                                    geometries_parsed = geom_series.apply(lambda x: wkb.loads(x.tobytes()) if pd.notna(x) else None)
                                    print("✓ Successfully parsed as WKB with tobytes() conversion")
                                except:
                                    # Last resort: try to convert to string first
                                    geometries_parsed = geom_series.apply(lambda x: wkb.loads(str(x).encode('latin-1')) if pd.notna(x) else None)
                                    print("✓ Successfully parsed as WKB with string encoding")
                    
                    df_clean = df.drop(columns=[geom_col])
                    df_clean['geometry'] = geometries_parsed
                    gdf_loaded = gpd.GeoDataFrame(df_clean, geometry='geometry')
                    print("✓ Successfully created GeoDataFrame from parsed geometries")
                    print(f"Loaded GeoDataFrame shape: {gdf_loaded.shape}")
                    print(f"CRS: {gdf_loaded.crs}")
                    
                except Exception as wkb_error:
                    print(f"✗ WKB/WKT parsing failed: {wkb_error}")
        else:
            print("✗ No geometry columns found")
            
    except Exception as e:
        print(f"✗ Parquet loading failed: {e}")

if __name__ == "__main__":
    test_parquet_loading() 