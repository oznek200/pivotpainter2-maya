# -*- coding: utf-8 -*-
from __future__ import annotations
"""
pp2_XVector.py
-----------------------------------
Pivot Painter 2 用：X-Vector テクスチャ エクスポーター

PNG (8-bit RGBA)
    R = 子 Transform のローカル +X 軸ベクトルのワールド X 成分 (−1..1 → 0..1)
    G = 子 Transform のローカル +X 軸ベクトルのワールド Y 成分 (−1..1 → 0..1)
    B = 子 Transform のローカル +X 軸ベクトルのワールド Z 成分 (−1..1 → 0..1)
    A = 階層深度 α  (0,1,2,3 → 19/255,7/255,5.5/255,5/255)
"""
import os, sys, site, inspect
import numpy as np
import maya.cmds as cmds
import maya.api.OpenMaya as om2

# -------- サードパーティ検索パス ------------------------------------------------
def _module_dir(fallback: str | None = None) -> str:
    if "__file__" in globals():
        return os.path.dirname(__file__)
    try:
        p = inspect.getsourcefile(sys.modules[__name__])  # type: ignore[arg-type]
        if p:
            return os.path.dirname(p)
    except TypeError:
        pass
    return fallback or os.getcwd()

_here = _module_dir()
site.addsitedir(os.path.join(os.path.dirname(_here), "third_party"))

ext_site = r"D:\Maya2023\Lib\site-packages"      # Pillow などを置いたフォルダ
if ext_site not in sys.path:
    sys.path.append(ext_site)

from PIL import Image   # noqa: F401

# -------------------------------------------------------------------------------
class PP2XVectorExporter:
    """X-Vector PNG を書き出すユーティリティ"""

    UVSET: str = "pp2_uv"
    DEPTH_ALPHA = {0: 19/255.0, 1: 7/255.0, 2: 5.5/255.0, 3: 5/255.0}

    # ------------------------------------------------------------------
    def __init__(
        self,
        root: str | None = None,
        out_dir: str | None = None,
        base_name: str = "",
    ):
        """
        Parameters
        ----------
        root      : ルート Transform 名（None なら現在の選択）
        out_dir   : 保存フォルダ
        base_name : ファイル名ベース（拡張子なし）
        """
        self.root      = root or self._require_selection()
        self.out_dir   = out_dir or r"D:/PP2_out2"
        self.base_name = base_name or "pp2_xvector"

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def export(self) -> None:
        """X-Vector テクスチャを書き出し"""
        tree = self._enum_tree(self.root)

        # --- UV グリッド取得 -----------------------------------------
        uv_u, uv_v, u_set, v_set = {}, {}, set(), set()
        for tr, _, _ in tree:
            mesh = cmds.listRelatives(tr, s=True, ni=True, f=True, type="mesh")[0]
            self._ensure_uv(mesh)

            u, v = cmds.polyEditUV(f"{mesh}.map[0]", q=True)
            u, v = round(u, 6), round(v, 6)
            uv_u[tr], uv_v[tr] = u, v
            u_set.add(u), v_set.add(v)

        cols = sorted(u_set)
        rows = sorted(v_set, reverse=True)
        u_idx = {u: i for i, u in enumerate(cols)}
        v_idx = {v: i for i, v in enumerate(rows)}
        nC, nR = len(cols), len(rows)

        tex = np.zeros((nR, nC, 4), np.float32)

        # --- X-Vector サンプリング -----------------------------------
        for tr, _, depth in tree:
            r = v_idx[uv_v[tr]]
            c = u_idx[uv_u[tr]]

            m = cmds.xform(tr, q=True, ws=True, m=True)
            vx = om2.MVector(m[0], m[1], m[2]).normalize()  # ローカル+X → ワールド

            tex[r, c, 0] = vx.x * 0.5 + 0.5  # -1..1 → 0..1
            tex[r, c, 1] = vx.z * 0.5 + 0.5
            tex[r, c, 2] = vx.y * 0.5 + 0.5
            tex[r, c, 3] = self.DEPTH_ALPHA.get(depth, 5/255.0)

        # --- 保存 -----------------------------------------------------
        os.makedirs(self.out_dir, exist_ok=True)
        out_path = os.path.join(self.out_dir, f"{self.base_name}.png")
        self._save_png_rgba(out_path, tex)

        cmds.inViewMessage(
            amg=f"[PP2] X-Vector 書き出し完了 → {out_path}",
            pos="midCenter", fade=True
        )

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _require_selection() -> str:
        sel = cmds.ls(sl=True, l=True, type="transform")
        if not sel:
            cmds.error("幹 Transform を 1 つ選択してください")
        return sel[0]

    @classmethod
    def _enum_tree(cls, root: str):
        """深さ優先で (node, parentIdx, depth) を列挙"""
        st, out = [(root, -1, 0)], []
        while st:
            node, pidx, d = st.pop()
            out.append((node, pidx, d))
            for ch in reversed(cmds.listRelatives(node, c=True, f=True,
                                                  type="transform") or []):
                st.append((ch, len(out)-1, d+1))
        return out

    # ----------------------------------------------------------
    def _ensure_uv(self, mesh: str) -> None:
        """mesh に self.UVSET を準備しカレント化"""
        if self.UVSET not in cmds.polyUVSet(mesh, q=True, auv=True):
            cmds.polyUVSet(mesh, create=True, uvSet=self.UVSET)
        cmds.polyUVSet(mesh, e=True, uvSet=self.UVSET, currentUVSet=True)

    # ----------------------------------------------------------
    @staticmethod
    def _save_png_rgba(path: str, arr: np.ndarray) -> None:
        img8 = np.rint(np.clip(arr, 0.0, 1.0) * 255.0).astype(np.uint8)
        Image.fromarray(img8, "RGBA").save(path, compress_level=0)

# ----------------------------------------------------------------------
# 使い方
# ----------------------------------------------------------------------
# 1) ルート Transform を選択
# 2) >>> from pp2_export_xvector_texture_class import PP2XVectorExporter
#    >>> PP2XVectorExporter().export()
# ----------------------------------------------------------------------
if __name__ == "__main__":
    PP2XVectorExporter().export()
