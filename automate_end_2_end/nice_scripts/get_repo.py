import pandas as pd


def get_groups():
    data = pd.read_csv('repos_bb.csv', sep='\t')
    project_name = list(data['Project Name'])
    repo_link = list(data['Bitbucket Clone URL'])
    return dict(zip(project_name, repo_link))

def get_group_key(repo_name):
    data = pd.read_csv('repos_bb.csv', sep='\t')
    data = data[data['Project Name'] == repo_name]
    if data['Bitbucket Group Name'].values is not None:
        # adding logic to extratc group
        return data['Bitbucket Clone URL'].values[0].split('/')[4]
    return f"Group not found for {repo_name}"

