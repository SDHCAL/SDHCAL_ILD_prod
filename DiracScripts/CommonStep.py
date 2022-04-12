import json

def raiseDecodeError(badkey):
    message='["JobParameters"]["InputFilesToJobsRatio"] is {0}. Authorized values are 1-to-n and n-to-1 with n an integer.'.format(badkey)
    raise KeyError(message)

def decodeInputFileParameters(jsdata):
    param=jsdata['JobParameters']
    NumberOfInputFiles=len(param['InputFiles'])
    NumberOfEventsPerFile=param['NumberOfEventsPerFile']
    InputfilesToJobs=param['InputFilesToJobsRatio']
    a=InputfilesToJobs.split('-',3)
    if len(a) != 3:
        raiseDecodeError(InputfilesToJobs)
    NumberOfFilesPerJob=int(a[0])
    NumberOfJobsPerFile=int(a[2])
    if NumberOfFilesPerJob !=1 and NumberOfJobsPerFile != 1:
        raiseDecodeError(InputfilesToJobs)
    if NumberOfJobsPerFile==1 and NumberOfInputFiles==1:
        return {"mode":"single","Nevents":NumberOfEventsPerFile}
    if NumberOfJobsPerFile==1 and NumberOfInputFiles>1:
        return {"mode":"splitInput","FilesPerJob":NumberOfFilesPerJob}
    if NumberOfJobsPerFile>1 and NumberOfEventsPerFile>0:
        return {"mode":"splitFiles","EventsPerFile":NumberOfEventsPerFile,"EventsPerJob":NumberOfEventsPerFile/NumberOfJobsPerFile}
    raise ValueError("Logical error in your JobParameters setting")
    

def extraCLIargument(jsdata):
    extraCLIarg="--action.calo Geant4SimpleCalorimeterAction --enableDetailedShowerMode --physics.list {0} ".format(jsdata['Detector']['physicsList'])
    extraCLIarg+="--enableGun --gun.particle {1} --gun.energy {0}*GeV ".format(jsdata['Particle']['ParticleEnergyInGeV'],jsdata['Particle']['ParticleName'])
    extraCLIarg+='--gun.distribution "{0}" '.format(jsdata['Particle']['ParticleDistribution'])
    return extraCLIarg

def detectorName(detector):
    if detector=="ILD_l5_v02":
        detector="LargeHybridTESLA"
    if detector=="ILD_l2_v02":
        detector="LargeVideau"
    if detector=="ILD_s5_v02":
        detector="SmallHybridTESLA"
    if detector=="ILD_s2_v02":
        detector="SmallVideau"
    return detector

def CalibDetectorName(detectorName):
    calib=detectorName
    if detectorName=="ILD_l2_v02":
        calib="ILD_l5_o2_v02"
    if  detectorName=="ILD_s2_v02":
        calib="ILD_s5_o2_v02"
    return calib

def extraCLIargMarlinSDHCALRecoBase(jsdata):
    extraCLIarg=""
    #Fix to missing file in current ILDConfig when running Videau geometry
    calibFile=jsdata['Detector']['CalibDetectorName']
    if calibFile=="automatic":
        calibFile=CalibDetectorName(jsdata['Detector']['DetectorName'])
    extraCLIarg+=" --constant.CalibrationFile=Calibration/Calibration_{0}.xml".format(calibFile)
    calib=jsdata['SDHCAL_Calibration']
    extraCLIarg+=' --constant.SDHcalEnergyFactors="{0}"  --constant.PandoraEcalToHadBarrelScale="{1}" --constant.PandoraEcalToHadEndcapScale="{2}" --constant.PandoraHcalToHadScale="{3}"'.format(calib['SDHCALEnergyFactors'],calib['PandoraEcalToHadronicEnergyConversionBarrel'],calib['PandoraEcalToHadronicEnergyConversionEndcap'],calib['PandoraHcalToHadronicEnergyConversion'])
    extraCLIarg+=' --constant.PandoraSettingsFile=PandoraSettings/PandoraSettingsPerfectPFA.xml'
    #turn on calibration details in PfoAnalysis (requires full SimCalorimeterHitInfo)
    extraCLIarg+=' --MyPfoAnalysis.CollectCalibrationDetails=1'
    return extraCLIarg
