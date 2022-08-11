
import gitlab
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime
from get_repo import get_group_key, get_groups
from gitlab.exceptions import GitlabCreateError
import time
import base64
# from file_lookup import FileLookup
load_dotenv()




class AutomateDotRSP:
    

    @staticmethod
    def create_test_ms_build(gl_project):
            branch = gl_project.branches.create({'branch': 'test-msbuild','ref': 'master'})
            return branch

    @staticmethod
    def check_branch(gl_project):
        #checkout gitlab test-msbuild branch
        try:
            branch = gl_project.branches.get('test-msbuild')
            if branch:
                return True
        except Exception as branch_exc:
            #create branch
            print(branch_exc)
            return False
            
    @staticmethod
    def check_path_exists(gl_project,file_path):
        try:
            items = gl_project.repository_tree(path=f'{file_path}', ref='test-msbuild')
            return items
        except Exception as exc:
            print(exc)


    @staticmethod
    def create_commit(gl_project, repo_name, in_file_path, out_file_path, branch_name='test-msbuild'):
        data = {
            'branch': branch_name,
            'commit_message': f"Added {in_file_path} for {repo_name}",
            'actions': [
                {
                    'action': 'create',
                    'file_path': in_file_path,
                    'content': open(out_file_path).read(),
                }
            ]
        }
        try:
            commit = gl_project.commits.create(data)
        except GitlabCreateError as exc:
            print("File already exists")
            data['actions'][0]['action'] = 'update'
            commit = gl_project.commits.create(data)
        return commit

    

    def add_properties_rsp(self, gl):
        #cs group id: 1928
        group_id = 1928
        group = gl.groups.get(group_id, lazy=True)
        #get all projects
        projects = group.projects.list(include_subgroups=True, all=True)
        for project in projects:
            try:
                project_dict = project.__dict__["_attrs"]
                #get project from gitlab
                gl_project = gl.projects.get(project_dict['id'])
                project_name_folder = project_dict['name']
                print(project_name_folder)
                #checkout gitlab test-msbuild branch
                if AutomateDotRSP.check_branch(gl_project=gl_project):
                    print("Branch found")
                else:
                    print("Branch not found")
                    #create branch
                    branch = AutomateDotRSP.create_test_ms_build(gl_project=gl_project)
                    branch = branch.__dict__["_attrs"]
                solutions_project_dir = AutomateDotRSP.check_path_exists(gl_project=gl_project,file_path=f"solutions/{project_name_folder}/")
                sln_exists = [x for x in solutions_project_dir if x['name']==f'{project_name_folder}.sln']
                if len(sln_exists) != 0:
                    solutions_dir =AutomateDotRSP.check_path_exists(gl_project=gl_project,file_path=f"solutions/")
                    rsp_exists = [x for x in solutions_dir if x['name']=='properties.rsp']
                    if len(rsp_exists) == 0: 
                        print(rsp_exists)
                        try:
                            commit = AutomateDotRSP.create_commit(gl_project=gl_project, repo_name=project_name_folder)
                            print(commit.__dict__["_attrs"]['id'])
                        except Exception as exc:
                            print(exc)
                    else:
                        print(f"properties.rsp exists for {project_name_folder}")
                                                
                else:
                    print("Possible java job")
            except Exception as exc:
                print("Repo not found", exc)
            
    def add_properties_by_name(self, gl:gitlab.Gitlab, project_id, project_name_folder, type):
        try:
            gl_project = gl.projects.get(project_id)
        except Exception as exc:
            print("Repo not found", exc)
        if AutomateDotRSP.check_branch(gl_project=gl_project):
            print("Branch found")
        else:
            print("Branch not found")
            #create branch
            branch = AutomateDotRSP.create_test_ms_build(gl_project=gl_project)
            branch = branch.__dict__["_attrs"]
        solutions_project_dir = AutomateDotRSP.check_path_exists(gl_project=gl_project,file_path=f"solutions/{project_name_folder}/")
        sln_exists = [x for x in solutions_project_dir if x['name']==f'{project_name_folder}.sln']
        print(sln_exists)
        if len(sln_exists) != 0:
            solutions_dir =AutomateDotRSP.check_path_exists(gl_project=gl_project,file_path=f"solutions/")
            rsp_exists = [x for x in solutions_dir if x['name']=='properties.rsp']
            if len(rsp_exists) == 0: 
                print(rsp_exists)
            else:
                print(f"properties.rsp exists for {project_name_folder}")
            in_file_path = 'solutions/properties.rsp'
            out_file_path = ''
            try:
                if type =='x86':
                    out_file_path = 'properties_x86.rsp'
                elif type == 'x64':
                    out_file_path = 'properties_x64.rsp'
                else:
                    out_file_path = 'properties_release.rsp'
                commit = AutomateDotRSP.create_commit(gl_project=gl_project, repo_name=project_name_folder, in_file_path=in_file_path, out_file_path=out_file_path)
                print(commit.__dict__["_attrs"]['id'])
            except Exception as exc:
                print(exc)
                                            
        else:
            print("Possible java job")
        
    #add file

    #commit file 

    #push file to test-msbuild

    #print done


if __name__ == '__main__':
    gl = gitlab.Gitlab(os.getenv("GITLAB_URL"), os.getenv("GITLAB_TOKEN"))
    gl.auth()
    gl_logs = {}
    solution = AutomateDotRSP()
    solution.add_properties_by_name(gl, 5437, "ApplicationFramework.Jobs", type="x64")
    # solution.add_properties_rsp(gl)