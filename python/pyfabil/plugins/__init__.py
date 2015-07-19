__author__ = 'Alessio Magro'

# Helper to reduces import names

# Plugin Superclass
from pyfabil.plugins.firmwareblock import FirmwareBlock

# Test plugins
from pyfabil.plugins.firmwaretest2 import FirmwareTest2
from pyfabil.plugins.firmwaretest  import FirmwareTest


# UniBoard plugins
from pyfabil.plugins.uniboard.wideband_wave_generator import UniBoardWBWaveGenerator
from pyfabil.plugins.uniboard.sensor_information      import UniBoardSensorInformation
from pyfabil.plugins.uniboard.system_information      import UniBoardSystemInformation
from pyfabil.plugins.uniboard.adu_i2c_commander       import UniBoardAduI2CCommander
from pyfabil.plugins.uniboard.beamforming_unit        import UniBoardBeamformingUnit
from pyfabil.plugins.uniboard.beamlet_statistics      import UniBoardBeamletStatistics
from pyfabil.plugins.uniboard.subband_statistics      import UniBoardSubbandStatistics
from pyfabil.plugins.uniboard.ppf_filterbank          import UniBoardPpfFilterbank
from pyfabil.plugins.uniboard.bsn_scheduler           import UniBoardBsnScheduler
from pyfabil.plugins.uniboard.tr_nonbonded            import UniBoardNonBondedTr
from pyfabil.plugins.uniboard.ss_parallel             import UniBoardSSParallel
from pyfabil.plugins.uniboard.beamformer              import UniBoardBeamformer
from pyfabil.plugins.uniboard.bsn_source              import UniBoardBsnSource
from pyfabil.plugins.uniboard.ss_reorder              import UniBoardSSReorder
from pyfabil.plugins.uniboard.aduh_quad               import UniBoardAduhQuad
from pyfabil.plugins.uniboard.ss_wide                 import UniBoardSSWide





