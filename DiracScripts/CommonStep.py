import json

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
