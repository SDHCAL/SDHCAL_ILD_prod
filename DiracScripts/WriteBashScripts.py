import json
import os
import CommonStep as CS
import random
    
def create_bash_script_file(filename):
    fich=open(filename,'w')
    fich.write("#!/bin/bash\n")
    os.chmod(filename,0o755)
    return fich

def write_slurm_bash_script_header(fich,jobname):
    fich.write("#SBATCH --job-name={0}\n".format(jobname))
    fich.write("#SBATCH --ntasks=1\n")
    fich.write("#SBATCH --time=24:00:00\n")
    fich.write("#SBATCH --mail-type=ALL\n")  
    fich.write("#SBATCH --mail-user={0}\n".format(os.environ['USER_MAIL']))
    fich.write("#SBATCH --output={0}_%j.out\n".format(jobname))
    fich.write("#SBATCH --error={0}_%j.out\n\n".format(jobname))

def write_bash_script_ilcsoft_init(fich,jsdata):
    fich.write("source {1}/{0}/init_ilcsoft.sh\n".format(jsdata['SoftwareVersions']['slurm_ilcsoftVersion'],jsdata['SoftwareVersions'].get('ilcsoftBaseDir','/cvmfs/ilc.desy.de/sw')))

def get_output_dir(jsdata):
    output_dir=jsdata['JobParameters']['output_dir']
    if output_dir[0] != '/':
        output_dir=os.path.join(os.getcwd(),output_dir)
    return output_dir

def create_ddsim_bash_script(jsdata,job_directory,job_number,with_slurm_header):
    million=1000000
    myRandom=random.randint(million,100*million)
    fileBase="ddsim"
    loopOn=jsdata['JobParameters']['LoopOn']
    for d in loopOn:
        value=jsdata[d['what']][d['subwhat']]
        if d['subwhat']=='DetectorName':
            value=CS.detectorName(value)
        fileBase+="_{0}_{1}".format(d['subwhat'],value)
    fileBase+="_{0}".format(job_number)
    job_file=os.path.join(job_directory,"{0}.sh".format(fileBase))

    fich=create_bash_script_file(job_file)
    if with_slurm_header:
       write_slurm_bash_script_header(fich,"ddsim")
    write_bash_script_ilcsoft_init(fich,jsdata)
    lcgeo_detector=jsdata['Detector']['DetectorName']
    output_dir=get_output_dir(jsdata)
    outputFile=os.path.join(output_dir,"{0}.slcio".format(fileBase))
    fich.write("rm {0}\n".format(outputFile))
    command="ddsim --compactFile $lcgeo_DIR/ILD/compact/{0}/{0}.xml ".format(lcgeo_detector)
    command+=CS.extraCLIargument(jsdata)
    command+=" --steeringFile {1}/ILDConfig/{0}/StandardConfig/production/ddsim_steer.py".format(jsdata['SoftwareVersions']['ILDConfigVersion'],jsdata['SoftwareVersions'].get('ilcsoftBaseDir','/cvmfs/ilc.desy.de/sw'))
    command+=" --numberOfEvents {0} --random.seed {1}".format(jsdata['JobParameters']['NumberOfEventsPerJob'],myRandom)
    command+=" --outputFile {0}".format(outputFile)
    fich.write("{0}\n".format(command))
    return job_file

def create_marlin_bash_script(jsdata,job_directory,inputFiles,Nevent,skipEvent,with_slurm_header):
    base_output_name="reco_"+os.path.splitext(os.path.basename(inputFiles[0]))[0]
    if Nevent>0:
        base_output_name+="_{0}".format(Nevent)
    if skipEvent>0:
        base_output_name+="_skip{0}".format(skipEvent)
    if len(inputFiles)>1:
        base_output_name+="_nFiles{0}".format(len(inputFiles))
    job_file=os.path.join(job_directory,"{0}.sh".format(base_output_name))
    fich=create_bash_script_file(job_file)
    if with_slurm_header:
       write_slurm_bash_script_header(fich,"reco")
    write_bash_script_ilcsoft_init(fich,jsdata)
    
    fich.write("cd /scratch\n")
    fich.write("cp -R {1}/ILDConfig/{0}/StandardConfig/production/ .\n".format(jsdata['SoftwareVersions']['ILDConfigVersion'],jsdata['SoftwareVersions'].get('ilcsoftBaseDir','/cvmfs/ilc.desy.de/sw')))
    fich.write("cd production\n")
    fich.write("cp {0}/steeringFiles/MarlinStdRecoSDHCALExtendedDST.xml .\n".format(os.getcwd()))
    output_dir=get_output_dir(jsdata)
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


