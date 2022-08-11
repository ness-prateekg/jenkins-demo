from optparse import Values
from traceback import print_tb
import gitlab
from atlassian import Bitbucket
from pprint import pprint
import numpy as np
import requests
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime
import verify_mirror
import get_repo
import time
load_dotenv()

bitbucket = Bitbucket(
    url=os.getenv("BITBUCKET_URL"),
    username=os.getenv("BITBUCKET_USERNAME"),
    password=os.getenv("BITBUCKET_PASSWORD"),
)

bb_logs = {}
projects = bitbucket.project_list()

gl = gitlab.Gitlab(os.getenv("GITLAB_URL"), os.getenv("GITLAB_TOKEN"))
gl.auth()
gl_logs = {}







def find_repositories():
    found_repos = pd.DataFrame(columns = ['repo_name', 'gl_web_url', 'project_id'])
    not_found_repos = pd.DataFrame(columns = ['repo_name'])
    repos = get_repo.get_groups()
    for repo_name, repo_link  in repos.items():
        if repo_link is np.nan:
            print(f"Error: repo link not found: {repo_name}")
            not_found_repos = pd.concat([not_found_repos, pd.DataFrame([{'repo_name': repo_name}])], ignore_index=True)
        else:
            start_string = '/repos/'
            end_string = '/browse'

            start_index = repo_link.find(start_string) + len(start_string)
            end_index = repo_link.find(end_string)

            # print(repo_name, repo_link[start_index:end_index])
            try:
                gl_repos = gl.projects.list(max_retries=-1, search=repo_link[start_index:end_index], all = True)

                try:
                    repo_idx = [x.attributes['web_url'].rsplit('/', 1)[-1].lower() for x in gl_repos].index(repo_link[start_index:end_index])
                    repo_dict = pd.DataFrame([{'repo_name':repo_name,'gl_web_url':gl_repos[repo_idx].attributes['web_url'], 'project_id':gl_repos[repo_idx].attributes['id']}])
                    found_repos = pd.concat([found_repos, repo_dict], ignore_index=True)
                    # found_repos.append({'repo_name':repo_name,'gl_web_url':gl_repos[repo_idx].attributes['web_url'], 'project_id':gl_repos[repo_idx].attributes['id']}, ignore_index=True)               
                except ValueError as exc:
                    not_found_repos = pd.concat([not_found_repos, pd.DataFrame([{'repo_name': repo_name}])], ignore_index=True)
                    
            except:  
                print(f"no repo exist for Repository: {repo_name}")
        

    # Creating two files to document the found repositories and 404 repositories
    found_repos.to_csv('found_repos.csv', index = False)
    not_found_repos.to_csv('not_found_repos.csv', index = False)




def find_branches(found_repos):
    branch_info = pd.DataFrame(columns = ['repo_name', 'branch_status', 'project_id'])
    for idx, repo in found_repos.iterrows():
        branches = list()
        gl_project = gl.projects.get(repo['project_id'])
        repo_name = repo['repo_name']
        repo_url = repo['gl_web_url'].rsplit('/', 1)[-1]
        print(repo_url)
        group_name = get_repo.get_group_key(repo_name)
        bitbucket_proj = bitbucket.project(group_name) 
        try:
            bb_branch_set = set([x['displayId'] for x in bitbucket.get_branches(bitbucket_proj['key'], repo_url, details=False, limit=999)])
            gl_branch_set = set([x.attributes['name'] for x in gl_project.branches.list(all = True)])
            branch_diff = bb_branch_set.difference(gl_branch_set)
                
            if len(branch_diff) == 0:
                branch_info = pd.concat([branch_info, pd.DataFrame([{'repo_name':repo_name, 'branch_status':"Done",'project_id':repo['project_id'] }])], ignore_index=True)
            else:
                branch_info = pd.concat([branch_info, pd.DataFrame([{'repo_name':repo_name, 'branch_status':",".join(list(branch_diff)), 'project_id':repo['project_id']}])], ignore_index=True)
        except:
            print(f"Error in repo name: {repo_name}")

    branch_info.to_csv('branch_info.csv')

        
def get_commit_info(found_repos):
    counter = 0
    
    for idx, repo in found_repos.iterrows():
        gl_commit_df = pd.DataFrame(columns = ['repo_url','id', 'author', 'displayName', 'emailAddress','authorTimestamp'])
        gl_project = gl.projects.get(repo['project_id'])
        counter += 1
        if counter == 100:
            time.sleep(60)
            counter = 0
        repo_name = repo['repo_name']
        repo_url = repo['gl_web_url'].rsplit('/', 1)[-1]
    # BitBucket Code
        print(repo_url)
        group_name = get_repo.get_group_key(repo_name)
        bitbucket_proj = bitbucket.project(group_name)
        try:
            branch_commits = bitbucket.get_commits(bitbucket_proj['key'], repo_url)
            for commit in branch_commits:
                bb_commits = pd.DataFrame(columns = ['repo_url','id',  'displayId','message','author', 'emailAddress','authorTimestamp', 'status'])
                bb_commit_dict = {'repo_url':repo_url,
                'id':commit.get('id'),
                'displayId':commit.get('displayId'),
                'message': commit["message"].replace("\n", ""),
                'author':commit["author"]['name'].lower(), 
                'emailAddress':commit.get('author').get('emailAddress'),
                'authorTimestamp':commit.get('authorTimestamp')}
                
                # print("BB timestamp",commit.get('authorTimestamp'))
                             
                
                # gl_branch_set = set([x.attributes['name'] for x in gl_project.branches.list(all = True)])
                # for idx, _commit in bb_commits.iterrows():
                short_id = commit['displayId']
                # print(f"GL_{repo_url}__{short_id}")
                try:
                    counter += 1
                    if counter == 100:
                        time.sleep(60)
                        counter = 0
                    gl_commit = gl_project.commits.get(short_id)
                    
                    gl_commit = gl_commit.__dict__["_attrs"]
                    if gl_commit['id'] == commit['id'] and gl_commit['committer_email'].lower() == commit.get('committer').get('emailAddress').lower() and gl_commit['author_email'].lower() == commit.get('author').get('emailAddress').lower():
                        print(f"{repo_url}__{short_id}__commit_present")
                    else:
                        print(f"{repo_url}__{short_id}__commit_unverified")
                        bb_commit_dict = dict(bb_commit_dict, **{'status':'Unmatched'})
                        bb_commits = pd.concat([bb_commits, pd.DataFrame([bb_commit_dict])], ignore_index=True)
                        # get_details(gl_commit, repo_url)
                except Exception as exc:
                    print(f"commit not found for {short_id}")
                    bb_commit_dict = dict(bb_commit_dict, **{'status':'Missing'})
                    bb_commits = pd.concat([bb_commits, pd.DataFrame([bb_commit_dict])], ignore_index=True)
                bb_commits.to_csv(f'./output_commit_logs/{repo_url}.csv', mode='a', index = False, header = False)
        except Exception as exc:
            print(exc)
        
          







found_repos = pd.read_csv('found_repos.csv')
# find_branches(found_repos)
# find_repositories()
# get_commit_info(found_repos)
# verify_users.verify_tags(found_repos, gl, bitbucket)
mirror_check_repos = pd.read_csv('found_repos_3.csv')
# verify_mirror.create_mirror_mapping(gl=gl)
verify_mirror.verify_mirror(found_repos=mirror_check_repos, gl=gl, bitbucket=bitbucket)