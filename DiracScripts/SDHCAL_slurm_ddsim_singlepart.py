import os
import json
import CommonStep as CS
import random

def mkdir_p(dir):
    '''make a directory (dir) if it doesn't exist'''
    if not os.path.exists(dir):
        os.mkdir(dir)


def sub_job_submit(jsdata,job_directory,Njob):
    million=1000000
    myRandom=random.randint(million,100*million)
    fileBase="ddsim"
    loopOn=jsdata['jobParameters']['LoopOn']
    for d in loopOn:
        fileBase+="_{0}_{1}".format(d['subwhat'],jsdata[d['what']][d['subwhat']])
    fileBase+="_{0}".format(Njob)
    job_file=os.path.join(job_directory,"{0}.job".format(fileBase))
    fich=open(job_file,'w')
    fich.write("#!/bin/bash\n")
    fich.write("#SBATCH --job-name=ddsim\n")
    fich.write("#SBATCH --ntasks=1\n")
    fich.write("#SBATCH --time=24:00:00\n")
    fich.write("#SBATCH --mail-type=ALL\n")  
    fich.write("#SBATCH --mail-user={0}\n".format(os.environ['USER_MAIL']))
    fich.write("#SBATCH --output=ddsim_%j.out\n")
    fich.write("#SBATCH --error=ddsim_%j.out\n\n")
    fich.write("source /cvmfs/ilc.desy.de/sw/{0}/init_ilcsoft.sh\n".format(jsdata['SoftwareVersions']['slurm_ilcsoftVersion']))
    lcgeo_detector=jsdata['Detector']['DetectorName']
    #human_detector=CS.detectorName(lcgeo_detector)
    outputFile=os.path.join(jsdata['jobParameters']['output_dir'],"{0}.slcio".format(fileBase))
    fich.write("rm {0}\n".format(outputFile))
    command="ddsim --compactFile $lcgeo_DIR/ILD/compact/{0}/{0}.xml ".format(lcgeo_detector)
    command+=CS.extraCLIargument(jsdata)
    command+=" --steeringFile /cvmfs/ilc.desy.de/sw/ILDConfig/{0}/StandardConfig/production/ddsim_steer.py".format(jsdata['SoftwareVersions']['ILDConfigVersion'])
    command+=" --numberOfEvents {0} --random.seed {1}".format(jsdata['jobParameters']['NumberOfEventsPerJob'],myRandom)
    command+=" --outputFile {0}".format(outputFile)
    fich.write("{0}\n".format(command))

    os.system("chmod +x {0}".format(job_file))
    os.system("sbatch {0}".format(job_file))
    
def job_submit(jsdata,job_directory):
    for Njob in range(jsdata['jobParameters']['NumberOfJobsPerPoint']):
        sub_job_submit(jsdata,job_directory,Njob)
        
def jobLoop(jsdata,level,job_directory):
     if level==-1:
        #jobPar=jsdata['jobParameters']
        #job = mySimJob(jsdata,Njobs=jobPar['NumberOfJobsPerPoint'],NeventsperJob=jobPar['NumberOfEventsPerJob'],output_dir=jobPar['output_dir'])
        #submit the job 
        job_submit(jsdata,job_directory)
     else:
        loopon=jsdata['jobParameters']['LoopOn'][level]
        for d in loopon['values']:
            jsdata[loopon['what']][loopon['subwhat']]=d
            jobLoop(jsdata,level-1,job_directory)
        
if __name__ == '__main__':
    random.seed()
    job_directory="{0}/slurm_jobs".format(os.getcwd())
    mkdir_p(job_directory)
    fp=open("json/SinglePartSim.json")
    js=json.load(fp)
    mkdir_p(js['jobParameters']['output_dir'])
    jobLoop(js,len(js['jobParameters']['LoopOn'])-1,job_directory)

