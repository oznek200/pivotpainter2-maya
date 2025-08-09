
---

# PP2 X-Vector Exporter – Algorithm Overview

## Purpose

The **PP2 X-Vector Exporter** generates a texture (PNG, 8-bit RGBA) that stores each child transform’s **local +X axis vector** in world space, along with its depth in the hierarchy.
This is a required texture for Unreal Engine’s **Pivot Painter 2** shader to apply directional effects such as wind animation.

## Key Points

* **Stores local +X axis in world space**: Encodes X/Y/Z vector components into RGB.
* **Encodes hierarchy depth in alpha**: Depth values are mapped to specific alpha values for shader use.
* **Safe UV handling**: Creates and uses a dedicated UV set (`pp2_uv`) without affecting other UV data.

## Process Flow

1. **Root selection**

   * User selects the root transform (trunk) of the hierarchy.
   * If no selection exists, an error is shown.

2. **Hierarchy traversal**

   * Enumerates all transforms under the root (depth-first search).
   * Records:

     * Transform name
     * Parent index
     * Depth level

3. **UV grid setup**

   * Ensures `pp2_uv` exists for each mesh (creates it if missing).
   * Reads UV coordinates from `pp2_uv` to determine texture grid positions.
   * Columns = U, Rows = V (sorted top-left to bottom-right).

4. **X-Vector sampling**

   * Gets the world-space transform matrix for each node.
   * Extracts and normalizes the **local +X axis vector**.
   * Stores:

     * **R**: X-axis X component (`-1..1 → 0..1`)
     * **G**: X-axis Z component (`-1..1 → 0..1`)
     * **B**: X-axis Y component (`-1..1 → 0..1`)
     * **A**: Encoded depth (0, 1, 2, 3 mapped to 19/255, 7/255, 5.5/255, 5/255)

5. **Texture output**

   * Saves as **8-bit PNG** with RGBA channels.
   * No compression to maintain exact values.

## Implementation Notes

* **Depth encoding**: Fixed alpha values allow the PP2 shader to distinguish depth levels without ambiguity.
* **Channel mapping**: Note that G and B store Z/Y components (not Y/Z) to match PP2’s shader expectations.
* **Output path**: Defaults to `D:/PP2_out2` but can be changed in the constructor.

## Output Example

* **Filename**: `pp2_xvector.png`
* **Resolution**: `#rows × #columns` (matches UV grid)
* **Format**: 8-bit RGBA PNG

> **Usage in Unreal Engine**:
> The X-Vector texture works together with the Pivot Position texture to animate meshes in a PP2 material. RGB defines rotation axes per part, and A encodes depth for controlling hierarchical animation.

---
