cmake_minimum_required(VERSION 3.13)

# Set the PICO_SDK_PATH if it is undefined.
# The build.sh script will override this, if you're using that.
if(NOT DEFINED ENV{PICO_SDK_PATH})
  set(ENV{PICO_SDK_PATH} "../../../pico-sdk")
endif()

# initialize the SDK based on PICO_SDK_PATH
# note: this must happen before project()
include(pico_sdk_import.cmake)

project(my_project)

# initialize the Raspberry Pi Pico SDK
pico_sdk_init()

# rest of your project
add_executable(lora_chat
    src/main.c
)

# Enable the USB serial port
pico_enable_stdio_usb(lora_chat 1)

target_link_libraries(lora_chat
    pico_stdlib # Add pico_stdlib library which aggregates commonly used features
)

# create map/bin/hex/uf2 file in addition to ELF.
pico_add_extra_outputs(lora_chat)
