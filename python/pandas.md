# Breaking up big csv files

dfs = pd.read_csv('/home/user/Downloads/CIS_Automotive_Kaggle_Sample.csv', sep=',', chunksize=20000)

count = 1

for chunk in dfs:
    chunk.to_csv(f'/home/user/Downloads/CIS_Automotive_Kaggle_Sample_{count}.csv')
    count += 1