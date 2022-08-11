
import gitlab
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime
from .get_repo import get_group_key, get_groups
from gitlab.exceptions import GitlabCreateError
from .file_lookup import FileLookup
import xml.etree.ElementTree as ET
from lxml import etree
import time
import base64
# from file_lookup import FileLookup
load_dotenv()




class AutomateDotRSP:
    

    @staticmethod
    def create_branch(gl_project, branch_name, ref):
            branch = gl_project.branches.create({'branch': branch_name,'ref': ref})
            return branch

    @staticmethod
    def check_branch(gl_project, branch_name):
        #checkout gitlab test-msbuild branch
        try:
            branch = gl_project.branches.get(branch_name)
            if branch:
                return True
        except Exception as branch_exc:
            return False
            
    @staticmethod
    def check_path_exists(gl_project,file_path, branch_name):
        try:
            items = gl_project.repository_tree(path=f'{file_path}', ref=branch_name, all = True)
            total_items = []
            total_items.extend(items)
            for item in items:
                if item['type'] == 'tree':
                    temp =  gl_project.repository_tree(path=item['path'], ref=branch_name, all = True)
                    if len(temp)>0:
                        total_items.extend(temp)
            return total_items
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
def traverse_xml(root):
    url_list = ["https://artifactory.actimize.cloud/artifactory/api/nuget/nuget-release-aws-local",
                "https://artifactory.actimize.cloud/artifactory/api/nuget/nuget-thirdparty-local",
                "https://artifactory.actimize.cloud/artifactory/api/nuget/nuget-snapshot-aws-local",
                "https://artifactory.actimize.cloud/artifactory/api/nuget/nuget.org"]
    for package in root:
            tag_name = package.tag
            if 'packagesource' in tag_name.lower():
                # package.findall('add')
                count = 0
                for p in package.findall('add'):
                    p.attrib['value'] =url_list[count]
                    count += 1
                    
    
    tree = ET.ElementTree(root)
    tree.write("temp/temp.xml", encoding = "utf-8", xml_declaration = True) 


def target_xml(root):
    url = "https://artifactory.actimize.cloud/artifactory/api/nuget/nuget-release-aws-local"
    for package in root.iter():
            tag_name = package.tag
            if 'packagesource' in tag_name.lower():
                if 'Include' in package.attrib:
                    package.attrib['Include'] = url
    
    tree = ET.ElementTree(root)
    tree.write("temp/target.xml", encoding = "utf-8", xml_declaration = True, default_namespace="") 
        


def find_file(file_name,project_name_folder, gl_project, branch_name):
            #checkout gitlab test-msbuild branch
            nuget_project_dir = AutomateDotRSP.check_path_exists(gl_project=gl_project,file_path=f"solutions/{project_name_folder}/.nuget", branch_name=branch_name)
            nuget_exists = [x for x in nuget_project_dir if x['name']==file_name]
            if not nuget_exists:
                #Add the repos with no nuget to a list
                with open('nuget_not_found_2.txt', 'a') as f:
                    f.write(f"{project_name_folder} - {file_name}\n")
                print(f"Not found .nuget for {project_name_folder}")
                return False
            else:
                print(f"##################{file_name} exists#########################")
            if len(nuget_exists) != 0:

                return {'file_details':nuget_exists[0]}
                
            else:
                print(f"{file_name} does not exists for {project_name_folder}")
                return False


def reconfigure_nuget_conf(gl_project, project_dict, file_path, branch_name):
    try:
                        
                        #Look up for file 
                        file_lookup = FileLookup(project= gl_project, git_short= project_dict['path_with_namespace'])
                        #project found 
                        file_contents = file_lookup.remote_file(branch=branch_name, filename=file_path)
                        nuconfig_xml_root = ET.fromstring(file_contents)
                        traverse_xml(nuconfig_xml_root)   
    except Exception as exc:
        #Project not found
        print("Exception in reading/writing xml for nuget config: ", exc)  
    



def reconfigure_nugettarget_conf(gl_project, project_dict, file_path, branch_name):
    try:
        file_lookup = FileLookup(project= gl_project, git_short= project_dict['path_with_namespace'])
        #project found 
        file_contents = file_lookup.remote_file(branch=branch_name, filename=file_path)
        ET.register_namespace('', "http://schemas.microsoft.com/developer/msbuild/2003")
        nutarget_xml_root = ET.fromstring(file_contents)
        target_xml(nutarget_xml_root)
    except Exception as exc:
        print("Exception in reading/writing xml for nuget target: ", exc)   
    


if __name__ == '__main__':
    gl = gitlab.Gitlab(os.getenv("GITLAB_URL"), os.getenv("GITLAB_TOKEN"))
    gl.auth()
    gl_logs = {}
    solution = AutomateDotRSP()
    # solution.add_properties_by_name(gl, 5437, "ApplicationFramework.Jobs", type="x64")
    gl_project = gl.projects.get(5771)
    print(solution.check_path_exists(gl_project, file_path='solutions', branch_name='test-msbuild'))
    # solution.add_properties_rsp(gl)