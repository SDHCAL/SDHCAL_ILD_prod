import os
import json
import CommonStep as CS
import WriteBashScripts as wbash
import random
import subprocess
import sys

def sub_job_submit(jsdata,job_directory,Njob,real_submit):
    job_file=wbash.create_ddsim_bash_script(jsdata,job_directory,Njob,True)
    if real_submit:
        subprocess.Popen(['bash','-l','-c',"sbatch {0}".format(job_file)])
    
def job_submit(jsdata,job_directory,real_submit):
    for Njob in range(jsdata['JobParameters']['NumberOfJobsPerPoint']):
        sub_job_submit(jsdata,job_directory,Njob,real_submit)
        
def jobLoop(jsdata,level,job_directory,real_submit):
     if level==-1:
        #jobPar=jsdata['JobParameters']
        #job = mySimJob(jsdata,Njobs=jobPar['NumberOfJobsPerPoint'],NeventsperJob=jobPar['NumberOfEventsPerJob'],output_dir=jobPar['output_dir'])
        #submit the job 
        job_submit(jsdata,job_directory,real_submit)
     else:
        loopon=jsdata['JobParameters']['LoopOn'][level]
        for d in loopon['values']:
            jsdata[loopon['what']][loopon['subwhat']]=d
            jobLoop(jsdata,level-1,job_directory,real_submit)
        
if __name__ == '__main__':
    random.seed()
    job_directory="{0}/slurm_jobs".format(os.getcwd())
    CS.mkdir_p(job_directory)
    jsonFile="json/SinglePartSim.json"
    if len(sys.argv)>=2:
        jsonFile=sys.argv[1]
    real_submit=True
    if len(sys.argv)==3:
        real_submit=False
    fp=open(jsonFile)
    js=json.load(fp)
    CS.mkdir_p(wbash.get_output_dir(js))
    jobLoop(js,len(js['JobParameters']['LoopOn'])-1,job_directory,real_submit)

