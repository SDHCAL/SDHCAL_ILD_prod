import os
import json
import CommonStep as CS
import random
import subprocess
import sys

def sub_job_submit(jsdata,job_directory,Njob):
    million=1000000
    myRandom=random.randint(million,100*million)
    fileBase="ddsim"
    loopOn=jsdata['jobParameters']['LoopOn']
    for d in loopOn:
        value=jsdata[d['what']][d['subwhat']]
        if d['subwhat']=='DetectorName':
            value=CS.detectorName(value)
        fileBase+="_{0}_{1}".format(d['subwhat'],value)
    fileBase+="_{0}".format(Njob)
    job_file=os.path.join(job_directory,"{0}.sh".format(fileBase))
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
    outputFile=os.path.join(jsdata['jobParameters']['output_dir'],"{0}.slcio".format(fileBase))
    fich.write("rm {0}\n".format(outputFile))
    command="ddsim --compactFile $lcgeo_DIR/ILD/compact/{0}/{0}.xml ".format(lcgeo_detector)
    command+=CS.extraCLIargument(jsdata)
    command+=" --steeringFile /cvmfs/ilc.desy.de/sw/ILDConfig/{0}/StandardConfig/production/ddsim_steer.py".format(jsdata['SoftwareVersions']['ILDConfigVersion'])
    command+=" --numberOfEvents {0} --random.seed {1}".format(jsdata['jobParameters']['NumberOfEventsPerJob'],myRandom)
    command+=" --outputFile {0}".format(outputFile)
    fich.write("{0}\n".format(command))

    os.chmod(job_file,0o755)
    subprocess.Popen(['bash','-l','-c',"sbatch {0}".format(job_file)])
    
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
    CS.mkdir_p(job_directory)
    jsonFile="json/SinglePartSim.json"
    if len(sys.argv)==2:
        jsonFile=sys.argv[1]
    fp=open(jsonFile)
    js=json.load(fp)
    CS.mkdir_p(js['jobParameters']['output_dir'])
    jobLoop(js,len(js['jobParameters']['LoopOn'])-1,job_directory)

