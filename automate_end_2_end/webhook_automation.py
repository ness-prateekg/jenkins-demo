from nice_scritps.gitlab_utils import AutomateDotRSP
import gitlab
from pprint import pprint
from gitlab.exceptions import GitlabHttpError, GitlabGetError
from dotenv import load_dotenv
from nice_scritps.jenkins_utils import build_job, get_job_details
from nice_scritps.gitlab_utils import find_file, reconfigure_nuget_conf, reconfigure_nugettarget_conf, traverse_xml, target_xml
from nice_scritps.file_lookup import FileLookup
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