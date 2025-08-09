# =====================================================================
#  pivot_center.py
# ---------------------------------------------------------------------
#  1. 頂点 / エッジ / フェースを選択して実行
#  2. 選択成分のワールド座標を平均 → その Transform のピボットを移動
# =====================================================================
import maya.cmds as cmds
import maya.api.OpenMaya as om2


class PivotMover:
    """選択頂点（複数可）の中心にピボットを移動するユーティリティ"""

    # ---------------------------------------------------------------
    # 内部 util
    # ---------------------------------------------------------------
    @staticmethod
    def _transform_from_component(comp):
        """
        comp: 'xxx|yyyShape.vtx[3]' のようなコンポーネントパス
        戻り値: トップレベル Transform ノード
        """
        obj = cmds.ls(comp, o=True, long=True)[0]         # コンポ→オブジェクト
        if cmds.nodeType(obj) == "mesh":                  # shape の場合は親へ
            obj = cmds.listRelatives(obj, p=True, pa=True)[0]
        return obj

    # ---------------------------------------------------------------
    # メイン処理
    # ---------------------------------------------------------------
    def move_to_selection_center(self):
        """現在の頂点選択の中心にピボットを移動"""
        sel = cmds.ls(sl=True, fl=True)  # flat list で取得
        if not sel:
            cmds.warning("頂点を選択してください。")
            return

        verts_by_xform = {}
        for v in sel:
            try:
                pos = cmds.pointPosition(v, world=True)
            except RuntimeError:
                cmds.warning(f"{v} は頂点ではありません。スキップします。")
                continue

            xform = self._transform_from_component(v)
            verts_by_xform.setdefault(xform, []).append(om2.MVector(pos))

        for xform, vecs in verts_by_xform.items():
            center = sum(vecs, om2.MVector()) / len(vecs)
            cmds.xform(xform, ws=True, piv=(center.x, center.y, center.z))
            print(f"[PivotToSelectionCenter] {xform} → {center}")

        cmds.inViewMessage(
            amg="<hl>Pivot 移動完了</hl>", pos="topCenter", fade=True
        )


# ------------------------- 使い方 --------------------------
#   1) 頂点やフェースを選択
#   2) 下記 2 行を実行
#
# mover = PivotMover()
# mover.move_to_selection_center()
#
# -----------------------------------------------------------
if __name__ == "__main__":
    PivotMover().move_to_selection_center()
