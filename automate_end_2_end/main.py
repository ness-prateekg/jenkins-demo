from bamboo_jenkins_verification import verify_artifacts
import pandas as pd
import os
from nice_scritps.automate_properties_rsp import AutomateDotRSP
from gitlab.exceptions import GitlabHttpError, GitlabGetError
from nice_scritps.file_lookup import FileLookup
import gitlab
import xml.etree.ElementTree as ET
from lxml import etree
from nice_scritps.automate_properties_rsp import AutomateDotRSP
from jenkins_automate import get_job_details, code_startup, prepare_build_parameters

gl = gitlab.Gitlab(os.getenv("GITLAB_URL"), os.getenv("GITLAB_TOKEN"))
gl.auth()
gl_logs = {}
jobs_on_bamboo = pd.read_csv('jobs_on_bamboo.csv')
jobs_on_jenkins = pd.read_csv('40 Jenkin jobs.csv')


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
    tree.write("./temp.xml", encoding = "utf-8", xml_declaration = True) 


def target_xml(root):
    url = "https://artifactory.actimize.cloud/artifactory/api/nuget/nuget-release-aws-local"
    for package in root.iter():
            tag_name = package.tag
            
            if 'packagesource' == tag_name.lower():
                if package.attrib['Include']:
                    package.attrib['Include'] = url
                else:
                    pass
    tree = ET.ElementTree(root)
    tree.write("target.xml", encoding = "utf-8", xml_declaration = True, default_namespace="") 
        


def find_file(file_name,project_name_folder, gl_project):
            #checkout gitlab test-msbuild branch
            if AutomateDotRSP.check_branch(gl_project=gl_project):
                pass
            else:
                print("Branch not found")
                # create branch
                branch = AutomateDotRSP.create_test_ms_build(gl_project=gl_project)
                branch = branch.__dict__["_attrs"]
            nuget_project_dir = AutomateDotRSP.check_path_exists(gl_project=gl_project,file_path=f"solutions/{project_name_folder}/.nuget")
            nuget_exists = [x for x in nuget_project_dir if x['name']==file_name]
            if not nuget_exists:
                #Add the repos with no nuget to a list
                with open('nuget_not_found.txt', 'a') as f:
                    f.write(f"{project_name_folder} - {file_name}\n")
                print(f"Not found .nuget for {project_name_folder}")
            else:
                print(f"##################{file_name} exists#########################")
            if len(nuget_exists) != 0:

                return {'project_dict':project_dict,'file_details':nuget_exists[0]}
                
            else:
                print(f"{file_name} does not exists for {project_name_folder}")
        


def reconfigure_nuget_conf(gl_project, project_dict, file_path):
    try:
                        
                        #Look up for file 
                        file_lookup = FileLookup(project= gl_project, git_short= project_dict['path_with_namespace'])
                        #project found 
                        file_contents = file_lookup.remote_file(branch='test-msbuild', filename=file_path)
                        nuconfig_xml_root = ET.fromstring(file_contents)
                        traverse_xml(nuconfig_xml_root)   
    except Exception as exc:
        #Project not found
        print(exc)
    



def reconfigure_nugettarget_conf(gl_project, project_dict, file_path):
    try:
                        
                        #Look up for file 
                        file_lookup = FileLookup(project= gl_project, git_short= project_dict['path_with_namespace'])
                        #project found 
                        file_contents = file_lookup.remote_file(branch='test-msbuild', filename=file_path)
                        ET.register_namespace('', "http://schemas.microsoft.com/developer/msbuild/2003")
                        nuconfig_xml_root = ET.fromstring(file_contents)
                        target_xml(nuconfig_xml_root)   
    except Exception as exc:
        #Project not found
        print(exc)




if __name__ == '__main__':
    group_id = 1928
    group = gl.groups.get(group_id, lazy=True)
    #get all projects
    projects = group.projects.list(include_subgroups=True, all=True)
    count = 0
    for project in projects:
        attempt = 0
        while True:
            try:
                project_dict = project.__dict__["_attrs"]
                #get project from gitlab
                gl_project = gl.projects.get(project_dict['id'])
                project_name_folder = project_dict['name']
                print(f"{attempt + 1} try for {project_name_folder}")
                file_details =  find_file(file_name = 'NuGet.Config', project_name_folder=project_name_folder, gl_project=gl_project)
                if file_details:
                    reconfigure_nuget_conf(gl_project=gl_project, project_dict=file_details['project_dict'], file_path=file_details['file_details']['path'])
                    AutomateDotRSP.create_commit(gl_project, project_name_folder, f'solutions/{project_name_folder}/.nuget/NuGet.Config','temp.xml')
                target_file_details = find_file(file_name = 'NuGet.targets', project_name_folder=project_name_folder, gl_project=gl_project)
                if target_file_details:
                    reconfigure_nugettarget_conf(gl_project=gl_project, project_dict=target_file_details['project_dict'], file_path=target_file_details['file_details']['path'])
                    AutomateDotRSP.create_commit(gl_project, project_name_folder, f'solutions/{project_name_folder}/.nuget/NuGet.targets','target.xml')
                
                #Commits have been made in respective files
                #Reconfigure/Create and build jobs
                job_name = project_name_folder.replace('.','_') 
                found_job = get_job_details(job_name=job_name)
                dict_parameters = prepare_build_parameters(git_url="gitlab@tlvgit03.nice.com:ActimizeDeployer/cs-solution.git", git_credential_id='act_fmc_ci_user',jenkins_job_name=job_name,branch = 'testing', jenkinsFile_path='pipeline/cs_solution_generic_build/Jenkinfiles_msbuild.groovy')
                code_startup(dict_parameters, found_job, build = True)
                print(f"Built job: {job_name}")
            except GitlabHttpError as exc:
                print("Got HTTP error ")
                attempt += 1
                continue
            except GitlabGetError as exc:
                print("Got Get error ")
                attempt += 1
                continue
            break
            
    #Verify artifacts of the job on bamboo and jenkins using prebuilt script