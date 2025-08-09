# -*- coding: utf-8 -*-
"""
set_pp2UV.py
-----------------------------------------
Pivot Painter 2 用：Transform ごとに 1 ドットを自動配置（クラス版）
"""

from __future__ import annotations
import math
import maya.cmds as cmds


class PP2UVAutoSquare:
    """Pivot Painter 2 用 UV オートレイアウトツール"""

    # 既定値
    UVSET: str = "pp2_uv"   # PP2 用に使う新規 / 既存 UV セット
    SRC_UV: str = "map1"    # Mesh が持つデフォルト UV セット
    MINCOL: int = 5         # PP2 既定：これより列数を小さくしない

    # ------------------------------------------------------------------
    # public
    # ------------------------------------------------------------------
    def __init__(
        self,
        root: str | None = None,
        uvset: str | None = None,
        src_uv: str | None = None,
        mincol: int | None = None,
    ) -> None:
        """
        Parameters
        ----------
        root   : ルート Transform 名（None なら現在の選択から取得）
        uvset  : 出力先 UV セット名
        src_uv : コピー元 UV セット名
        mincol : 最小列数
        """
        self.root   = root or self._get_root_from_selection()
        self.UVSET  = uvset   or self.UVSET
        self.SRC_UV = src_uv  or self.SRC_UV
        self.MINCOL = mincol  or self.MINCOL

    # ------------------------------------------------------------------
    def execute(self) -> None:
        """メイン処理"""
        trs  = list(self._walk(self.root))
        n    = len(trs)
        cols = self._best_cols(n)
        rows = int(math.ceil(n / float(cols)))

        du = 1.0 / cols
        dv = 1.0 / rows

        for i, tr in enumerate(trs):
            col_idx = i % cols
            row_idx = i // cols
            u = du * (col_idx + 0.5)
            v = 1.0 - dv * (row_idx + 0.5)

            for mesh in cmds.listRelatives(tr, s=True, ni=True,
                                           f=True, type="mesh") or []:
                self._ensure_uv(mesh)
                cmds.polyEditUV(mesh + ".map[*]", u=u, v=v, su=0, sv=0)

        msg = f"{self.UVSET}: cols={cols} rows={rows}   RowHeight={dv:.5f}"
        cmds.inViewMessage(amg=msg, pos="midCenter", fade=True)
        print(f"★ UE の Material Instance で RowHeight = {dv:.5f}")

    # ------------------------------------------------------------------
    # private utility
    # ------------------------------------------------------------------
    @staticmethod
    def _get_root_from_selection() -> str:
        sel = cmds.ls(sl=True, l=True, type="transform")
        if not sel:
            cmds.error("幹 Transform を 1 つ選択してください")
        return sel[0]

    @staticmethod
    def _walk(root: str):
        """root 以下の Transform 階層を深さ優先で列挙"""
        st = [root]
        while st:
            n = st.pop()
            yield n
            st.extend(cmds.listRelatives(n, c=True, f=True,
                                         type="transform") or [])

    # ----------------------------------------
    def _ensure_uv(self, mesh: str) -> None:
        """
        mesh に self.UVSET が無ければ self.SRC_UV からコピーし、
        その UVSET をカレントにして X 投影で 1 点だけ作成
        """
        if self.UVSET not in cmds.polyUVSet(mesh, q=True, auv=True):
            cmds.polyUVSet(mesh, copy=True,
                           uvSet=self.SRC_UV, newUVSet=self.UVSET)

        cmds.polyUVSet(mesh, e=True, uvSet=self.UVSET, currentUVSet=True)
        cmds.polyProjection(mesh + ".f[*]", md="x", ibd=True, ch=False)

    # ----------------------------------------
    def _best_cols(self, n: int) -> int:
        """n ピースをほぼ正方形に近い分割にする列数を返す"""
        root = int(math.sqrt(n))
        cand = [max(self.MINCOL, root + i) for i in range(0, 3)]
        return min(cand, key=lambda c: abs(math.ceil(n / float(c)) - c))


# ----------------------------------------------------------------------
# 使い方例
# ----------------------------------------------------------------------
#   1) ルート Transform を 1 つ選択
#   2) 以下を実行
#
#       import pp2_make_uv_auto_square_fixed_v2_class as pp2
#       pp2.PP2UVAutoSquare().execute()
#
#   ── 任意で ────────────────────────────
#       tool = pp2.PP2UVAutoSquare(uvset="my_uv", mincol=4)
#       tool.execute()
# ----------------------------------------------------------------------
if __name__ == "__main__":
    PP2UVAutoSquare().execute()
