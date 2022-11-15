import os
import json
import CommonStep as CS
import WriteBashScripts as wbash
import sys
import subprocess

def reco_sub_job_submit(jsdata,job_directory,inputFiles,Nevent,skipEvent,real_submit):
    job_file=wbash.create_marlin_bash_script(jsdata,job_directory,inputFiles,Nevent,skipEvent,True)
    if real_submit:
        subprocess.Popen(['bash','-l','-c',"sbatch {0}".format(job_file)])
    
def reco_job_submit(jsdata,job_directory,real_submit):
    jobMode=CS.decodeInputFileParameters(jsdata)
    param=jsdata['JobParameters']
    if jobMode["mode"]=="single":
        reco_sub_job_submit(jsdata,job_directory,param['InputFiles'],param['NumberOfEventsPerFile'],0,real_submit)
    if jobMode["mode"]=="splitInput":
        Nfiles=jobMode["FilesPerJob"]
        fileSplit=[param['InputFiles'][i:i+Nfiles] for i in range(0, len(param['InputFiles']), Nfiles)]
        for files in fileSplit:
            reco_sub_job_submit(jsdata,job_directory,files,0,0,real_submit)
    if jobMode["mode"]=="splitFiles":
        skip=range(0,jobMode["EventsPerFile"],jobMode["EventsPerJob"])
        for filename in param['InputFiles']:
            for Nskip in skip:
                reco_sub_job_submit(jsdata,job_directory,[filename],jobMode["EventsPerJob"],Nskip,real_submit)

if __name__ == '__main__':
    job_directory="{0}/slurm_jobs".format(os.getcwd())
    CS.mkdir_p(job_directory)
    jsonFile="json/SDHCAL_baseReco.json"
    if len(sys.argv)>=2:
        jsonFile=sys.argv[1]
    real_submit=True
    if len(sys.argv)==3:
        real_submit=False
    fp=open(jsonFile)
    js=json.load(fp)
    CS.mkdir_p(wbash.get_output_dir(js))
    reco_job_submit(js,job_directory,real_submit)
    
