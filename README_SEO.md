# XPeach SEO・検索エンジン登録手順

XPeachの正規URLは `https://www.xpeach.tv/` です。`https://xpeach.tv/` はWorkerで、パスとクエリを維持したまま301転送します。

## 実装済みのSEO基盤

- `public/robots.txt`: 公開ページを許可し、`/admin`、`/api/admin`、通報完了画面を除外
- `public/sitemap.xml`: 公開中・未削除・未通報の動画、公開カテゴリ、投稿者、固定ページだけを掲載
- 公開ページ: title、description、www正規URLのcanonical、Open Graph、Twitter Card
- 動画詳細: 実データだけを使った`VideoObject` JSON-LD
- 管理系URL: meta robotsと`X-Robots-Tag`の両方でnoindex
- `wrangler.jsonc`: `404-page`により存在しないURLをHTTP 404で返す
- 静的アセット: 長期ブラウザキャッシュ。HTMLはCloudflare標準の再検証動作を維持

サイトマップは現在1ファイルです。50,000 URLに近づいたら、動画を複数のsitemapへ分割し、`sitemapindex`から参照する構造へ変更してください。

## Google Search Consoleへ登録する

1. [Google Search Console](https://search.google.com/search-console/)を開き、Googleアカウントでログインします。
2. 「プロパティを追加」を選びます。画面名は変更される場合があります。
3. 通常は「ドメイン」を選び、`xpeach.tv`を入力します。これはwww、非www、http、httpsをまとめて確認できます。
4. Googleから表示されたTXT値をコピーします。
5. Cloudflare Dashboardでxpeach.tvのゾーンを開き、「DNS」からTXTレコードを追加します。
   - Type: `TXT`
   - Name: `@`（画面によっては`xpeach.tv`）
   - Content: Googleが表示した値
6. DNS保存後、Search Consoleへ戻って「確認」を実行します。反映に時間がかかる場合は、TXTを消さず後で再確認します。

### ドメインとURLプレフィックスの違い

- **ドメインプロパティ**: `xpeach.tv`配下をまとめて管理します。DNS TXT認証が必要で、推奨です。
- **URLプレフィックス**: `https://www.xpeach.tv/`だけを管理します。HTMLファイルやmetaタグでも認証できますが、別ホスト・別プロトコルは別管理です。

URLプレフィックスのHTMLファイル認証を使う場合は、Googleから取得した確認ファイルを名前・内容を変えずに`public/`直下へ置き、mainへpushします。秘密鍵ではありませんが、Googleが指定したファイルだけを置いてください。

## sitemap.xmlを送信する

1. Search Consoleで対象プロパティを開きます。
2. 「サイトマップ」を開きます。
3. `https://www.xpeach.tv/sitemap.xml`（入力欄がドメイン固定なら`sitemap.xml`）を送信します。
4. 「成功しました」等の状態になることを確認します。検出URL数の反映には時間がかかります。

## URL検査とインデックス登録

1. Search Console上部のURL検査へ、`https://www.xpeach.tv/`または公開動画URLを入力します。
2. 公開URLのテストを行い、取得可能でcanonicalがwwwになっていることを確認します。
3. 必要な代表ページのみ「インデックス登録をリクエスト」します。全動画を連続送信する必要はありません。
4. 「ページのインデックス登録」レポートで、登録済み・除外・クロール済み未登録などの理由を確認します。

成人向けの可能性があるサイトでは、SafeSearch等により表示範囲が制限されることがあります。隠しテキスト、キーワード詰め込み、クローキングは行わず、ページ内容と一致する情報だけを掲載します。

## Bing Webmaster Tools

1. [Bing Webmaster Tools](https://www.bing.com/webmasters/)へログインします。
2. Search Consoleからインポートするか、`https://www.xpeach.tv/`を手動追加します。
3. 手動追加時は、案内されたDNS TXTまたは確認ファイルで所有権を確認します。
4. Sitemapsから`https://www.xpeach.tv/sitemap.xml`を送信します。

## 公開後の確認URL

- `https://www.xpeach.tv/robots.txt`
- `https://www.xpeach.tv/sitemap.xml`
- `https://www.xpeach.tv/`
- `https://xpeach.tv/test?source=seo`（www側へ301され、パスとクエリが維持されること）
- 存在しないURL（HTTP 404になること）

公開カタログはDBのスナップショットを書き出す方式です。動画の公開状態を変更した場合は、`tools/export_snapshot.py`で再生成してからpushしてください。公開ページの閲覧ではX API・AI APIを呼びません。
