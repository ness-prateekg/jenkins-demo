from atlassian import Bamboo
import pandas as pd
from pprint import pprint
from requests import get
import jenkins
import requests
server = jenkins.Jenkins('https://ilactcje.nice.com/job/FMC/job/CS/', username='abaluapuri',password='A12345678b')
bamboo = Bamboo(url = "http://bamboo.cssrd.local/", username='bbro', password='bbro')


# project_plans = {}
# for project in bamboo.projects(max_results=9999):
#     job_on_bamboo = pd.DataFrame(columns=['job_name','planKey'], index=None)
#     for plan in bamboo.project_plans(project_key=project['key'], max_results=9999):
#         print(plan['shortName'], plan['key'])
#         job_on_bamboo = pd.concat([job_on_bamboo, pd.DataFrame([{'job_name':plan['shortName'],'planKey':plan['key']}])], ignore_index=True)
#     job_on_bamboo.to_csv('jobs_on_bamboo.csv', index = False, header = False, mode='a')


def percent_error(original:int, compare:int):
    percent = abs((original - compare)/original)
    return percent

# jobs_on_bamboo = pd.read_csv('jobs_on_bamboo.csv')
# jobs_on_jenkins = pd.read_csv('40 Jenkin jobs.csv')

def verify_artifacts(jobs_on_bamboo, jobs_on_jenkins):

    for idx, job in jobs_on_jenkins.iterrows():
        job = job.values[0]   
        j_job = job.replace('.','_') 
        j_job_url = f"https://ilactcje.nice.com/job/FMC/job/CS/job/{j_job}/"
        bamboo_plan = jobs_on_bamboo[jobs_on_bamboo['job_name']==job]
        if not bamboo_plan.empty:
            bamboo_plan_key = bamboo_plan.values[0][1]
            print(bamboo_plan_key)
            plan_details = bamboo.project_latest_results(bamboo_plan_key, max_results=1)
            for p in plan_details:
                if p['state']== 'Successful':
                    #request for artifact wth buildnumber
                    response = get(f"http://bamboo.cssrd.local/rest/api/latest/result/{p['buildResultKey']}.json?expand=artifacts", auth = ('bbro','bbro'))
                    response = response.json()
                    artifacts = response['artifacts']['artifact']
                    
                    bamboo_artifacts = [x for x in artifacts if x['link']['href'].split('/')[-1].split('.')[-1]=='msi' or x['link']['href'].split('/')[-1].split('.')[-1]=='zip' or x['link']['href'].split('/')[-1].split('.')[-1]=='nupkg' or x['link']['href'].split('/')[-1].split('.')[-1]=='exe']
            #Jenkins artifacts
            # print(f"{server.get_build_info(j_job, number=9)['artifacts']}")
            jenkins_last_good_build_number = server.get_job_info(name=j_job)['lastCompletedBuild']['number']
            jenkins_artifacts = server.get_build_info(j_job, number=jenkins_last_good_build_number)['artifacts']
            # print(jenkins_artifacts)
            #get jenkins job header
            print(artifacts, jenkins_artifacts)
            if bamboo_artifacts and jenkins_artifacts:
                for art in jenkins_artifacts:
                    df = pd.DataFrame(columns = ['job_name', 'jenkins_job_url', 'is_msi','file_size_j','percent_error','Success','art_found_bamboo'])
                    jenkins_artificat_url = f"https://ilactcje.nice.com/job/FMC/job/CS/job/{j_job}/lastSuccessfulBuild/artifact/{art['relativePath']}"
                    # print(jenkins_artificat_url)
                    jenkins_art_details = requests.head(jenkins_artificat_url,  auth = ('abaluapuri','A12345678b'))
                    jenkins_artifact_size = jenkins_art_details.headers['Content-Length']
                    # check for absolute percent error
                    bamboo_artifact_size = [x for x in bamboo_artifacts if x['link']['href'].split('/')[-1]==art['fileName']]
                    if bamboo_artifact_size:
                        bamboo_artifact_size = bamboo_artifact_size[0]['size']
                    
                        percent_error_bamboo_jenkins = percent_error(int(bamboo_artifact_size), int(jenkins_artifact_size))
                        if percent_error_bamboo_jenkins < 5:
                            df_dict = {'job_name':j_job, 'jenkins_job_url': j_job_url, 'is_msi': art['relativePath'].split('.')[-1]=='msi', 'file_size_j':int(jenkins_artifact_size), 'percent_error':percent_error_bamboo_jenkins,'Success':'True','art_found_bamboo':'True'}
                            df = pd.concat([df, pd.DataFrame([df_dict])], ignore_index=True)
                            print("Artifact well within limit")
                            pprint(df_dict)
                        else:
                            df_dict = {'job_name':j_job, 'jenkins_job_url': j_job_url, 'is_msi': art['relativePath'].split('.')[-1]=='msi', 'file_size_j':int(jenkins_artifact_size), 'percent_error':percent_error_bamboo_jenkins,'Success':'False','art_found_bamboo':'True'}
                            print("Artifact crosses the error threshold")
                        df = pd.concat([df, pd.DataFrame([df_dict])], ignore_index=True)
                        with open('bamboo_jenkins_verification.csv','a') as f:
                            df.to_csv('bamboo_jenkins_verification.csv', mode = 'a',index = False, header = f.tell()==0)
                    else:
                        pass
                        print("Could not find package in bamboo by the name:  ",art['fileName'] )
                        df_dict = {'job_name':j_job, 'jenkins_job_url': j_job_url, 'is_msi': art['relativePath'].split('.')[-1]=='msi', 'file_size_j':int(jenkins_artifact_size), 'percent_error':percent_error_bamboo_jenkins,'Success':'False','art_found_bamboo':'False'}
                        with open('bamboo_jenkins_verification.csv','a') as f:
                            df.to_csv('bamboo_jenkins_verification.csv', mode = 'a',index = False, header = f.tell()==0)
            else:
                print("No artifacts found for job: ", j_job)    
        else:
            print("Plan empty for: ", job)
