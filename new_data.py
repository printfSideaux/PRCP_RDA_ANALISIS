import numpy as np
import pandas as pd
import os
import geopandas as gpd 


def create_new_data(df: pd.DataFrame):
    #conjuto de dados utilizados juntos em um df
    new_data = pd.DataFrame({
        'A': np.random.rand(10),
        'B': np.random.rand(10)
    })
    return new_data


    

    