import wmi

_wmi = wmi.WMI()


def collect_hardware():
    result = {
        "cpu": [],
        "gpu": [],
        "memory": [],
        "disks": []
    }

    for cpu in _wmi.Win32_Processor():
        result["cpu"].append({
            "name": cpu.Name.strip() if cpu.Name else None,
            "manufacturer": cpu.Manufacturer,
            "cores": cpu.NumberOfCores,
            "threads": cpu.NumberOfLogicalProcessors,
            "max_clock_mhz": cpu.MaxClockSpeed
        })

    for gpu in _wmi.Win32_VideoController():
        result["gpu"].append({
            "name": gpu.Name,
            "driver_version": gpu.DriverVersion,
            "vram_bytes": ((int(gpu.AdapterRAM) + (1 << 32)) % (1 << 32)) if gpu.AdapterRAM is not None else None
        })

    for memory in _wmi.Win32_PhysicalMemory():
        result["memory"].append({
            "manufacturer": memory.Manufacturer,
            "part_number": memory.PartNumber.strip() if memory.PartNumber else None,
            "capacity_bytes": int(memory.Capacity) if memory.Capacity else None,
            "speed_mhz": memory.Speed
        })

    for disk in _wmi.Win32_DiskDrive():
        result["disks"].append({
            "model": disk.Model,
            "media_type": disk.MediaType,
            "interface": disk.InterfaceType,
            "size_bytes": int(disk.Size) if disk.Size else None
        })

    return result
