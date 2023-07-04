import numpy as np
import pandas as pd
from ydata_profiling import ProfileReport
df = pd.read_csv('co2_eda.csv')
profile = ProfileReport(df, title="Pandas Profiling Report")
profile.to_file("your_report.html")
