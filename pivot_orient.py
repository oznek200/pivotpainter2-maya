# =====================================================================
#  pivot_orient.py
# ---------------------------------------------------------------------
#  選択 Transform / Shape について：
#    1. ピボットはそのまま         （位置のみ使用）
#    2. バウンディングボックス中心を取得
#    3. vec = center - pivot  を +X に合わせる回転を計算
#    4. Maya 2023+ : manipPivot + bakeCustomOrient
#       Maya 2022- : orientGrp(親) を挿入して回転を打ち消す
# =====================================================================
import math, numpy as np
import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.mel as mel


class PivotOrienter:
    """選択オブジェクトのピボットを BBox 中心方向へ向けるユーティリティ"""

    # ---------- util : quaternion (+X → vec) → Euler XYZ ----------
    @staticmethod
    def _euler_from_x(vec):
        """+X を vec に重ねるクォータニオンを XYZ オイラー角[deg]で返す"""
        q = om.MQuaternion(om.MVector(1, 0, 0), vec.normal())
        e = q.asEulerRotation()
        return [round(math.degrees(a), 6) for a in (e.x, e.y, e.z)]

    # ---------- Maya 2022 fallback : orient 親グループを挿入 ----------
    @staticmethod
    def _insert_orient_parent(tr, rx, ry, rz):
        parent = cmds.listRelatives(tr, p=True, f=True)
        ori = cmds.createNode("transform", n="ori_" + tr.split("|")[-1])
        if parent:
            cmds.parent(ori, parent[0], r=True)

        piv = cmds.xform(tr, q=True, ws=True, rp=True)
        cmds.xform(ori, ws=True, t=piv, ro=[rx, ry, rz])
        cmds.parent(tr, ori, r=True)

        # 子側のローカル回転を打ち消す
        cmds.setAttr(tr + ".rotate", -rx, -ry, -rz)

    # ---------- メイン処理 ----------
    def __init__(self):
        # Maya 2023 以降なら bakeCustomOrient が利用可能
        self.has_bake = mel.eval('exists "bakeCustomOrient"')

    def orient_selected(self):
        """現在の選択に対してピボットを BBox 方向へ向ける"""
        sel = cmds.ls(sl=True, long=True)
        if not sel:
            cmds.warning("Nothing selected.")
            return

        count = 0
        for node in sel:
            # Transform ノードへ正規化
            if cmds.nodeType(node) != "transform":
                p = cmds.listRelatives(node, p=True, f=True) or []
                if not p:
                    continue
                node = p[0]

            # メッシュ Shape を取得
            shapes = cmds.listRelatives(node, s=True, ni=True, f=True, type="mesh")
            if not shapes:
                continue
            shape = shapes[0]

            # ピボット（world）と BBox 中心（world）
            pivot = np.array(cmds.xform(node, q=True, ws=True, rp=True), dtype=np.float64)
            bb = cmds.exactWorldBoundingBox(shape)
            center = np.array(
                [(bb[0] + bb[3]) / 2.0, (bb[1] + bb[4]) / 2.0, (bb[2] + bb[5]) / 2.0],
                dtype=np.float64,
            )

            vec = center - pivot
            if np.allclose(vec, 0):
                cmds.warning(f"Skip (pivot == center): {node}")
                continue

            rx, ry, rz = self._euler_from_x(om.MVector(*vec))

            if self.has_bake:
                cmds.select(node, r=True)
                cmds.manipPivot(o=(rx, ry, rz))              # ピボット操作ツールに回転をセット
                mel.eval(f"bakeCustomOrient {rx} {ry} {rz}")  # ローカル軸へベイク
            else:
                self._insert_orient_parent(node, rx, ry, rz)  # 親グループ方式

            count += 1

        # manipPivot を元に戻す
        if self.has_bake:
            cmds.manipPivot(reset=True)

        cmds.inViewMessage(
            amg=f"<hl>BBox-Pivot oriented : {count} obj</hl>",
            pos="topCenter",
            fade=True,
        )


# ------------------------- 使い方 --------------------------
#   1) オブジェクトを選択
#   2) 下記 2 行を実行
#
# orienter = PivotOrienter()
# orienter.orient_selected()
#
# -----------------------------------------------------------
if __name__ == "__main__":
    # Maya Script Editor でそのまま走らせても OK
    PivotOrienter().orient_selected()
