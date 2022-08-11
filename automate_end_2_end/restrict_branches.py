from nice_scripts.gitlab_utils import AutomateDotRSP
import gitlab
from pprint import pprint
from gitlab.exceptions import GitlabHttpError, GitlabGetError
from dotenv import load_dotenv
from nice_scripts.jenkins_utils import build_job, get_job_details
from nice_scripts.gitlab_utils import find_file, reconfigure_nuget_conf, reconfigure_nugettarget_conf, traverse_xml, target_xml
from nice_scripts.file_lookup import FileLookup
from jenkins import NotFoundException
from gitlab.exceptions import GitlabCreateError
import os



def init_gl():
    gl = gitlab.Gitlab(os.getenv("GITLAB_URL"), os.getenv("GITLAB_TOKEN"))
    gl.auth()
    return gl


if __name__ == '__main__':
   
    gl = init_gl()
    gl_logs = {}
    group_id = 1928 #cs group id
    group = gl.groups.get(group_id, lazy=True)
    #get all projects
    projects = group.projects.list(include_subgroups=True, all=True)
    # count = 0
    for project in projects:
        attempt = 0
        while True:
            print(f"Attempt number: {attempt + 1}")
            try:
                project_dict = project.__dict__["_attrs"]
                #get project from gitlab
                gl_project = gl.projects.get(project_dict['id'])
                project_name_folder = project_dict['name']
                print(project_name_folder)
                gl_branch_set = sorted(set([x.attributes['name'] for x in gl_project.branches.list(all = True) if x.attributes['name'].startswith('release') and 'msbuild' not in x.attributes['name'] 
                                            or x.attributes['name'] == 'master'
                                            or 'hotfix' in x.attributes['name']]))
                if len(gl_branch_set) == 0:
                    print(f"Not creating branch for {project_name_folder}")
                    with open("temp/no_branch.csv",'a') as f:
                        f.write(f"{project_dict['id']},{project_name_folder}, False")
                        f.write("\n")
                    break
                for branch in gl_branch_set:
                    try:
                        gl_project.protectedbranches.create({
                            'name':branch,
                            'merge_access_level': gitlab.const.AccessLevel.MAINTAINER,
                            'push_access_level': gitlab.const.AccessLevel.MAINTAINER
                        })

                        print(f"Protected branch: {branch} for {project_name_folder}")
                        
                    except GitlabCreateError as exc:
                        print(f"Branch: {branch} already protected")
                        print(exc)
                    
            except GitlabHttpError as exc:
                print("Got HTTP error ")
                attempt += 1
                continue
            except GitlabGetError as exc:
                print("Got Get error ")
                attempt += 1
                continue
            break