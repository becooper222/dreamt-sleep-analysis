# PCB Design

This directory contains the PCB layout files for the sleep monitor wearable.

## Files

- `sleep_monitor.kicad_pcb` - KiCad PCB layout
- `gerbers/` - Manufacturing files (Gerber, drill)
- `sleep_monitor_3d.step` - 3D model export

## PCB Specifications

| Parameter | Value |
|-----------|-------|
| Dimensions | 35mm × 25mm |
| Layers | 2 |
| Thickness | 1.6mm |
| Copper | 1oz |
| Finish | HASL or ENIG |
| Min trace | 0.2mm |
| Min space | 0.2mm |

## Layer Stack

| Layer | Usage |
|-------|-------|
| Top | Components, signal routing |
| Bottom | Ground plane, power routing |

## Design Considerations

### Component Placement

1. **ESP32-S3-Zero**: Center of board, USB-C accessible at edge
2. **MAX30102**: Bottom of board, exposed for skin contact
3. **MPU6050**: Near center for best motion sensing
4. **Battery Connector**: Edge of board for easy connection

### Routing Guidelines

- I2C traces: Keep short and parallel
- Power traces: Minimum 0.5mm width
- Ground plane: Solid pour on bottom layer
- Antenna area: No copper under ESP32 antenna

### Manufacturing

Recommended fabrication houses:
- JLCPCB (China)
- PCBWay (China)
- OSH Park (USA)

## Assembly Notes

1. Solder SMD components first (resistors, capacitors)
2. Add module headers or solder modules directly
3. Test continuity before powering on
4. Program firmware via USB before final assembly

