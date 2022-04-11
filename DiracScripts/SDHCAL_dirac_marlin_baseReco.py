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

def myRecoJob(jsdata,dirac,inputFileNames,NeventsPerFile=0,NeventsPerJob=0):
    """Create reco job
    :param jsdata :: json job parameters 
    :param inputFileNames :: list of string with full filenames in Dirac File Catalog or single string with the filename
    :param int NeventsPerFile :: number of events in the file to process (0 means all)
    :param int NeventsPerJob :: number of events to process in one job, one input file is splitted across many jobs. If set to something else than 0, NeventsPerFile should be set to non zero value.
    When using NeventsPerFile, user should check the total number of events in his files to make sure  all events will be processed
    """
    fileList=inputFileNames  if isinstance(inputFileNames, list) else [inputFileNames]
    if NeventsPerJob>0 and NeventsPerFile==0:
        raise ValueError("Parameter NeventsPerFile should not be zero when NeventsPerJob is set to a non zero value.")

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
    singleJob=False
    if NeventsPerJob>0:
        job.setSplitFilesAcrossJobs(fileList, NeventsPerFile, NeventsPerJob)
    else:
        if len(fileList) > 1:
            job.setSplitInputData(fileList)
        else:
            singleJob=True
    base_output_name="reco_"+os.path.splitext(os.path.basename(fileList[0]))[0]
    #remove eventual file job simulation number assuming list of identical files is given
    split_cleaning=jsdata['JobParameters']['output_base_name_remove']
    base_output_name=base_output_name.rsplit(split_cleaning['split_character'],split_cleaning['split_number'])[0]
    if not singleJob:
        if NeventsPerFile>0:
            base_output_name+="_reco_{0}".format(NeventsPerFile)
    if NeventsPerJob>0:
        base_output_name+="_reco_{0}".format(NeventsPerJob)
    
    #Marlin application
    #First standard reco with Pandora Truth
    ma = Marlin()
    ma.setVersion(jsdata['SoftwareVersions']['marlinVersion'])
    if singleJob:
        ma.setInputFile(fileList[0])
        if NeventsPerFile !=0:
            ma.setNumberOfEvents(NeventsPerFile)
    ma.setSteeringFile("MarlinStdReco.xml")
    ma.setLogFile("marlin.log")
    ma.setDetectorModel(jsdata['Detector']['DetectorName'])
    extraCLIarg=CS.extraCLIargMarlinSDHCALRecoBase(jsdata)
    extraCLIarg+=" --constant.OutputBaseName={0}".format(base_output_name)
    ma.setExtraCLIArguments( extraCLIarg )

    #CMSEnergy hould correspond to the existence of Config/Parameters${CMSEnergy}GeV.xml in ILDConfig
    ma.setEnergy(jsdata['Detector']['CMSEnergy'])
    outputRECfile="{0}_REC.slcio".format(base_output_name)
    outputDSTfile="{0}_DST.slcio".format(base_output_name)
    PFOoutputFile="{0}_PfoAnalysis.root".format(base_output_name)
    ma.setOutputRecFile(outputRECfile)
    ma.setOutputDstFile(outputDSTfile)
    ma.setOutputFile(outputRECfile)
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
    JobParams=js['JobParameters']
    NeventsPerFile=JobParams['NumberOfEventsToProcessInFilePerJob']
    NeventsPerJob=JobParams['NumberOfJobsPerFileIfSPlitFile']
    if NeventsPerJob!=0:
        NeventsPerJob=NeventsPerFile/NeventsPerJob
    myRecoJob(js,dirac,JobParams['InputFiles'],NeventsPerFile,NeventsPerJob)
    
