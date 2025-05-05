#!/usr/bin/env bash
# This script does all the necessary steps for running the code on the Pi Pico
# In order, these are the steps it performs:
# * Mounts the Pico if it isn't already
# * Runs the project build script
# * Copies the .uf2 file to the Pico
# * Opens the serial port with a screen command

# Make sure to change the below constants for your system!
I_HAVE_CONFIRMED_THESE_ARE_CORRECT=no # Change to 'yes' once you're happy.
PICO_MNTDIR=/run/media/`whoami`/RPI-RP2 # Where the device should be mounted.
PICO_BLKDEV=/dev/sdd1 # Block device used for automatic mounting, if it isn't already
SERIAL_PORT=/dev/ttyACM0 # Serial port for the screen command

# Automount abort routine
cleanup() {
  echo "Cleaning up mountpoint"
  # Attempt to unmount device
  failed=0 # Zero means all ok, 1 means umount failed, 2 means rmdir failed
  if grep -qs "$PICO_BLKDEV " /proc/mounts; then
    # Try three times to unmount the device
    for try in {1..3}; do
      sudo umount "$PICO_BLKDEV" 
      if [ $? -eq 0 ]; then
        # Show how many tries it took, if more than 1 was needed.
        [ $try -gt 1 ] && echo Unmounted OK after $try tries
        break # We can stop trying now it's unmounted ok
      fi
      sleep 1 # Waiting is sometimes necessary
    done
    failed=1 # None of the tries worked! Oh dear.
    >&2 echo "Failed to unmount Pico"
  fi

  # Then clean up the directory if it exists
  if [ -d "$PICO_MNTDIR" ]; then
    sudo rmdir "$PICO_MNTDIR"
    failed=$? # Store the return code
  fi
  
  # Apologetic failure message
  if [ $failed -ne 0 ]; then
    >&2 echo Cleanup failed! Something has gone terribly wrong.
    >&2 echo "There is now a (probably) empty mountpoint at \"$PICO_MNTDIR\""
    >&2 echo You will have to clean this up manually. Very sorry for the inconvenience.
    exit 1 # Definitely want to make sure we stop at this point
  fi
}

# Ensure the user isn't just blindly running this
if [ $I_HAVE_CONFIRMED_THESE_ARE_CORRECT != yes ]; then
  >&2 echo "Hold on just a second! There's some configuration you need to do."
  >&2 echo "Not all systems behave the same, so there are some constant variables at the top of this script you will need to adjust."
  >&2 echo "The option to disable this message is alongside the other constants."
  exit 1
fi

# First, check if the device is connected
if [ ! -d "$PICO_MNTDIR" ]; then
  # If not, that's ok. We can try to mount it ourselves.
  # Well, provided the device is actually connected.
  if [ ! -b "$PICO_BLKDEV" ]; then
    >&2 echo "Can't find the Pico. Did you hold the BOOTSEL button while plugging it in?"
    exit 1
  fi
  
  echo Attempting to automatically mount...
  sudo mkdir -p "$PICO_MNTDIR" # Create the mountpoint
  if [ ! -d "$PICO_MNTDIR" ]; then
    # User must have failed to authenticate the sudo.
    >&2 echo "Unauthorised; Can't create mountpoint"
    exit 1
  fi
  
  # Then mount the device. The uid and gid must be specfied, otherwise there are errors during the copy operation.
  uid=$(id -u `whoami`)
  gid=$(id -g `whoami`)
  sudo mount -o uid=$uid,gid=$gid "$PICO_BLKDEV" "$PICO_MNTDIR"
  if [ $? -ne 0 ]; then # If we quit at this moment then we'd be leaving behind an empty mountpoint
    >&2 echo Failed to mount device!
    cleanup
    exit 1
  fi

  echo -e "Successfully mounted device!\n" # All went well!
fi

# Get the path to the parent folder containing this script
source="$(dirname $(realpath ${BASH_SOURCE[0]}))"

# Run the build script and exit if it fails
"$source/build.sh"
[ $? -ne 0 ] && exit 1

# Attempt to copy the firmware file
echo -n "Uploading uf2... "
cp "$source"/build/*.uf2 "$PICO_MNTDIR"
if [ $? -ne 0 ]; then
  >&2 echo -e \nUnable to copy firmware!
  exit 1
fi
echo Done.
cleanup

# Show a spinner while waiting for the serial port to show up
echo -n "Wait for chip reboot  "
i=0
declare -a anim=("─" "\\" "|" "/")
while [ ! -c "$SERIAL_PORT" ]; do
  sleep 0.1
  printf "\b${anim[$i]}"
  ((i=i+1))
  [ $i -ge ${#anim[@]} ] && i=0
done
echo

#minicom -D "$SERIAL_PORT" -b 115200
