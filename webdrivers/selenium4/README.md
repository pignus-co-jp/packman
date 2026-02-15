# 必須 
## pip インストール
### Seleniumライブラリをインストール
!pip install selenium

# Google Colab 環境の場合
## apt インストール
### パッケージリストを更新
!apt-get update

### Chromiumブラウザとそのドライバをインストール
!apt install -y chromium-chromedriver

### 必須ライブラリ
!apt-get update -qq
!apt-get install -y -qq \
libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0 \
libnss3 libxss1 libasound2 libgbm1 \
fonts-liberation

### 日本語化ライブラリ
!apt-get install -y fonts-ipafont-gothic fonts-ipafont-mincho


## パス設定
### Chromedriverを適切な場所にコピー
!cp /usr/lib/chromium-browser/chromedriver /usr/bin

