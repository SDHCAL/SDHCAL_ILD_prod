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
