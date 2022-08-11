from atlassian import Bitbucket
import gitlab
import get_repo
import pandas as pd
import time
import numpy as np



# Mirror mapping
def create_mirror_mapping(gl: gitlab.Gitlab ):
    found_repos = pd.DataFrame(columns = ['repo_name', 'gl_web_url','bb_url', 'project_id'])
    not_found_repos = pd.DataFrame(columns = ['repo_name'])
    repos = get_repo.get_groups()
    for repo_name, repo_link  in repos.items():
        print(repo_name)
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
                    repo_dict = pd.DataFrame([{'repo_name':repo_name,'gl_web_url':gl_repos[repo_idx].attributes['web_url'],'bb_url':repo_link, 'project_id':gl_repos[repo_idx].attributes['id']}])
                    found_repos = pd.concat([found_repos, repo_dict], ignore_index=True)
                    

                    # found_repos.append({'repo_name':repo_name,'gl_web_url':gl_repos[repo_idx].attributes['web_url'], 'project_id':gl_repos[repo_idx].attributes['id']}, ignore_index=True)               
                except ValueError as exc:
                    not_found_repos = pd.concat([not_found_repos, pd.DataFrame([{'repo_name': repo_name}])], ignore_index=True)
            
            except:  
                print(f"no repo exist for Repository: {repo_name}")

        

    # Creating two files to document the found repositories and 404 repositories
    found_repos.to_csv('found_repos_3.csv', index = False)
    not_found_repos.to_csv('not_found_3.csv', index = False)


def verify_mirror(found_repos, gl: gitlab.Gitlab, bitbucket: Bitbucket ):
    counter = 0   
    for idx, repo in found_repos.iterrows():
        try:
            gl_project = gl.projects.get(repo['project_id'])
        except Exception as exc:
            print(exc, f"Repo not found: {repo}")
        repo_name = repo['repo_name']
        repo_url = repo['gl_web_url'].rsplit('/', 1)[-1]
        print(repo_url)
        group_name = get_repo.get_group_key(repo_name)
        bitbucket_proj = bitbucket.project(group_name)
        bb_repo_data = bitbucket.get_repo(bitbucket_proj['key'], repo_url)
        bb_repo_clone_link = bb_repo_data['links']['clone']
        bb_clone_link = str()
        for link_obj in bb_repo_clone_link:
            if link_obj['name'] == 'http':
                bb_clone_link = link_obj['href']

        if len(gl_project.remote_mirrors.list()) == 0:
            print(gl_project['_links'])
        else:
            print(gl_project.remote_mirrors.list())
        break

        # group_name = get_repo.get_group_key(repo_name)
        # bitbucket_proj = bitbucket.project(group_name)
        # try:

        #     bb_tags = bitbucket.get_tags(bitbucket_proj['key'], repo_url)
        #     for idx, tag in enumerate(bb_tags):
        #         print(idx+1)
        #         try:
        #             bb_tags = pd.DataFrame(columns = ['repo_url','id',  'displayId','type','latestCommit', 'status'])
        #             bb_tags_dict = {'repo_url':repo_url,
        #             'id':tag.get('id'),
        #             'displayId':tag.get('displayId'),
        #             'type': tag["type"],
        #             'latestCommit':tag["latestCommit"]}
        #             gl_tag = gl_project.tags.get(tag['id'].split('/')[-1])
        #             gl_tag = gl_tag.__dict__["_attrs"]
        #             print(gl_tag['commit']['id'])
        #             counter += 1
        #             if counter == 100:
        #                 time.sleep(60)
        #                 counter = 0
        #             if gl_tag['commit']['id'] == tag['latestCommit'] and gl_tag['name'] == tag['displayId']:
        #                 print(f"{repo_url}__{tag['id']}__tag_present")
        #             else:
        #                 print(f"{repo_url}__{tag['id']}__commit_unverified")
        #                 bb_tags_dict = dict(bb_tags_dict, **{'status':'Unmatched'})
        #                 bb_tags = pd.concat([bb_tags, pd.DataFrame([bb_tags_dict])], ignore_index=True)
        #                 bb_tags.to_csv(f'./output_tag_logs/{repo_url}_tags.csv', mode='a', index = False, header = False)
        #         except Exception as exc:
        #             print(f"Tag not found: {tag['id']}")
        #             bb_tags_dict = dict(bb_tags_dict, **{'status':'Missing'})
        #             bb_tags = pd.concat([bb_tags, pd.DataFrame([bb_tags_dict])], ignore_index=True)
        #             bb_tags.to_csv(f'./output_tag_logs/{repo_url}_tags.csv', mode='a', index = False, header = False)
        # except Exception as exc:
        #     print(exc)
        
  