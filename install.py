#!/usr/bin/python
import os,sys,commands,urllib2,platform
from commands import *
os.system("clear")
print "Raspbmc installer for Linux and Mac OS X"
print "http://raspbmc.com"
print "----------------------------------------"

# check if root with whoami, getuid doesn't return 0 if sudoing
currentUser = commands.getoutput("whoami")
if currentUser != 'root':
  print "Please re-run this script with root privileges, i.e. 'sudo ./install.py'\n"
  sys.exit()

# check if running on Mac
mac = (platform.system() == 'Darwin')


# yes/no prompt adapted from http://code.activestate.com/recipes/577058-query-yesno/
def query_yes_no(question, default="yes"):
  valid = {"yes":"yes", "y":"yes",  "ye":"yes",
       "no":"no",   "n":"no"}
  if default == None:
    prompt = " [y/n] "
  elif default == "yes":
    prompt = " [Y/n] "
  elif default == "no":
    prompt = " [y/N] "
  else:
    raise ValueError("invalid default answer: '%s'" % default)

  while 1:
    sys.stdout.write(question + prompt)
    choice = raw_input().lower()
    if default is not None and choice == '':
      return default
    elif choice in valid.keys():
      return valid[choice]
    else:
      sys.stdout.write("Please respond with 'yes' or 'no' "\
               "(or 'y' or 'n').\n")


def unmount(drive): # unmounts drive
  print 'Unmounting the drive in preparation for writing...'
  output = getoutput('diskutil unmountDisk ' + drive)
  print output
  if 'Unmount failed for' in output:
    print 'Error: the drive couldn\'t be unmounted, exiting...'
    exit()


def eject(drive): # ejects drive
  print 'Finalising SD card, please wait...'
  if mac:
    output = getoutput('diskutil eject ' + drive)
  else:
    output = getoutput('sync')
  print output


def listdevices():
  if mac:
    output = getoutput('diskutil list | grep -e "[#1-9]:"')
  else:
    output = getoutput('fdisk -l | grep -E "Disk /dev/"')
  print output


def chunk_report(bytes_so_far, chunk_size, total_size):
  percent = float(bytes_so_far) / total_size
  percent = round(percent*100, 2)
  sys.stdout.write("Downloaded %0.2f of %0.2f MiB (%0.2f%%)\r" %
    (float(bytes_so_far)/1048576, float(total_size)/1048576, percent))
  if bytes_so_far >= total_size:
    sys.stdout.write('\n')


def chunk_read(response, file, chunk_size, report_hook):
  total_size = response.info().getheader('Content-Length').strip()
  total_size = int(total_size)
  bytes_so_far = 0
  while 1:
    chunk = response.read(chunk_size)
    file.write(chunk)
    bytes_so_far += len(chunk)
    if not chunk:
      break
    if report_hook:
      report_hook(bytes_so_far, chunk_size, total_size)
  return bytes_so_far


def download(url):
  print "Downloading, please be patient..."
  dl = urllib2.urlopen(url)
  dlFile = open('installer.img.gz', 'w')
  chunk_read(dl, dlFile, 8192, chunk_report)
  #dlFile.write(dl.read())
  dlFile.close()


def deviceinput():
  # they must know the risks!
  verified = "no"
  raw_input("Please ensure you've inserted your SD card, and press Enter to continue.")
  while verified is not "yes":
    print("")
    if mac:
      print("Enter the 'IDENTIFIER' of the device you would like imaged, from the following list:")
    else:
      print("Enter the 'Disk' you would like imaged, from the following list:")
    listdevices()
    print("")
    if mac:
      device = raw_input("Enter your choice here (e.g. 'disk1s1'): ")
    else:
      device = raw_input("Enter your choice here (e.g. 'mmcblk0' or 'sdd'): ")

    # Add /dev/ to device if not entered
    if not device.startswith("/dev/"):
      device = "/dev/" + device;

    print("It is your own responsibility to ensure there is no data loss! Please backup your system before imaging")
    cont = query_yes_no("Are you sure you want to install Raspbmc to '" + device + "'?", "no")

    if cont == "no":
      exit()
    else:
      verified = "yes"

    if os.path.exists(device) == False:
      print "Device doesn't exist"
      # and thus we are not 'verified'
      verified = "no"

  return device


def imagedevice(dev, imagefile):
  print("")
  if mac:
    unmount(dev)
    import re
    regex = re.compile('/dev/r?(disk[0-9]+?)')
    try:
      disk = re.sub('r?disk', 'rdisk', regex.search(dev).group(0))
    except:
      print "Malformed disk specification -> ", disk
      exit()
  else:
    disk = dev

  # use the system's built in imaging and extraction facilities
  print "Please wait while Raspbmc is installed to your SD card..."
  print "(This may take some time and no progress will be reported until it has finished.)"
  if mac:
    os.system("gunzip -c " + imagefile + " | dd of=" + disk + " bs=1m")
  else:
    os.system("gunzip -c " + imagefile + " | dd of=" + disk + " bs=1M")
  print "Installation complete."
  eject(disk)


def raspbmcinstaller():
  # configure the device to image
  blkdevice = deviceinput()
  # should downloading and extraction be done?
  if os.path.exists("installer.img.gz"):
    redl = query_yes_no("It appears that the Raspbmc installation image has already been downloaded. Would you like to re-download it?", "no")
    if redl == "no":
      # go straight to imaging
      imagedevice(blkdevice, "installer.img.gz")
      print""
      print "Raspbmc is now ready to finish setup on your Pi, please insert the"
      print "SD card with an active internet connection"
      print""
      sys.exit()
  # otherwise, call the dl
  download("http://download.raspbmc.com/downloads/bin/ramdistribution/installer.img.gz")
  # now we can image
  imagedevice(blkdevice, "installer.img.gz")
  print""
  print "Raspbmc is now ready to finish setup on your Pi, please insert the"
  print "SD card with an active internet connection"
  print""


raspbmcinstaller()
