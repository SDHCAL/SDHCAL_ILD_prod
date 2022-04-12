import os
import json
import CommonStep as CS
import sys
import subprocess

def reco_sub_job_submit(jsdata,job_directory,inputFiles,Nevent,skipEvent):
    base_output_name="reco_"+os.path.splitext(os.path.basename(inputFiles[0]))[0]
    if Nevent>0:
        base_output_name+="_{0}".format(Nevent)
    if skipEvent>0:
        base_output_name+="_skip{0}".format(skipEvent)
    if len(inputFiles)>1:
        base_output_name+="_nFiles{0}".format(len(inputFiles))
    job_file=os.path.join(job_directory,"{0}.sh".format(base_output_name))
    fich=open(job_file,'w')
    fich.write("#!/bin/bash\n")
    fich.write("#SBATCH --job-name=reco\n")
    fich.write("#SBATCH --ntasks=1\n")
    fich.write("#SBATCH --time=24:00:00\n")
    fich.write("#SBATCH --mail-type=ALL\n")  
    fich.write("#SBATCH --mail-user={0}\n".format(os.environ['USER_MAIL']))
    fich.write("#SBATCH --output=reco_%j.out\n")
    fich.write("#SBATCH --error=reco_%j.out\n\n")
    fich.write("source /cvmfs/ilc.desy.de/sw/{0}/init_ilcsoft.sh\n".format(jsdata['SoftwareVersions']['slurm_ilcsoftVersion']))
    fich.write("cd /scratch\n")
    fich.write("cp -R  /cvmfs/ilc.desy.de/sw/ILDConfig/{0}/StandardConfig/production/ .\n".format(jsdata['SoftwareVersions']['ILDConfigVersion']))
    fich.write("cd production\n")
    fich.write("cp {0}/steeringFiles/MarlinStdRecoSDHCALExtendedDST.xml .\n".format(os.getcwd()))
    output_dir=jsdata['JobParameters']['output_dir']
    if output_dir[0] != '/':
        output_dir=os.path.join(os.getcwd(),output_dir)
    CS.mkdir_p(output_dir)
    output_base=os.path.join(output_dir,base_output_name)
    fich.write("rm {0}_REC.slcio\n".format(output_base))
    fich.write("rm {0}_DST.slcio\n".format(output_base))
    fich.write("rm {0}_extDST.slcio\n".format(output_base))
    fich.write("rm {0}_AIDA.root\n".format(output_base))
    fich.write("rm {0}_extAIDA.root\n".format(output_base))
    fich.write("rm {0}_PfoAnalysis.root\n".format(output_base))
    command_one="Marlin MarlinStdReco.xml --constant.lcgeo_DIR=${lcgeo_DIR}"
    command_one+=" --constant.DetectorModel={0}".format(jsdata['Detector']['DetectorName'])
    command_one+=CS.extraCLIargMarlinSDHCALRecoBase(jsdata)
    command_one+=" --constant.OutputBaseName={0}".format(output_base)
    command_one+=" --constant.CMSEnergy={0}".format(jsdata['Detector']['CMSEnergy'])
    if Nevent>0:
        command_one+=" --global.MaxRecordNumber={0}".format(Nevent)
    if skipEvent>0:
        command_one+=" --global.SkipNEvents={0}".format(skipEvent)
    command_one+=' --global.LCIOInputFiles="'
    for inputfilename in inputFiles:
        command_one+="{0} ".format(inputfilename)
    command_one=command_one[:-1]+'"'
    fich.write("{0}\n\n".format(command_one))
    command_two="Marlin  MarlinStdRecoSDHCALExtendedDST.xml --constant.lcgeo_DIR=${lcgeo_DIR}"
    command_two+=" --constant.DetectorModel={0}".format(jsdata['Detector']['DetectorName'])
    command_two+=" --constant.OutputBaseName={0}".format(output_base)
    command_two+=" --global.LCIOInputFiles={0}_REC.slcio".format(output_base)
    fich.write("{0}\n\n".format(command_two))
    
    os.chmod(job_file,0o755)
    subprocess.Popen(['bash','-l','-c',"sbatch {0}".format(job_file)])
    
def reco_job_submit(jsdata,job_directory):
    jobMode=CS.decodeInputFileParameters(jsdata)
    param=jsdata['JobParameters']
    if jobMode["mode"]=="single":
        reco_sub_job_submit(jsdata,job_directory,param['InputFiles'],param['NumberOfEventsPerFile'],0)
    if jobMode["mode"]=="splitInput":
        Nfiles=jobMode["FilesPerJob"]
        fileSplit=[param['InputFiles'][i:i+Nfiles] for i in range(0, len(param['InputFiles']), Nfiles)]
        for files in fileSplit:
            reco_sub_job_submit(jsdata,job_directory,files,0,0)
    if jobMode["mode"]=="splitFiles":
        skip=range(0,jobMode["EventsPerFile"],jobMode["EventsPerJob"])
        for filename in param['InputFiles']:
            for Nskip in skip:
                reco_sub_job_submit(jsdata,job_directory,[filename],jobMode["EventsPerJob"],Nskip)

if __name__ == '__main__':
    job_directory="{0}/slurm_jobs".format(os.getcwd())
    CS.mkdir_p(job_directory)
    jsonFile="json/SDHCAL_baseReco.json"
    if len(sys.argv)==2:
        jsonFile=sys.argv[1]
    fp=open(jsonFile)
    js=json.load(fp)
    reco_job_submit(js,job_directory)
    
