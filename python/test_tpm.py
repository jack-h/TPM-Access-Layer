import re
from time import sleep

__author__ = 'lessju'

from pyfabil import TPM, Device

tpm = None

def sync_fpgas(tpm):
    devices = ["fpga1", "fpga2"]
    print "Syncing FPGAs"
    for f in devices:
        tpm['%s.pps_manager.pps_gen_tc' % f] = 0xA6E49BF  #700 MHz!

    # setting sync time
    for f in devices:
        tpm["%s.pps_manager.sync_time_write_val" % f] = 0x0

    # sync time write command
    for f in devices:
        tpm["%s.pps_manager.sync_time_cmd.wr_req" % f] = 0x1

    check_synchornisation(tpm)


def check_synchornisation(tpm):
    t0, t2 = 0, 1
    while t0 != t2:
        t0 = tpm["fpga1.pps_manager.sync_time_read_val"]
        t1 = tpm["fpga2.pps_manager.sync_time_read_val"]
        t2 = tpm["fpga1.pps_manager.sync_time_read_val"]

    fpga = "fpga1" if t0 > t1 else "fpga2"
    for i in range(abs(t1 - t0)):
        print "Decrementing %s by 1" % fpga
        tpm["%s.pps_manager.sync_time_cmd.down_req" % fpga] = 0x1

def run():
    # Connect and initliase
    global tpm
    tpm = TPM(ip = "10.0.10.2", port = 10000)

    ###### ------ Kcu Dev Board ----- ######
    #kcu = tpm.load_plugin("KcuTestFirmware", device = Device.FPGA_1)
    #kcu.start_streaming()
    ########################################

    # Load tpm test firmware for both FPGAs
    tpm.load_plugin("TpmTestFirmware", device = Device.FPGA_1)
#    tpm.load_plugin("TpmTestFirmware", device = Device.FPGA_2)

    # Check FPGA syncrhonisation
    sync_fpgas(tpm)

    # Temporary
    tpm[0x30000024] = 0x0

    # To send data
    #tpm.tpm_test_firmware.send_raw_data()


def download():
    global tpm
    tpm = TPM(ip = "10.0.10.2", port = 10000, simulator = True)
    tpm.download_firmware(Device.FPGA_1, "/home/lessju/Code/TPM-Access-Layer/bitfiles/xtpm_xcku040_tpm_top_wrap.bit")

if __name__ == "__main__":
    download()
    run()
