# Social Radar — MVP 1.0

台灣熱門搜尋與話題觀測工具。React、Vite、TypeScript、Tailwind CSS；Python 官方 RSS Collector；GitHub Actions + Pages。

## 使用

- 今日熱門：最近 24 小時被本工具觀測到的搜尋詞。
- 本週趨勢：最近 7 天的觀測與實際快照次數；新站不推算不存在的歷史。
- 話題詳情：原始來源、RSS 發布時間、觀測時間、相關新聞標題與連結。
- 收藏：話題收藏、私人筆記、手動 Threads／Instagram 連結、JSON 備份匯入／匯出。
- 分析提示詞：複製後自行貼到 ChatGPT；瀏覽器禁止剪貼簿時可手動選取文字。
- 系統狀態：來源更新失敗、超過 12 小時警告、超過 24 小時過期提示。

收藏與備註僅儲存在目前瀏覽器的 `social-radar.personal.v1`，不會上傳 GitHub。與龜啤工作台的 IndexedDB 分開。清除瀏覽器資料、更換裝置或更換網址前，請匯出備份。

## 資料來源與真實性

正式來源：[Google Trends 台灣 RSS](https://trends.google.com/trending/rss?geo=TW)。[Google 官方匯出說明](https://support.google.com/trends/answer/3076011)。開發時已實際讀取 XML，並以真實資料建立初始快照。

RSS 實際提供 `title`、`ht:approx_traffic`、`pubDate`、`link`，部分項目附有 `ht:news_item` 標題與 URL。沒有相關搜尋詞、完整活躍狀態或可靠熱門排名，缺少欄位保持 null／unknown。

- `source_published_at` 是 RSS pubDate，不宣稱是趨勢開始時間。
- `first_seen_at` 是本工具首次觀測搜尋詞的時間，不是事件發生時間。
- 話題 ID 是來源、地區與正規化搜尋詞的穩定雜湊：同名搜尋詞可能涵蓋不同事件，並非事件識別碼。
- `snapshot_count` 是目前索引累積觀測數；本週畫面另依近 7 天歷史快照計數。
- 當次沒收錄不代表已停止熱門。排名、成長率及社群互動數不推測。
- 新聞只保留 RSS 提供的標題及連結；不擷取全文、圖片或影片。
- 沒有足夠分類依據的話題保留「其他」，目前不猜測事件類別。
- 六小時觀測間隔可能漏掉短暫趨勢，不能宣稱完整的全台社群排行榜。

Threads：`ENABLE_THREADS=false`。Collector 明確停用；即使改成 true，未驗證授權仍不會擷取。未來需完成 Meta App、OAuth、threads_keyword_search 與資料保留政策驗證。不要把 Access Token 寫入任何前端或資料檔案。

Instagram：第一版只支援公開貼文連結手動收藏，不蒐集全站熱門資料。

## 零必要固定費用

使用 GitHub Free、公開 Repository、標準 Ubuntu Actions 執行環境、GitHub Pages 預設網域。無付費資料庫、API、AI、自訂網域或代理服務；不需要信用卡。禁止選用付費大型 runner 或擴大付費快取。Pages 部署暫存保留 1 天。

GitHub 與來源服務的免費條件可能變更；不足時停用或降級，不自動購買服務。GitHub Pages 使用限制不適合電子商務或付費 SaaS，這個專案是公開資料觀測工具。

## GitHub 部署

1. 建立公開 `usermatty1992/social-radar` Repository，預設分支 main。
2. 上傳這個專案的原始碼、package-lock.json、data 與 `.github/workflows/update-and-deploy.yml`。不要上傳 node_modules、私人收藏、啤酒草稿或照片。
3. Repository → Settings → Pages → Source 選 **GitHub Actions**。
4. Actions → Update trends and deploy Pages → Run workflow。
5. 完成後開啟 `https://usermatty1992.github.io/social-radar/`。實際網址以 deployment 結果為準。

工作流程在同一個排程 run 內完成：擷取、驗證、提交公共 JSON、測試、建置及部署。不依賴 GITHUB_TOKEN 的資料 commit 再次觸發 push。排程 UTC `17 3,9,15,21 * * *` 對應台灣時間每日 05:17、11:17、17:17、23:17。

全流程以 concurrency 避免同一 workflow 寫入競爭。main 若設為受保護分支，需要另行安排資料寫入權限；不要以強制推送繞過保護。

## 開發與驗證

需求：Node.js 24、Python 3.11+。Python 使用標準庫，沒有額外 pip 套件。

```bash
npm ci
python scripts/update_data.py
python scripts/validate_data.py
python -m unittest discover -s tests -p 'test_*.py'
npm test
npm run build
npm run dev
```

開發預覽與正式網站均讀取 `public/data`，`npm run build` 會先將資料複製進 public。第一次開發前先建置，或執行 `node scripts/prepare-data.mjs`。

`npm run package:local` 在 build 後產生獨立 `Social-Radar.html`，內嵌真實資料快照，直接開啟不必啟動服務。這個離線檔案不會自動抓新資料，會顯示此限制與擷取時間。正式 Pages 版本則會讀取部署後的資料。

## 容錯與維護

- 網路錯誤、逾時、格式不符：Collector 回傳失敗、status 標記錯誤，latest/topics 保留最近有效資料。
- 正常空 RSS：視為成功但當次零筆；保留近 30 天索引與歷史。
- 格式驗證失敗：停止發布不相容資料。
- 一天內的多次快照保存在同一 daily JSON 的 snapshots 陣列，避免覆蓋前幾次觀測。
- 工作樹保留近 30 天歷史；Git commit 紀錄仍可能保留更舊內容。未來若接入有刪除義務的社群資料，不能直接沿用永久 commit 方案。
- 公開 Repository 60 天無活動可能自動停用 schedule；到 Actions 檢查並重新啟用。
- 排程可能延遲或漏跑；請看最近成功時間，必要時手動 Run workflow。
- 收藏匯入錯誤不覆蓋原資料；重複 ID 保留原備註。不信任匯入備份裡的額外統計欄位。
- 不在日志、JSON 或 bundle 寫入 token。未來登入授權僅限 Collector 的 Actions Secrets。

## 常見問題

**為什麼全部都是「其他」？** 現有 RSS 沒提供事件分類；尚未有可靠分類規則，寧可不猜。

**為什麼本週少於 7 天？** 新工具剛開始建立觀測資料，不回填虚構歷史。

**Threads 為什麼沒有資料？** 尚未授權接入。先用 Google 搜尋趨勢，Threads／Instagram 連結可手動收藏。

**手機收藏和電腦不一致？** MVP 無帳號、無跨裝置同步；請匯出 JSON，在另一裝置匯入。

**工作台「重新整理」會抓趨勢嗎？** 啤酒工作台的按鈕只重建圖卡與文案。雷達有自己的重新整理，讀取最新已部署的公共快照；不會從瀏覽器觸發雲端擷取。
