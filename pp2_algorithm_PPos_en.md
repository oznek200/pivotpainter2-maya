
---

# PP2 Pivot Position Exporter – Algorithm Overview

## Purpose

The **PP2 Pivot Position Exporter** outputs a texture (EXR) that encodes each object’s pivot position and its parent index in a format compatible with Unreal Engine’s **Pivot Painter 2** workflow.

## Key Points

* **Preserves original UV (map1)**: The script avoids overwriting the model’s original UV set.
* **Safe UV duplication**: Creates a dedicated UV set (`pp2_uv`) to store PP2 layout without affecting other UV data.
* **Error avoidance**: Bypasses the `polyEditUV -uvSet` flag error by ensuring the target UV set exists before switching.

## Process Flow

1. **Root selection**

   * The user selects the root transform (trunk) of the hierarchy.
   * If no selection exists, an error is displayed.

2. **Hierarchy traversal**

   * Recursively enumerates all transforms under the root.
   * Records:

     * Transform name
     * Parent index
     * Depth level in hierarchy

3. **UV grid setup**

   * Reads the `pp2_uv` coordinates of each mesh.
   * Builds a 2D grid (columns = U, rows = V) sorted from top-left to bottom-right.
   * Each cell corresponds to one transform.

4. **Pivot position sampling**

   * Gets each transform’s **world-space rotate pivot position**.
   * Computes offsets relative to the root’s pivot.
   * Stores:

     * **R**: Offset X
     * **G**: Absolute world Z
     * **B**: Offset Y
     * **A**: Packed parent index (normalized)

5. **Texture output**

   * Saves a **32-bit float EXR** with RGBA channels.
   * Channels:

     * **R**: ΔX (relative to root)
     * **G**: Absolute Z
     * **B**: ΔY
     * **A**: Encoded parent index
   * Uses OpenEXR via Python bindings for precise floating-point output.

## Implementation Notes

* **UV creation**: If `pp2_uv` doesn’t exist, it is duplicated from `map1`.
* **Parent index encoding**: `(1024 + index) / (2^24)` ensures high precision for decoding in shaders.
* **File path**: Output folder defaults to `D:/PP2_out2`, but can be changed in the constructor.

## Output Example

* **Filename**: `pp2_pivotpos.exr`
* **Resolution**: `#rows × #columns` (matches UV grid)
* **Format**: 32-bit RGBA, OpenEXR

> **Usage in Unreal Engine**:
> Load the EXR into a PP2-compatible material. The parent index in the A channel allows shader-based hierarchical transformations, while R/G/B provide pivot offsets.

---
