from atlassian import Bitbucket
import gitlab
import get_repo
import pandas as pd
import time


def verify_tags(found_repos, gl: gitlab.Gitlab , bitbucket: Bitbucket):
    counter = 0   
    for idx, repo in found_repos.iterrows():
        gl_project = gl.projects.get(repo['project_id'])
        repo_name = repo['repo_name']
        repo_url = repo['gl_web_url'].rsplit('/', 1)[-1]
        print(repo_url)
        group_name = get_repo.get_group_key(repo_name)
        bitbucket_proj = bitbucket.project(group_name)
        try:

            bb_tags = bitbucket.get_tags(bitbucket_proj['key'], repo_url)
            for idx, tag in enumerate(bb_tags):
                print(idx+1)
                try:
                    bb_tags = pd.DataFrame(columns = ['repo_url','id',  'displayId','type','latestCommit', 'status'])
                    bb_tags_dict = {'repo_url':repo_url,
                    'id':tag.get('id'),
                    'displayId':tag.get('displayId'),
                    'type': tag["type"],
                    'latestCommit':tag["latestCommit"]}
                    gl_tag = gl_project.tags.get(tag['id'].split('/')[-1])
                    gl_tag = gl_tag.__dict__["_attrs"]
                    print(gl_tag['commit']['id'])
                    counter += 1
                    if counter == 100:
                        time.sleep(60)
                        counter = 0
                    if gl_tag['commit']['id'] == tag['latestCommit'] and gl_tag['name'] == tag['displayId']:
                        print(f"{repo_url}__{tag['id']}__tag_present")
                    else:
                        print(f"{repo_url}__{tag['id']}__commit_unverified")
                        bb_tags_dict = dict(bb_tags_dict, **{'status':'Unmatched'})
                        bb_tags = pd.concat([bb_tags, pd.DataFrame([bb_tags_dict])], ignore_index=True)
                        bb_tags.to_csv(f'./output_tag_logs/{repo_url}_tags.csv', mode='a', index = False, header = False)
                except Exception as exc:
                    print(f"Tag not found: {tag['id']}")
                    bb_tags_dict = dict(bb_tags_dict, **{'status':'Missing'})
                    bb_tags = pd.concat([bb_tags, pd.DataFrame([bb_tags_dict])], ignore_index=True)
                    bb_tags.to_csv(f'./output_tag_logs/{repo_url}_tags.csv', mode='a', index = False, header = False)
        except Exception as exc:
            print(exc)
        
  