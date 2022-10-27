import pandas as pd
import csv

data = pd.read_csv('data.csv')

codigo_postal = data['codigo_postal']
z = data['z']


x = [[codigo_postal[i], z[i]] for i in range(len(codigo_postal))]

result = []
for item in x:
    if item not in result:
        result.append(item)

data = pd.DataFrame()
data.index = [rpta[0] for rpta in result]
data['z'] = [rpta[1] for rpta in result]

data.to_csv('data2.csv')

