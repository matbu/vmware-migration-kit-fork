#!/bin/bash
UDEV_RULES_FILE="${UDEV_RULES_FILE:-/etc/udev/rules.d/70-persistent-net.rules}"

exec 3>&1
log() {
    echo $@ >&3
}

extract_mac_addresses() {
  local macs=()
  # Iterate through /sys/class/net to find MAC addresses
  for device in /sys/class/net/*; do
    if [[ -f "$device/address" ]]; then
      mac=$(cat "$device/address" 2>/dev/null)
      if [[ -n "$mac" ]]; then
        macs+=("$mac")
      fi
    fi
  done
  # Return the list of MAC addresses
  echo "${macs[@]}"
}

extract_ifconfig() {
  declare -A devices
  interfaces=$(ifconfig -a | grep -o "^[a-zA-Z0-9@]*" | grep -v "^$")
  log "Interfaces found: $interfaces"

  for interface in $interfaces; do
    mac=$(cat "/sys/class/net/$device/address" 2>/dev/null)
    log "Interface: $interface, MAC: $mac"
    if [[ -n "$mac" ]]; then
      devices["$interface"]="$mac"
    fi
  done
  log "Devices: ${devices}"

  for device in "${!devices[@]}"; do
    log "  Device: $device, MAC: ${devices[$device]}"
  done

  for device in "${!devices[@]}"; do
    log "$device:${devices[$device]}"
    echo "$device:${devices[$device]}"
  done
}

generate_udev_rules() {
  local devices=("$@")
  echo "Generating udev rules..."
  echo "# Persistent network device rules" > "$UDEV_RULES_FILE"
  for entry in "${devices[@]}"; do
    # Parse the serialized string (device:MAC)
    device="${entry%%:*}"
    mac="${entry#*:*}"
    if [[ -n "$device" && -n "$mac" ]]; then
      echo "SUBSYSTEM==\"net\",ACTION==\"add\",ATTR{address}==\"$mac\",NAME=\"$device\"" >> "$UDEV_RULES_FILE"
    fi
  done
  echo "Udev rules written to $UDEV_RULES_FILE"
}

extract_nm_connections() {
  declare -A devices
  local macs=("$@") # Accept the MAC list as arguments
  local i=0         # Initialize index

  for file in /etc/NetworkManager/system-connections/*; do
    if [[ -f "$file" ]]; then
      device=$(grep -oP '(?<=^interface-name=).*' "$file")
      log "File: $file, Device: $device"

      if [[ -n "$device" ]]; then
        mac=${macs[i]}
        log "Device: $device, MAC: $mac"

        if [[ -n "$mac" ]]; then
          devices["$device"]="$mac"
        fi
        i=$((i + 1))
      fi
    fi
  done

  log "Devices from NetworkManager: ${devices[@]}"

  for device in "${!devices[@]}"; do
    log "$device:${devices[$device]}"
    echo "$device:${devices[$device]}"
  done
}


extract_sysconfig_connections() {
  declare -A devices

  for file in /etc/sysconfig/network-scripts/ifcfg-*; do
    if [[ -f "$file" ]]; then
      # Extract the device name (DEVICE= value)
      device=$(grep -oP '(?<=^DEVICE=).*' "$file" | tr -d '"')
      log "File: $file, Device: $device"
      mac=$(grep -oP '(?<=^HWADDR=).*' "$file" | tr -d '"')
      if [[ -n "$device" && -n "$mac" ]]; then
          devices["$device"]="$mac"
      fi
    fi
  done
  log "Devices from sysconfig: ${devices[@]}"
  for device in "${!devices[@]}"; do
    log "$device:${devices[$device]}"
    echo "$device:${devices[$device]}"
  done
}


main() {
  macs=($(extract_mac_addresses))
  log $macs
  exdevices=($(extract_nm_connections "${macs[@]}"))
  if [[ ${#exdevices[@]} -eq 0 ]]; then
    log "No network devices found in NetworkManager. Trying sysconfig..."
    exdevices=($(extract_sysconfig_connections))
    if [[ ${#exdevices[@]} -eq 0 ]]; then
      log "No network devices found. Trying . Ifcfg..."
      exdevices=($(extract_ifconfig))
      if [[ ${#exdevices[@]} -eq 0 ]]; then
        log "No network devices... existing"
        exit 1
        fi
    fi
  fi
  generate_udev_rules "${exdevices[@]}"
}
main
