# SDHCAL_ILD_prod
Tools to simulate and reconstruct SDHCAL ILD events. 

The tools consist of python scripts that can either be used to submit jobs to ILCDirac or to create shell scripts that are then submitted to a slurm batch system.
In both cases, the job parameters are provided in a json file. 

## ILCDirac specifics
For using the ILCDirac grid, you need to initialise with the following code :
```
source /cvmfs/clicdp.cern.ch/DIRAC/bashrc
dirac-proxy-init -g ilc_user
```
## Slurm batch specifics
The slurm batch machine you are using should have an access to the `/cvmfs/ilc.desy.de/` directory.
The slurm batch system uses a mail to communicate with you. Before running the script for slurm, you need to provide your e-mail in an environment variable named `USER_MAIL`.

## running the scripts
To run the script, you should be located in the directory where this README file is located and enter : `python DiracScripts/<script>.py` where script should be replaced by the name of the python script.
For all scripts, you can change the json file used for launching the jobs by adding its name on the command line : `python DiracScripts/<script>.py <jsonFile>` 

# Single particle simulation 
The scripts to produce single particle ILD simulation are 
* `SDHCAL_dirac_ddsim_singlepart.py` to run simulation jobs on the ILCDirac grid
* `SDHCAL_slurm_ddsim_singlepart.py` to run simulation jobs on slurm batch machines

The script parameters are controlled by a json file. The default json file for single particle production can be found in `json/SinglePartSim.json`
The parameters in the json file are the following :
* Particle
  * ParticleName : the name of the particle in ddsim/GEANT4 format
  * ParticleEnergyInGeV : the particle energy in GeV
  * ParticleDistribution : the angular distribution of the particle. See the ddsim/Geant4 particle gun documentation for possible values.
* Detector
  * DetectorName : The name of the detector. It should correspond to one of the detector listed in the lcgeo package under `lcgeo/ILD/compact`. The current list of detector can be found at https://github.com/iLCSoft/lcgeo/tree/master/ILD/compact
  * physicsList : The GEANT4 physics list to use, see GEANT4 documentation for valid names.
* SoftwareVersions
  * ddsimVersion : the ddsim version to use when using ILCDirac. To know which versions are available, run `dirac-ilc-show-software`
  * slurm\_ilcsoftVersion : the ilcsoft version to use when using slurm. The ilcsoft directory is defined as `/cvmfs/ilc.desy.de/sw/<slurm_ilcsoftVersion>/`
  * ILDConfigVersion : the ILDConfig version to use.
    * For ILCDirac, run `dirac-ilc-show-software` to know which version are available
    * For slurm, the ILDConfig version will be in `/cvmfs/ilc.desy.de/sw/ILDConfig/<ILDConfigVersion>/`
* jobParameters
  * NumberOfEventsPerJob : the number of events per job.
  * NumberOfJobsPerPoint : the number of job to run per set of parameters. Forr a given set of parameters, this corresponds to the number of produced files. Each file will contain NumberOfEventsPerJob events.
  * output\_dir : the name of the output directory. output\_dir can be either a single name (`dir`) or a path (`dir/subdir/subsubdir/...`).
    * For ILCDirac, the directory is on the Dirac grid catalog under `/ilc/user/u/username/<output_dir>`. 
    * For slurm, the directory is created on your local account where slurm runs.
  * LoopOn : A list of variables to loop on. Variables should be in the json file. LoopOn should contain a list of loop instructions. Each loop instruction is made of the following :
    * what : top level json value (Particle, Detector or SoftwareVersions)
    * subwhat : second level of json value. Should be compatible with value given in "what". For example if "what" is set to "Particle" then "subwhat" can be set to ParticleName, ParticleEnergyInGeV or ParticleDistribution.
    * values : the list of values to loop on. Each value here corresponds to a set of parameters for what concerned NumberOfJobsPerPoint.

# Standard reconstruction
The scripts to run standard ILD reconstruction from a simulation output are :
* `SDHCAL_dirac_marlin_baseReco.py` to run reconstruction jobs on the ILCDirac grid
* `SDHCAL_slurm_marlin_baseReco.py` to run reconstruction jobs on slurm batch machines

The script parameters are controlled by a json file. The default json file for single particle production can be found in `json/SDHCAL_baseReco.json`
The parameters in the json file are the following :
* Detector
  * DetectorName : The name of the detector. It should correspond to the detector name used to run ddsim.
  * CalibDetectorName : The name should be either "automatic" or a name which is described in the ILDConfig package under `ILDConfig/StandardConfig/production/Calibration/Calibration_<CalibDetectorName>.xml`. If set to automatic, for Videau geometry, it translates automatically the Videau Detector name into the corresponding hybrid Tesla simulation name.
  * CMSEnergy : This parameter should correspond to a file in ILDConfig under `ILDConfig/StandardConfig/production/Config/Parameters<CMSEnergy>GeV.xml`. 
* SoftwareVersions 
  * marlinVersion : the Marlin version to use when using ILCDirac. To know which versions are available, run `dirac-ilc-show-software`
  * ILDConfigVersion : the ILDConfig version to use. See the same parameter in [previous section](https://github.com/SDHCAL/SDHCAL_ILD_prod#single-particle-simulation) to details how the parameter is handled.
  * slurm\_ilcsoftVersion : the ilcsoft version to use when using slurm. The ilcsoft directory is defined as `/cvmfs/ilc.desy.de/sw/<slurm_ilcsoftVersion>/`
* SDHCAL_Calibration : The values in the example files comes from Bo Li's studies with hybrid detector and linear energy reconstruction
  * SDHCALEnergyFactors : A list of 3 real parameters to assign an individual hit energy value for each of the 3 SDHCAL thresholds. Meaningful only when using linear SDHCAL energy reconstruction.
  * PandoraEcalToHadronicEnergyConversionBarrel : A PandoraPFA energy rescaling factor for Hadronic energy in the ECAL Barrel.
  * PandoraEcalToHadronicEnergyConversionEndcap : A PandoraPFA energy rescaling factor for Hadronic energy in the ECAL Endcaps.
  * PandoraHcalToHadronicEnergyConversion : A PandoraPFA energy rescaling factor for Hadronic energy in the HCAL.
* JobParameters
  * InputFilesToJobsRatio : this parameter should be a string in the form "i-j" with i and j integer numbers. At least i or j should be equal to 1. The possible values are then :
    * `1-1` with one input file : NumberOfEventsPerFile events will be processed by a sigle job in the input file. If NumberOfEventsPerFile is set to zero, the entire input file is processed.
    * `n-1` with more than one input files : n can be equal to 1. The input file lists will be split in group of n files. Each file group will be entirely processed by one job.
    * `1-n` with n greater than 1 : each input file will be processed by n jobs. The number of events in each file should be specified by the parameter NumberOfEventsPerFile
  * NumberOfEventsPerFile : either the number of event to process when only one input file and one job or the number of events in a single file when InputFilesToJobsRatio is set to `1-n` mode with n greater than 1.
  * output\_dir : see [previous section](https://github.com/SDHCAL/SDHCAL_ILD_prod#single-particle-simulation) to see how this parameter is treated
  * output\_base\_name\_remove : the name of the first input file without its extension is used as the basename for the output files. We can remove some portion of the end of the file basename. The parameters describe how the removal is done :
    * split\_character : the character used to separate fields in the file basename
    * split\_number : the number of fields to remove at the end of the file basename
  * InputFiles : The list of inputfiles files with absolute name (name starting by `/`). For ILCDirac, the files are in the Dirac File catalog. For slurm, the files are in a local directory.
 
# issues and to do list
* Standard reconstruction doesn't work on single particle simulation due to Marlin crashing.
* Missing ability to run simulation on a set of input stdhep files.
* Missing ability to use your own ILDConfig instead of standard one.


