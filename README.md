# pyswitchcontroller

Arduino と FT232RL を使って Switch を Python から操作するライブラリ

## 必要なもの

1. Arduino Leonardo もしくは互換品
2. USBシリアル変換モジュール (FT232RL 等)
3. 上を接続する物
   
## セットアップ(Windows)

1. Arduino に arduino/ft232.ino を書き込む
2. FT232RLにドライバをインストール
   1. [zadig](https://zadig.akeo.ie/)をダウンロード
   2. Options -> List All Devices をクリック
   3. `libusb-win32` を選択して Reinstall Driver
3. 全部つなぐ
![](connect_image.jpg)
