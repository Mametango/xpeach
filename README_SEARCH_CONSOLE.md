# Google Search Console 登録手順

XPeach は正規URLを `https://www.xpeach.tv` に統一しています。Google Search Console では、Cloudflare DNSを管理しているため「ドメインプロパティ」＋DNS TXT認証を推奨します。

## 1. Search Consoleでプロパティを追加

1. [Google Search Console](https://search.google.com/search-console) を開き、Googleアカウントでログインします。
2. 「プロパティを追加」を選びます。
3. プロパティタイプで「ドメイン」を選び、`xpeach.tv` と入力します（`https://`やパスは付けません）。
4. 表示されたTXTレコードの値をコピーします。

## 2. Cloudflare DNSで所有権を確認

1. Cloudflareの対象アカウントで `xpeach.tv` のサイトを開きます。
2. 「DNS」→「Records（レコード）」→「Add record（レコードを追加）」を開きます。
3. Typeは `TXT`、Nameは `@`（ルートドメイン）、ContentはSearch Consoleが発行した `google-site-verification=...` の値をそのまま入力します。
4. 保存し、Search Consoleへ戻って「確認」を押します。

DNS反映には数分〜最大で時間がかかる場合があります。確認後もTXTレコードは残して構いません。

「URLプレフィックス」方式は `https://www.xpeach.tv/` のようにURL単位で登録する方法です。DNSを編集できない場合にHTMLファイルまたはmetaタグで確認できますが、サブドメイン等をまとめて確認できるドメインプロパティの方が本番運用に適しています。

## 3. HTMLファイル方式（代替）

Search ConsoleでHTMLファイル方式を選び、発行されたファイル（例 `googleXXXXXXXXXXXXXXXX.html`）をリポジトリの `public/` 直下へ置いてmainへpushします。デプロイ後、次のURLで200になることを確認してからSearch Consoleで「確認」を押します。

`https://www.xpeach.tv/googleXXXXXXXXXXXXXXXX.html`

確認ファイルの名前と内容は変更しないでください。確認完了後もファイルを残してください。

## 4. metaタグ方式（ビルド時）

HTMLファイルを置けない場合は、エクスポート時に環境変数を設定します。確認コード自体はGitへコミットしません。

```powershell
$env:GOOGLE_SITE_VERIFICATION = "google-site-verification=XXXXXXXX"
docker compose exec -e GOOGLE_SITE_VERIFICATION="$env:GOOGLE_SITE_VERIFICATION" web python /app/tools/export_snapshot.py /tmp/xpeach-public
```

生成HTMLの`<head>`へ`google-site-verification` metaタグが入り、値は公開HTMLに表示されます。確認コードを設定しない場合はタグを出力しません。

## 5. sitemap.xmlを送信

1. Search Consoleの左メニューで「サイトマップ」を開きます。
2. 「新しいサイトマップを追加」に `sitemap.xml` と入力します（ドメイン全体を登録した場合）。
3. 「送信」を押し、ステータスが「成功しました」になることを確認します。

現在のサイトマップは、公開中の動画・カテゴリ・クリエイターと固定公開ページをDBから再生成し、`<loc>`をすべて `https://www.xpeach.tv/...`、`<lastmod>`を更新日にしています。管理画面や非公開・削除済み動画は含めません。生成処理は `tools/export_snapshot.py` に集約されているため、新しい動画を公開した後に同じエクスポートを実行すると更新できます。URLが50,000件を超える場合は、同処理をページ・動画ファイルへ分割してsitemap indexへ拡張できます。

## 6. URL検査とインデックス登録

1. Search Console上部のURL検査へ公開URL（例 `https://www.xpeach.tv/video/75/`）を入力します。
2. クロール済み情報を確認し、必要な場合だけ「インデックス登録をリクエスト」を押します。
3. 「ページがインデックスに登録されましたか？」や「ページのインデックス登録」を定期的に確認します。

年齢確認、非公開、削除済み、管理画面は検索対象外です。登録直後の反映には時間がかかることがあります。

## 7. Bing

Bing Webmaster Toolsでもサイトを追加し、同じ `https://www.xpeach.tv/sitemap.xml` を送信できます。Cloudflare DNSのTXT認証を使う場合は、Bingが表示するレコード名・値をCloudflare DNSへ追加してください。

## 8. 動作確認

以下が200であることを確認します。

- `https://www.xpeach.tv/robots.txt`
- `https://www.xpeach.tv/sitemap.xml`
- 所有権確認HTMLを置いた場合の `https://www.xpeach.tv/googleXXXXXXXX.html`

`robots.txt` は `/admin` と管理APIをクロール禁止にし、sitemap URLを明記しています。
