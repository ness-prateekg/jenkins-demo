import pandas as pd


df = pd.read_csv('temp/tokens.csv', index_col=None)
df = df[['url','tokens']]
df['job_name'] = df['url'].apply(lambda x: x.split('/')[-2])
df['url'] = df['url'].apply(lambda x: x.replace('job/','').replace('ilactcje.nice.com/', 'ilactcje.nice.com/project/'))
df.to_csv('temp/token_modified.csv', index=False)