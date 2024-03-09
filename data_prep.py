import pandas as pd

df = pd.DataFrame.from_dict(json.loads(json_object), orient='index')
df.reset_index(level=0, inplace=True)
df = pd.json_normalize(df['data'])
print(df.head(10))