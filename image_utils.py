import base64
from io import BytesIO
from PIL import Image

def process_image(file, max_size=1024):
    """
    画像をリサイズし、base64文字列に変換する関数

    Parameters:
    - file: アップロードされたファイル
    - max_size: 画像の最大サイズ（幅または高さの最大値）

    Returns:
    - 画像のbase64エンコード文字列
    """
    try:
        img = Image.open(file)
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size))
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        raise Exception(f"画像処理中にエラーが発生しました: {str(e)}")
