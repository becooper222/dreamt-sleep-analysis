# Enclosure Design

3D printable enclosure for the sleep monitor wearable.

## Files

- `enclosure_top.stl` - Top shell
- `enclosure_bottom.stl` - Bottom shell with sensor window
- `strap_clip.stl` - Wristband attachment clips
- `enclosure.f3d` - Fusion 360 source file
- `enclosure.step` - STEP export for other CAD software

## Dimensions

| Parameter | Value |
|-----------|-------|
| Length | 45mm |
| Width | 35mm |
| Height | 15mm |
| Weight | ~12g (without electronics) |

## Design Features

### Top Shell
- Recessed area for status LED visibility
- USB-C port cutout
- Snap-fit clips for assembly

### Bottom Shell
- Optical window for PPG sensor
- Skin-contact surface
- Ventilation for temperature sensor

### Wristband
- Standard 20mm watch band compatible
- Quick-release spring bar slots
- Or: integrated silicone strap design

## Printing Guidelines

### Recommended Settings

| Parameter | Value |
|-----------|-------|
| Material | PETG or ABS |
| Layer Height | 0.15mm |
| Infill | 30% |
| Walls | 3 |
| Support | Minimal (bridges only) |
| Orientation | Flat side down |

### Material Considerations

- **PLA**: Not recommended (poor skin contact, warps with body heat)
- **PETG**: Good balance of strength and comfort
- **ABS**: Most durable, requires ventilation when printing
- **TPU**: Can be used for strap components

### Post-Processing

1. Remove support material carefully
2. Sand mating surfaces for better fit
3. Test-fit electronics before final assembly
4. Optional: Apply clear coat for better finish

## Assembly

1. Insert PCB into bottom shell
2. Route battery cable
3. Connect battery
4. Place top shell and snap into place
5. Attach wristband

## Optical Window

For PPG sensor functionality:

1. Use clear/transparent filament for sensor area, OR
2. Leave 10mm circular hole and seal with:
   - Clear epoxy
   - Thin glass or acrylic disc
   - Medical-grade adhesive film

## Waterproofing (Optional)

For sweat/splash resistance:

1. Apply silicone sealant to shell seam
2. Use O-ring gasket (2mm diameter)
3. Seal USB port with rubber plug when not charging

## Comfort Considerations

- Round all edges that contact skin
- Ensure PPG sensor has slight pressure against skin
- Allow 1-2mm gap for airflow
- Consider hypoallergenic coating for sensitive skin

