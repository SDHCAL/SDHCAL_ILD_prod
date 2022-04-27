import sys
import json
import CommonStep as CS
#Magic DIRAC needed voodoo
from DIRAC.Core.Base import Script
Script.parseCommandLine()
#No idea what would append with the above when this file is imported.

from ILCDIRAC.Interfaces.API.DiracILC import DiracILC
from ILCDIRAC.Interfaces.API.NewInterface.UserJob import  UserJob
from ILCDIRAC.Interfaces.API.NewInterface.Applications import DDSim




#define simulation job
def mySimJob(jsdata,Njobs=10,NeventsperJob=1000,output_dir="test"):
    job = UserJob()
    #job names
    job.setName( "MyDDsim" )
    job.setJobGroup( "GGProd" )
    #what to retrieve in the job output
    job.setOutputSandbox(['*.log', '*.sh', '*.py'])
    #CPU time for the job 
    job.setCPUTime(100 * 4 * 60)
    #exclude some site (like failing site
    job.setBannedSites(['LCG.RAL-LCG2.uk'])
    if Njobs>1 :
        job.setSplitEvents(eventsPerJob=NeventsperJob, numberOfJobs=Njobs)
    
    #Simulation job with DDsim
    ddsim = DDSim()
    #run dirac-ilc-show-software to find versions to find various software versions
    ddsim.setVersion(jsdata['SoftwareVersions']['ddsimVersion'])
    ddsim.setDetectorModel(jsdata['Detector']['DetectorName'])
    ddsim.setNumberOfEvents(NeventsperJob)
    
    #Is this setting correct for SDHCAL simulation ?
    ddsim.setSteeringFile("/cvmfs/ilc.desy.de/sw/ILDConfig/{0}/StandardConfig/production/ddsim_steer.py".format(jsdata['SoftwareVersions']['ILDConfigVersion']))
    ddsim.setEnergy(jsdata['Particle']['ParticleEnergyInGeV'])
    extraCLIarg=CS.extraCLIargument(jsdata)
    ddsim.setExtraCLIArguments(extraCLIarg)
    #output file name should not be too long (less than 128 or 256 letters)
    detector=CS.detectorName(jsdata['Detector']['DetectorName'])
    outputFileName="sim_{0}_single_{1}_{2}_GeV_{3}.slcio".format(detector,jsdata['Particle']['ParticleName'],jsdata['Particle']['ParticleEnergyInGeV'],NeventsperJob)
    ddsim.setOutputFile(outputFileName)

    #append ddsim to the job
    res = job.append(ddsim)
    print res
    if not res['OK']:
        print res['Not ok appending ddsim to job']
        sys.exit("Problem with appending ddsim to job")

    #tell the job where to put the output file on the grid
    #fisrt argument is the output file name (don't know yet how it behaves with split jobs"
    #second is the grid directory under /ilc/user/u/username/ where the output will be copied
    job.setOutputData(outputFileName,output_dir,OutputSE=['DESY-SRM','CERN-DST-EOS'])
    return job


def jobLoop(jsdata,level,dirac):
    if level==-1:
        jobPar=jsdata['jobParameters']
        job = mySimJob(jsdata,Njobs=jobPar['NumberOfJobsPerPoint'],NeventsperJob=jobPar['NumberOfEventsPerJob'],output_dir=jobPar['output_dir'])
        #submit the job 
        print job.submit(dirac)
        #print jsdata
    else:
        loopon=jsdata['jobParameters']['LoopOn'][level]
        for d in loopon['values']:
            jsdata[loopon['what']][loopon['subwhat']]=d
            jobLoop(jsdata,level-1,dirac)

if __name__ == '__main__':
    #manageParameters
    jsonFile="json/SinglePartSim.json"
    if len(sys.argv)==2:
        jsonFile=sys.argv[1]
    fp=open(jsonFile)
    js=json.load(fp)
    #create the object that will managed the job submission
    dirac = DiracILC(True,"simu.rep")
    #submit the jobs
    jobLoop(js,len(js['jobParameters']['LoopOn'])-1,dirac)

