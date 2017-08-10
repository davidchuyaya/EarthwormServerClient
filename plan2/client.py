from EarthwormServerClient.plan2 import FileIO
import os

SAC_DIR = "clientSAC"
TRACEBUF_DIR = "clientTracebuf"

# Make directories if necessary
os.makedirs(TRACEBUF_DIR, exist_ok=True)

# Test. Converts all .sac in clientSAC that are from KMNB into tracebufs.
for filename in os.listdir(SAC_DIR):
    if filename.startswith("KMNB"):
        sac_path = "{0}/{1}".format(SAC_DIR, filename)
        tracebuf_path = "{0}/{1}".format(TRACEBUF_DIR, filename)
        FileIO.convert_sac_to_tracebuf(sac_path, tracebuf_path)
