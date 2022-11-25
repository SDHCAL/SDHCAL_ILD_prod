import sys
import os
import json
import CommonStep as CS

#Magic DIRAC needed voodoo
from DIRAC.Core.Base import Script
Script.parseCommandLine()

from ILCDIRAC.Interfaces.API.DiracILC import DiracILC
from ILCDIRAC.Interfaces.API.NewInterface.UserJob import  UserJob
from ILCDIRAC.Interfaces.API.NewInterface.Applications import Marlin

def myRecoJob(jsdata,dirac):
    """Create reco job
    :param jsdata :: json job parameters 
    :param dirac :: the ILCDirac u=interface
    """
    #definition of the job and some of its properties
    job = UserJob()
    #job names
    job.setName( "MarlinStandardReco" )
    job.setJobGroup( "Reco_base" )
    #what to retrieve in the job output
    job.setOutputSandbox(['*.log', '*.xml', '*.steer'])
    #CPU time for the job 
    job.setCPUTime(100 * 4 * 60)
    #exclude some site (like failing site)
    job.setBannedSites(['LCG.RAL-LCG2.uk'])
    
    job.setILDConfig(jsdata['SoftwareVersions']['ILDConfigVersion'])
    job.setInputSandbox(["steeringFiles/MarlinStdRecoSDHCALExtendedDST.xml"])
    fileList=jsdata['JobParameters']['InputFiles']
    base_output_name="reco_"+os.path.splitext(os.path.basename(fileList[0]))[0]
    #remove eventual file job simulation number assuming list of identical files is given
    split_cleaning=jsdata['JobParameters']['output_base_name_remove']
    base_output_name=base_output_name.rsplit(split_cleaning['split_character'],split_cleaning['split_number'])[0]
    jobMode=CS.decodeInputFileParameters(jsdata)
    if jobMode["mode"]=="splitInput":
        job.setSplitInputData(fileList,jobMode["FilesPerJob"])
    if jobMode["mode"]=="splitFiles":
        job.setSplitFilesAcrossJobs(fileList,jobMode["EventsPerFile"],jobMode["EventsPerJob"])
        base_output_name+="_reco_{0}".format(jobMode["EventsPerJob"])
    if jobMode["mode"]=="single":
        job.setInputData(fileList[0])
        if jobMode["Nevents"] != 0:
            base_output_name+="_reco_{0}".format(jobMode["Nevents"])
    
    #Marlin application
    #First standard reco with Pandora Truth
    ma = Marlin()
    ma.setVersion(jsdata['SoftwareVersions']['marlinVersion'])
    if jobMode["mode"]=="single":
        ma.setInputFile(os.path.basename(fileList[0]))
        NeventsPerFile=jobMode["Nevents"]
        if NeventsPerFile !=0:
            ma.setNumberOfEvents(NeventsPerFile)
    ma.setSteeringFile("MarlinStdReco.xml")
    ma.setLogFile("marlin.log")
    ma.setDetectorModel(jsdata['Detector']['DetectorName'])
    extraCLIarg=CS.extraCLIargMarlinSDHCALRecoBase(jsdata)
    extraCLIarg+=" --constant.OutputBaseName={0}".format(base_output_name)
    #ma.setExtraCLIArguments( extraCLIarg )

    #CMSEnergy hould correspond to the existence of Config/Parameters${CMSEnergy}GeV.xml in ILDConfig
    ma.setEnergy(jsdata['Detector']['CMSEnergy'])
    outputRECfile="{0}_REC.slcio".format(base_output_name)
    outputDSTfile="{0}_DST.slcio".format(base_output_name)
    PFOoutputFile="{0}_PfoAnalysis.root".format(base_output_name)
    #ma.setOutputRecFile(outputRECfile)
    #ma.setOutputDstFile(outputDSTfile)
    ma.setOutputFile(outputRECfile)
    extraCLIarg+=" --DSTOutput.LCIOOutputFile={0}".format(outputDSTfile)
    ma.setExtraCLIArguments( extraCLIarg ) 
    #append marlin to the job
    res = job.append(ma)
    if not res['OK']:
        print res['Not ok appending Marlin to job']
        quit()

    #Second Marlin run to produce extended DST file
    # NB : specific marlin steering file to be send in the job input sandbox
    mabis = Marlin()
    mabis.setVersion(jsdata['SoftwareVersions']['marlinVersion'])
    mabis.getInputFromApp( ma )
    mabis.setSteeringFile("MarlinStdRecoSDHCALExtendedDST.xml")
    mabis.setLogFile("marlin_bis.log")
    mabis.setDetectorModel(jsdata['Detector']['DetectorName'])
    extraCLIarg=""
    extraCLIarg+=" --constant.OutputBaseName={0}".format(base_output_name)
    mabis.setExtraCLIArguments( extraCLIarg )
    mabis.setEnergy(jsdata['Detector']['CMSEnergy'])
    outputextDSTfile="{0}_extDST.slcio".format(base_output_name)
    mabis.setOutputRecFile(outputextDSTfile)
    mabis.setOutputFile(outputextDSTfile)
    #append marlin to the job
    res = job.append(mabis)
    if not res['OK']:
        print res['Not ok appending Marlin to job']
        quit()

    #tell the job where to put the output file on the grid
    #first argument is the list of input file
    #second is the grid directory under /ilc/user/u/username/ where the output will be copied
    job.setOutputData([outputRECfile,outputextDSTfile,PFOoutputFile],jsdata['JobParameters']['output_dir'],OutputSE=['DESY-SRM','CERN-DST-EOS','IN2P3-SRM'])

    #submit the job 
    print job.submit(dirac)
    
if __name__ == '__main__':
    #manageParameters
    jsonFile="json/SDHCAL_baseReco.json"
    if len(sys.argv)==2:
        jsonFile=sys.argv[1]
    fp=open(jsonFile)
    js=json.load(fp)
    #create the object that will managed the job submission
    dirac = DiracILC(True,"reco.rep")
    #submit the jobs
    myRecoJob(js,dirac)
    
