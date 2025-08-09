# -*- coding: utf-8 -*-
"""
pp2_pivotposition.py  (safe-UV & no-error)
----------------------------------------------------------------
Pivot Painter 2: PivotPosition テクスチャ (EXR) 出力
  • 元 UV(set1 / map1) を変更しない
  • polyEditUV の -uvSet エラーを回避
"""

from __future__ import annotations
import os, sys, site, inspect
from typing import Optional
import numpy as np
import maya.cmds as cmds
import maya.api.OpenMaya as om2
import OpenEXR, Imath                             # type: ignore

# ---------- 3rd-party パス ----------------------------------------------------
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

ext_site = r"D:\Maya2023\Lib\site-packages"
if ext_site not in sys.path:
    sys.path.append(ext_site)
# -----------------------------------------------------------------------------

class PP2PivotPosExporter:
    UVSET   = "pp2_uv"                      # PP2 用 UV
    SRC_UV  = "map1"                        # コピー元
    DEPTH_A = {0:19/255.0, 1:7/255.0, 2:5.5/255.0, 3:5/255.0}

    # ----------------------------------------------------------------------
    def __init__(
        self,
        root:      Optional[str] = None,
        out_dir:   Optional[str] = None,
        base_name: str          = "",
    ):
        self.root      = root or self._require_selection()
        self.out_dir   = out_dir or r"D:/PP2_out2"
        self.base_name = base_name or "pp2_pivotpos"

    # ----------------------------------------------------------------------
    def export(self) -> None:
        tree = self._enum_tree(self.root)

        piv_w, uv_u, uv_v = {}, {}, {}
        u_set, v_set      = set(), set()

        for tr, *_ in tree:
            mesh = cmds.listRelatives(tr, s=True, ni=True,
                                      f=True, type="mesh")[0]
            self._ensure_uv(mesh)

            # pp2_uv を一時カレントにしてサンプル
            cur = cmds.polyUVSet(mesh, q=True, currentUVSet=True)[0]
            cmds.polyUVSet(mesh, e=True, uvSet=self.UVSET, currentUVSet=True)
            u, v = cmds.polyEditUV(f"{mesh}.map[0]", q=True)
            cmds.polyUVSet(mesh, e=True, uvSet=cur, currentUVSet=True)

            u, v = round(u,6), round(v,6)
            uv_u[tr], uv_v[tr] = u, v
            u_set.add(u), v_set.add(v)

            x,y,z = cmds.xform(tr, q=True, ws=True, rp=True)
            piv_w[tr] = om2.MPoint(x,y,z)

        # --- グリッド ------------------------------------------------------
        cols, rows = sorted(u_set), sorted(v_set, reverse=True)
        u_idx      = {u:i for i,u in enumerate(cols)}
        v_idx      = {v:i for i,v in enumerate(rows)}
        nC, nR     = len(cols), len(rows)

        enum2grid = {i: v_idx[uv_v[n]]*nC + u_idx[uv_u[n]]
                     for i,(n, *_ ) in enumerate(tree)}

        tex   = np.zeros((nR, nC, 4), np.float32)
        rootP = piv_w[self.root]

        for i,(tr, pidx, _) in enumerate(tree):
            r,c = v_idx[uv_v[tr]], u_idx[uv_u[tr]]
            dv  = piv_w[tr] - rootP
            tex[r,c,0] = dv.x
            tex[r,c,1] = piv_w[tr].z
            tex[r,c,2] = dv.y
            tex[r,c,3] = self._pack_parent(enum2grid.get(pidx, 0))

        os.makedirs(self.out_dir, exist_ok=True)
        path = os.path.join(self.out_dir, f"{self.base_name}.exr")
        self._save_exr(path, tex)

        cmds.inViewMessage(amg=f"[PP2] PivotPos → {path}",
                           pos="midCenter", fade=True)

    # ----------------------------------------------------------------------
    # helpers
    # ----------------------------------------------------------------------
    @staticmethod
    def _require_selection() -> str:
        sel = cmds.ls(sl=True, l=True, type="transform")
        if not sel:
            cmds.error("幹 Transform を 1 つ選択してください")
        return sel[0]

    @staticmethod
    def _pack_parent(idx: int) -> float:
        return (1024+idx) / float(2**24)

    @classmethod
    def _enum_tree(cls, root: str):
        st, out = [(root,-1,0)], []
        while st:
            n,p,d = st.pop()
            out.append((n,p,d))
            for ch in reversed(cmds.listRelatives(n, c=True, f=True,
                                                  type="transform") or []):
                st.append((ch,len(out)-1,d+1))
        return out

    # ----------------------------------------------------------
    def _ensure_uv(self, mesh: str) -> None:
        """pp2_uv が無ければ map1 から複製。編集は後でまとめて行う"""
        if self.UVSET not in cmds.polyUVSet(mesh, q=True, auv=True):
            cmds.polyUVSet(mesh,
                           copy=True,
                           uvSet=self.SRC_UV,
                           newUVSet=self.UVSET)

    # ----------------------------------------------------------
    @staticmethod
    def _save_exr(path: str, arr: np.ndarray) -> None:
        h,w,_ = arr.shape
        hdr   = OpenEXR.Header(w, h)
        hdr["channels"] = {c: Imath.Channel(Imath.PixelType(
            Imath.PixelType.FLOAT)) for c in "RGBA"}
        out = OpenEXR.OutputFile(path, hdr)
        out.writePixels({c: arr[...,i].tobytes() for i,c in enumerate("RGBA")})
        out.close()

# ----------------------------------------------------------------------
if __name__ == "__main__":
    PP2PivotPosExporter().export()
