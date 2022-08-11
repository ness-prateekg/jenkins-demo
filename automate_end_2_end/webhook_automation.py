from nice_scripts.gitlab_utils import AutomateDotRSP
import gitlab
import pandas as pd
from pprint import pprint
from gitlab.exceptions import GitlabHttpError, GitlabGetError
from dotenv import load_dotenv
from nice_scripts.jenkins_utils import build_job, get_job_details
from nice_scripts.gitlab_utils import find_file, reconfigure_nuget_conf, reconfigure_nugettarget_conf, traverse_xml, target_xml
from nice_scripts.file_lookup import FileLookup
from jenkins import NotFoundException
from gitlab.exceptions import GitlabCreateError
import os
if os.path.exists("temp/webhook_exc.txt"):
            os.remove("temp/webhook_exc.txt")
            print("The file has been deleted successfully")


df = pd.read_csv('temp/token_modified.csv')

def init_gl():
    gl = gitlab.Gitlab(os.getenv("GITLAB_URL"), os.getenv("GITLAB_TOKEN"))
    gl.auth()
    return gl


def configure_webhook(project,job_name):
    job_df = df[df['job_name'].map(lambda x: x.lower())==job_name.lower()]
    if job_df.empty:
        print(f"No job named: {job_name} found in the sheet")
        #Remove file if already exists
        with open("temp/webhook_exc.txt",'a') as f:
            f.write(f"No job found for {job_name} in jenkins job sheet\n") 
    else:
        #code if job found in csv
        print(f"Job found for: {job_name}")
        webhook_url = job_df['url'].values[0]
        webhook_secret_token = job_df['tokens'].values[0]
        try:
            hooks = project.hooks.list()
            for hook in hooks:
                hook.delete()
            #master webhook
            hook = project.hooks.create({'url': webhook_url, 'push_events': 1,
             'enable_ssl_verification':0,
             'token':webhook_secret_token,
             'push_events_branch_filter':'master'})
            hook.save()

            #release webhook
            hook = project.hooks.create({'url': webhook_url, 'push_events': 1,
             'enable_ssl_verification':0,
             'token':webhook_secret_token,
             'push_events_branch_filter':'*release*'})
            hook.save()
            print(f"webhooks saved for job: {job_name}")
        except Exception as exc:
            print(exc)

if __name__ == '__main__':
   
    gl = init_gl()
    gl_logs = {}
    group_id = 1928 #cs group id
    group = gl.groups.get(group_id, lazy=True)
    #get all projects
    projects = group.projects.list(include_subgroups=True, all=True)
    for project in projects:
        attempt = 0
        while True:
            try:
                project_dict = project.__dict__["_attrs"]
                #get project from gitlab
                gl_project = gl.projects.get(project_dict['id'])
                project_name_folder = project_dict['name']
                jenkins_job_name = project_name_folder.replace('.','_') 
                configure_webhook(gl_project, jenkins_job_name) #replace the name of job here
                


            except GitlabHttpError as exc:
                print("Got HTTP error ")
                attempt += 1
                continue
            except GitlabGetError as exc:
                print("Got Get error ")
                attempt += 1
                continue
            break