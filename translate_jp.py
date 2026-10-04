"""Japanese translation dictionary for drawing_for_simutrans_addon_making.

Keys are the English UI strings exactly as written in
drawing_for_simutrans_addon_making.py; values are their Japanese
translations. Strings missing from JP are shown in English as-is, so a new
UI string only needs an entry here to be translated.
Strings containing {name} placeholders are filled in with str.format()
after translation, so keep the same placeholders in the Japanese text."""

LANGUAGES = {
    "en": "English",
    "ja": "日本語",
}

JP = {
    # ---- tabs ----
    "File": "ファイル",
    "Edit": "編集",
    "Special Colors": "特殊色",
    "Layer": "レイヤー",
    "Process": "加工",
    "Color Replace": "色置換",

    # ---- File tab ----
    "New": "新規",
    "Open": "開く",
    "Save": "保存",
    "Save As...": "名前を付けて保存...",
    "Language:": "言語:",

    # ---- Edit tab ----
    "Undo": "元に戻す",
    "Redo": "やり直し",
    "Copy": "コピー",
    "Cut": "切り取り",
    "Paste": "貼り付け",
    "Clear Outside": "選択範囲外を消去",
    "Confirm Paste": "貼り付けを確定",

    # ---- Special Colors tab ----
    "Simutrans Special Colors": "Simutrans 特殊色",
    "Highlight Special Colors": "特殊色を強調表示",

    # ---- toolbar ----
    "Pen": "ペン",
    "Fill": "塗りつぶし",
    "Line": "直線",
    "Eraser": "消しゴム",
    "Pipette": "スポイト",
    "Move": "移動",
    "Select": "選択",
    "ParaSelect": "形状選択",
    "Rect": "矩形",
    "FillRect": "塗り矩形",
    "Prism": "直方体",
    "Color": "色",
    "Alpha": "アルファ",
    "Zoom[%]": "ズーム[%]",
    "Box": "長方形",
    "H-Para": "壁面",
    "D-Para": "床面",
    "Height:": "高さ:",
    "Left:": "左:",
    "Right:": "右:",

    # ---- Layer tab ----
    "New Layer": "新規レイヤー",
    "Duplicate Layer": "レイヤーを複製",
    "Delete Layer": "レイヤーを削除",
    "▲ Up": "▲ 上へ",
    "▼ Down": "▼ 下へ",
    "Export Layer": "レイヤーを書き出し",
    "Export All Layer": "全レイヤーを書き出し",
    "Import to Layer": "レイヤーに読み込み",
    "Merge Layer Down": "下のレイヤーと結合",
    "Add": "加算",
    "Mult": "乗算",
    "Replace": "置換",
    "Bright": "比較(明)",
    "Lightmap": "ライトマップ",
    "Layer Offset": "レイヤーオフセット",
    "Apply": "適用",

    # ---- Process tab ----
    "Simutrans Guides": "Simutrans ガイド",
    "Show": "表示",
    "Build:": "製作:",
    "Play:": "ゲーム:",
    "Y-Off:": "Yオフセット:",
    "Turn gray": "グレー化",
    "Delete Background": "背景を削除",
    "add margin (build_paksize)": "余白追加 (製作paksize)",
    "Image Resize": "画像の拡大縮小",
    "New Size:": "新サイズ:",
    "Apply Resize": "サイズ変更を適用",

    # ---- Color Replace tab ----
    "Original (R,G,B):": "元の色 (R,G,B):",
    "Update (R,G,B):": "新しい色 (R,G,B):",
    "Use Current": "現在の色を使用",
    "Range (int or R,G,B):": "範囲 (整数 または R,G,B):",
    "New Alpha:": "新しいアルファ:",
    "Ignore Special Color": "特殊色を除外",
    "Preview": "プレビュー",
    "Replace To": "置換先",
    "Update Color": "新しい色",
    "Player 1": "プレイヤー色1",
    "Player 2": "プレイヤー色2",
    "Base Shade (= Original)": "基準の濃さ (= 元の色)",
    "Apply Replace": "置換を実行",
    "Color Replace: no pixels in range": "色置換: 範囲内のピクセルがありません",
    "Color Replace: {n} pixels updated": "色置換: {n} ピクセルを変更しました",

    # ---- dialogs / messages ----
    "New Canvas": "新規キャンバス",
    "Width:": "幅:",
    "Create": "作成",
    "Width/Height must be integers": "幅と高さは整数で入力してください",
    "Width/Height must be positive": "幅と高さは正の数で入力してください",
    "Unsaved Changes": "未保存の変更",
    "You have unsaved changes.\nWhat would you like to do?":
        "保存されていない変更があります。\nどうしますか?",
    "Don't Save": "保存しない",
    "Error": "エラー",
    "Valid paksize required": "正しい paksize を入力してください",
    "Colors/range must be 'R,G,B' or an integer, alpha 0-255":
        "色と範囲は「R,G,B」または整数、アルファは 0〜255 で入力してください",
    "Save layer {n}": "レイヤー {n} を保存",

    # ---- status bar ----
    "Tool": "ツール",
    "Zoom": "ズーム",
    "Offset": "オフセット",
    "Pos": "座標",
}


def translate(text, lang="ja"):
    """Return text translated into lang; unknown text (or lang "en")
    returns the English text unchanged."""
    if lang == "ja":
        return JP.get(text, text)
    return text
