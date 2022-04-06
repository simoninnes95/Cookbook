import json
import response
import pandas as pd

url = ""
doc = response.get(url).content

out = json.load(doc)
out

df = pd.DataFrame(out)
df.head()

DA Shared Data Gateway

Gateway icon
