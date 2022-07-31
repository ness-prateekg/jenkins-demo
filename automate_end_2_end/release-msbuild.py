from nice_scritps.gitlab_utils import AutomateDotRSP
import gitlab
from gitlab.exceptions import GitlabHttpError, GitlabGetError
from dotenv import load_dotenv
from nice_scritps.jenkins_utils import build_job, get_job_details
from nice_scritps.gitlab_utils import find_file, reconfigure_nuget_conf, reconfigure_nugettarget_conf, traverse_xml, target_xml
from nice_scritps.file_lookup import FileLookup
from gitlab.exceptions import GitlabCreateError
import os









def init_gl():
    pass

if __name__ == '__main__':
   
    gl = gitlab.Gitlab("https://tlvgit03.nice.com/","DkzGKCennR_FkpgLQpF_")
    gl.auth()
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
                print(project_name_folder)
                #Get project branches::::::::::::::::::::::::: maintain a log that there is no release branch
                gl_branch_set = sorted(set([x.attributes['name'] for x in gl_project.branches.list(all = True) if x.attributes['name'].startswith('release') and 'msbuild' not in x.attributes['name']]))
                if len(gl_branch_set) == 0:
                    print(f"Not creating branch for {project_name_folder}")
                    with open("temp/no_release.csv",'a') as f:
                        f.write(f"{project_dict['id']},{project_name_folder}, False")
                        f.write("\n")
                    break
                gl_branch_set = gl_branch_set[-2:]
                for branch in gl_branch_set:
                    #create release-<number>-msbuild if not present
                    if AutomateDotRSP.check_branch(gl_project=gl_project, branch_name=f"{branch}-msbuild"):
                        print(f"Branch found: {branch}-msbuild")
                        branch =  gl_project.branches.get(f"{branch}-msbuild")
                        branch = branch.__dict__["_attrs"]
                    else:
                        print(f"Branch not found: {branch}-msbuild")
                        # create branch
                        branch = AutomateDotRSP.create_branch(gl_project=gl_project, branch_name=f"{branch}-msbuild", ref=branch)
                        branch = branch.__dict__["_attrs"]
                        print(f"Branch created for: {project_name_folder}-{branch['name']}")
                    #create/update properties.rsp from test-msbuild
                    solutions_project_dir = AutomateDotRSP.check_path_exists(gl_project=gl_project,file_path=f"solutions/{project_name_folder}/", branch_name=branch['name'])
                    sln_exists = [x for x in solutions_project_dir if x['name']==f'{project_name_folder}.sln']
                    if len(sln_exists) != 0:
                        solutions_dir =AutomateDotRSP.check_path_exists(gl_project=gl_project,file_path=f"solutions/", branch_name='test-msbuild')
                        rsp_exists = [x for x in solutions_dir if x['name']=='properties.rsp']
                        if len(rsp_exists) != 0: 
                            # print(rsp_exists)
                            properties_path = [x['path'] for x in rsp_exists if x['name']=='properties.rsp'][0]
                            #trigger file lookup
                            file_lookup = FileLookup(project= gl_project, git_short = project_dict['path_with_namespace'])
                            file_contents = file_lookup.remote_file(branch='test-msbuild', filename=properties_path)
                            #store it in a temp file and delete later
                            with open("temp/properties.rsp",'w') as f:
                                f.write(file_contents)
                            try:
                            # Do not create commit for test-msbuild
                                commit = AutomateDotRSP.create_commit(gl_project,
                                repo_name = project_name_folder, 
                                in_file_path = f'solutions/properties.rsp',
                                out_file_path = 'temp/properties.rsp',
                                branch_name=branch['name'])
                                print(commit.__dict__["_attrs"]['id'])
                            except Exception as exc:
                                print(exc)
                        else:
                            print(f"properties.rsp does not exist for {project_name_folder} in test-msbuild")
                            with open("temp/no_properties.txt",'a') as f:
                                f.write(f"No properties.rsp for {project_name_folder} in test-msbuild\n")


                        #nuget.config file changes
                        file_details =  find_file(file_name = 'NuGet.Config', project_name_folder=project_name_folder, gl_project=gl_project, branch_name=branch['name'])
                        if file_details:
                            #recreate nuget.config
                            reconfigure_nuget_conf(gl_project=gl_project, project_dict=project_dict, file_path=file_details['file_details']['path'], branch_name=branch['name'])
                            AutomateDotRSP.create_commit(gl_project, project_name_folder, f'solutions/{project_name_folder}/.nuget/NuGet.Config','temp/temp.xml', branch_name=branch['name'])
                        else:
                            print(f"Could not find Nuget.config for {project_name_folder}")
                        target_file_details =  find_file(file_name = 'NuGet.targets', project_name_folder=project_name_folder, gl_project=gl_project, branch_name=branch['name'])
                        if target_file_details:
                            #recreate nuget.targets
                            reconfigure_nugettarget_conf(gl_project=gl_project, project_dict=project_dict, file_path=file_details['file_details']['path'], branch_name=branch['name'])
                            AutomateDotRSP.create_commit(gl_project, project_name_folder, f'solutions/{project_name_folder}/.nuget/NuGet.targets','temp/target.xml', branch_name=branch['name'])
                        else:
                            print(f"Could not find NuGet.targets for {project_name_folder}")

                        #Trigger jobs with release msbuild branch
                        job_name = project_name_folder.replace('.','_') 
                        found_job = get_job_details(job_name=job_name)
                        build_job(job_name=job_name, repo_branch=branch['name'], slave="Gitlab-Jenkins-slave-msbuild-15-VM")
                        if not found_job:
                            print(f"No job foundfor {project_name_folder} in jenkins")
                            with open("temp/no_job_found.txt",'a') as f:
                                f.write(f"No job found for {project_name_folder} in jenkins\n")
                        else:
                            print(f"Built job: {job_name}")

                    else:
                        print(f"sln file does not exist for {project_name_folder} in test-msbuild")
                        with open("temp/no_sln_file.txt",'a') as f:
                            f.write(f"No sln file for {project_name_folder} in test-msbuild\n")

                    
            except GitlabHttpError as exc:
                print("Got HTTP error ")
                attempt += 1
                continue
            except GitlabGetError as exc:
                print("Got Get error ")
                attempt += 1
                continue
            break