#!/usr/bin/env python3
"""
Sensor Test Script for Sleep Monitor Wearable

This script connects to the wearable device via BLE and validates
that sensor data is being received correctly.

Requirements:
    pip install bleak asyncio

Usage:
    python test_sensors.py
"""

import asyncio
import struct
from datetime import datetime

try:
    from bleak import BleakClient, BleakScanner
except ImportError:
    print("Error: bleak library not installed")
    print("Install with: pip install bleak")
    exit(1)

# BLE UUIDs (must match firmware)
SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"
IMU_CHAR_UUID = "12345678-1234-1234-1234-123456789001"
PPG_CHAR_UUID = "12345678-1234-1234-1234-123456789002"
HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HR_CHAR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

# Test results
test_results = {
    'device_found': False,
    'connected': False,
    'imu_data_received': False,
    'ppg_data_received': False,
    'hr_data_received': False,
    'imu_samples': 0,
    'ppg_samples': 0,
    'hr_readings': []
}


def parse_imu_data(data: bytes):
    """Parse IMU data packet from BLE characteristic."""
    samples = []
    offset = 0
    sample_size = 14  # 2 bytes timestamp + 6x2 bytes data
    
    while offset + sample_size <= len(data):
        timestamp = struct.unpack('>H', data[offset:offset+2])[0]
        ax = struct.unpack('>h', data[offset+2:offset+4])[0] / 1000.0
        ay = struct.unpack('>h', data[offset+4:offset+6])[0] / 1000.0
        az = struct.unpack('>h', data[offset+6:offset+8])[0] / 1000.0
        gx = struct.unpack('>h', data[offset+8:offset+10])[0] / 10.0
        gy = struct.unpack('>h', data[offset+10:offset+12])[0] / 10.0
        gz = struct.unpack('>h', data[offset+12:offset+14])[0] / 10.0
        
        samples.append({
            'timestamp': timestamp,
            'accel': (ax, ay, az),
            'gyro': (gx, gy, gz)
        })
        offset += sample_size
    
    return samples


def parse_ppg_data(data: bytes):
    """Parse PPG data packet from BLE characteristic."""
    samples = []
    offset = 0
    sample_size = 8  # 2 bytes timestamp + 3 bytes red + 3 bytes IR
    
    while offset + sample_size <= len(data):
        timestamp = struct.unpack('>H', data[offset:offset+2])[0]
        red = (data[offset+2] << 16) | (data[offset+3] << 8) | data[offset+4]
        ir = (data[offset+5] << 16) | (data[offset+6] << 8) | data[offset+7]
        
        samples.append({
            'timestamp': timestamp,
            'red': red,
            'ir': ir
        })
        offset += sample_size
    
    return samples


def imu_notification_handler(sender, data):
    """Handle IMU data notifications."""
    global test_results
    test_results['imu_data_received'] = True
    samples = parse_imu_data(data)
    test_results['imu_samples'] += len(samples)
    
    if samples:
        s = samples[-1]
        print(f"  IMU: acc=({s['accel'][0]:+.2f}, {s['accel'][1]:+.2f}, {s['accel'][2]:+.2f}) g, "
              f"gyro=({s['gyro'][0]:+.1f}, {s['gyro'][1]:+.1f}, {s['gyro'][2]:+.1f}) deg/s")


def ppg_notification_handler(sender, data):
    """Handle PPG data notifications."""
    global test_results
    test_results['ppg_data_received'] = True
    samples = parse_ppg_data(data)
    test_results['ppg_samples'] += len(samples)
    
    if samples:
        s = samples[-1]
        print(f"  PPG: red={s['red']}, ir={s['ir']}")


def hr_notification_handler(sender, data):
    """Handle heart rate notifications."""
    global test_results
    test_results['hr_data_received'] = True
    
    if len(data) >= 2:
        hr = data[1]
        test_results['hr_readings'].append(hr)
        print(f"  Heart Rate: {hr} bpm")


async def scan_for_device(target_name: str = "SleepMon"):
    """Scan for the sleep monitor device."""
    print(f"Scanning for device '{target_name}'...")
    
    devices = await BleakScanner.discover(timeout=10.0)
    
    for device in devices:
        if device.name and target_name.lower() in device.name.lower():
            print(f"  Found: {device.name} ({device.address})")
            return device
    
    print("  Device not found!")
    return None


async def run_tests(device_address: str):
    """Run sensor validation tests."""
    global test_results
    
    print(f"\nConnecting to {device_address}...")
    
    async with BleakClient(device_address) as client:
        test_results['connected'] = True
        print("  Connected!")
        
        # List services
        print("\nDiscovered services:")
        for service in client.services:
            print(f"  {service.uuid}: {service.description}")
            for char in service.characteristics:
                print(f"    {char.uuid}: {char.properties}")
        
        # Subscribe to notifications
        print("\nSubscribing to sensor notifications...")
        
        try:
            await client.start_notify(IMU_CHAR_UUID, imu_notification_handler)
            print("  IMU notifications enabled")
        except Exception as e:
            print(f"  IMU subscription failed: {e}")
        
        try:
            await client.start_notify(PPG_CHAR_UUID, ppg_notification_handler)
            print("  PPG notifications enabled")
        except Exception as e:
            print(f"  PPG subscription failed: {e}")
        
        try:
            await client.start_notify(HR_CHAR_UUID, hr_notification_handler)
            print("  Heart Rate notifications enabled")
        except Exception as e:
            print(f"  HR subscription failed: {e}")
        
        # Collect data for 10 seconds
        print("\nCollecting data for 10 seconds...")
        await asyncio.sleep(10)
        
        # Stop notifications
        try:
            await client.stop_notify(IMU_CHAR_UUID)
            await client.stop_notify(PPG_CHAR_UUID)
            await client.stop_notify(HR_CHAR_UUID)
        except:
            pass


def print_summary():
    """Print test summary."""
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    print(f"Device found:      {'✓' if test_results['device_found'] else '✗'}")
    print(f"Connected:         {'✓' if test_results['connected'] else '✗'}")
    print(f"IMU data received: {'✓' if test_results['imu_data_received'] else '✗'} ({test_results['imu_samples']} samples)")
    print(f"PPG data received: {'✓' if test_results['ppg_data_received'] else '✗'} ({test_results['ppg_samples']} samples)")
    print(f"HR data received:  {'✓' if test_results['hr_data_received'] else '✗'}")
    
    if test_results['hr_readings']:
        avg_hr = sum(test_results['hr_readings']) / len(test_results['hr_readings'])
        print(f"Average HR:        {avg_hr:.1f} bpm")
    
    # Overall result
    all_passed = all([
        test_results['device_found'],
        test_results['connected'],
        test_results['imu_data_received'],
        test_results['ppg_data_received']
    ])
    
    print("\n" + "=" * 50)
    if all_passed:
        print("RESULT: ALL TESTS PASSED ✓")
    else:
        print("RESULT: SOME TESTS FAILED ✗")
    print("=" * 50)


async def main():
    """Main test routine."""
    print("=" * 50)
    print("Sleep Monitor Wearable - Sensor Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Scan for device
    device = await scan_for_device()
    
    if device:
        test_results['device_found'] = True
        await run_tests(device.address)
    
    print_summary()


if __name__ == "__main__":
    asyncio.run(main())

