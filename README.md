# EarthwormServerClient
Communication between LinkIt IoT platform and a Windows server using Python

## Requirements
1. A Windows server with [Earthworm](http://www.earthwormcentral.org/) installed
2. A [LinkIt Smart 7688 SoC](https://labs.mediatek.com/en/platform/linkit-smart-7688#HDK) with connection to the internet
3. Python 3.6 on both server and client
4. A chip capable of detecting vibrations in 3 dimensions and creating [.sac](https://ds.iris.edu/files/sac-manual/manual/file_format.html) files, sending them to a specific directory on the LinkIt

## Motivation
We want to expand the coverage, detail, and data set of earthquake data while reducing cost and size of the measuring material as to get the equipment into the hands of as many people as possible. New MEMS technology combined with emerging IoX trends allow for a small, cheap, wireless to complement data collection, which used to be limited to professional equipment. This way, more schools, offices, and homes can install their own earthquake data collection devices.

Data transfer and algorithms are provided by Earthworm, an API created by USGS and used by the CWB in Taiwan. However, we could not install it on LinkIt, leading to complications in data transfer (which could've been done with `import` and `export` modules).

This repo includes multiple methods of communicating between LinkIt and a Windows server using Python, supported by both devices. The Windows server's data will be fed into Earthworm, which is presumably already running on the server.

# Plan 1
## Overview
Takes .sac files on Linkit and sends them to the server in TCP communications that look like this:
 * Client connects to server
 * Server: Request (.sac) file name
 * Client: Sends file name
 * Server: Request file size
 * Client: Sends file size
 * Server: Request file
 * Client: Sends chunks of file, each of size `MAX_DATA_SIZE`
 * Server: For each chunk it receives, checks if it received >= the number of bytes specified as the file size
 * Server: Request end communication (once it detects it received all the bytes in file size)
 * Client breaks communication with server
 * Client finds next .sac file, back to step 1
 
Each .sac file the server receives is saved in `SAC_DIR` and converted and appended to a `Tracebuf` file using the `sac2tb` Earthworm module. For every `NUM_TBUF_COMPRESS` files, the server uses the `remux_tbuf` module to create a .tnk (tank) file in `TANK_DIR`. The tank file is numbered incrementally starting from `1.tnk`.

### Pros
 * Only Python and .exe files are used. No compiling necessary.
 * TCP breaking communications with each .sac file received should allow a large number of connections without multithreading (as long as the server processes each connection quickly). Otherwise, each client would have its own reserved thread, and the number of possible clients would be limited.
 * Client software is only in charge of communication, not translating between file types.

### Cons
 * Slowed down by number of steps.  
Sensor -> .sac -> Python client (TCP) -> Python server (TCP) -> Tracebuf -> .tnk -> tankplayer -> RING
 * No multithreading on server.
 * Intermediary files are kept on server (although modifying code to delete them is easy).

### Usage
#### Server
1. On the server, copy the files: `server.py`, `const.py`, `sac2tb.exe`, and `remux_tbuf.exe`. Make sure they're in the same directory.
2. In the terminal, run `ew_nt.cmd`, which should be in `earthworm/run/params`, wherever Earthworm is set up. This is so that `remux_tbuf.exe` can run properly.
3. Modify `MAX_CONNECTIONS` and `NUM_TBUF_COMPRESS` in `server.py` accordingly.
4. Connect to the internet. In the terminal where `ew_nt.cmd` was run, run `server.py`. The server is now ready to listen to incoming connections.
5. Have a `tankplayer` module that attempts to find new tank files in `TANK_DIR`, which is specified in `server.py`. This is done by modifying `tankplayer.d` so that `GetFromDir` is uncommented and points to where the new tank files will be created. This module should also feed its data into an Earthworm RING, after which Earthworm will do its processing.

#### Client
1. On the LinkIt, copy the files: `client.py` and `const.py`. Make sure they're in the same directory. **In** the directory, create a folder whose name is equal to the value of `SAC_FILE_DIR` in `client.py`. That folder is where the .sac files should be stored. `client.py` will attempt to find `saclist` within that directory. `saclist` contains the file names of all the .sac files.
2. Modify `HOST` in `client.py` such that it points to the server's IP.
3. Note that `client.py` will quit after sending all the .sac files specified in `saclist`. To make it run continuously, modify it so it can find the newly generated folders. Or, modify it so it isn't dependent on `saclist` but can still find newly generated `.sac` files in order.
4. Connect to the internet, and type `client.py` into the terminal.

##### Notes
Created by David Chu 朱崇亞 as part of the NTU IoX summer program.
