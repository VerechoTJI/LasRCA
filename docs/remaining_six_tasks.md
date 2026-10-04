# LasRCA 後六項：實際目標、子任務與驗收

更新日期：2026-10-04。這份文件是本次工作的執行與驗收依據，不能把「工具完成」當作「實驗完成」。原始 `reproduction_staus_original.md` 與參考 PPTX 保持不動。

## 依據與本次實驗條件

- 原始需求：[reproduction_staus_original.md](E:/Misc/FastCodingWorkspace/AI/SMCI/reproduction_staus_original.md)，0C-06～0C-11。
- 參考簡報：[Phase0-C_Reproduction_20260929.pptx](C:/Users/tangj/AppData/Local/Temp/Phase0-C_Reproduction_20260929.pptx)。第2頁列六項需求；第14、17、23、26、29頁採「目標／要求／程式變更」，後續頁呈現結果。本文件沿用該結構，補上可執行子任務與驗收。
- 簡報第9～13頁協助區分 raw_data、analysis、dataset、LLM artifacts；第20～22、25頁提供論文比較表格的整理方式。簡報中的數字與模型結果屬於當時實驗，不直接當成本次成果或論文原文證據。
- 沿用公開程式提供的 **100 cases／subgraphs**，不重做選樣、不增加另一條選樣對照。本次標註輸入不是簡報第30頁所列的682次 entity occurrences；實際數量以目前選樣檔內容為準。
- 使用 **GPT-6 Luna + OAuth** 取代原 GPT-4。保留原四階段 prompts、階段順序及故障類型對照；結果稱為「Luna 補標實驗」，不聲稱與 GPT-4 回答相同。
- 網路與 Windows DPAPI 已恢復授權。DPAPI 用於保護本機 OAuth tokens，與資料處理、模型演算法無關。
- 標準差 fallback 已移除；保留目前設定的 percentile clipping，且零 IQR 使用原始數值座標。五個 seeds 的正式比較要採一致設定，不能直接混用舊 fallback checkpoints。
- 每個獨立完成的程式／文件任務驗證後 commit；長時間實驗保留獨立 run artifacts。作者 released 產物、原始 archives、synced sources 與原始進度文件不覆寫。

## 與論文方法的關係

以下標示用於區分「執行公開流程」與「本次為了執行、驗證或保存證據而增加的工作」。共同出現在同一子任務時，不能把新增工具歸為論文方法。

| 標示 | 意義 | 本次例子 |
|---|---|---|
| **執行支援：與論文方法無關** | 本次新增的執行、紀錄或維護功能，不列為論文方法或演算法重現成果 | request快取／續跑、run目錄、status／logs、SHA-256、環境紀錄、token與成本統計、隔離輸出／cache、commit |
| **重現驗證：非論文演算法** | 用來判定重現是否成立、解釋差異的檢查或分析；不代表作者提出此驗收程序 | 單元測試、finite檢查、schema／shape、資料差異、GT錯標分析、mean±std彙整、論文對照、待驗證清單 |
| **相容性修正：非論文方法** | 為讓公開程式在本機或完整流程中可執行所做的工程修正 | Windows路徑、UTF-8、缺少Istio產生呼叫、prompt讀寫路徑修正 |
| **實驗設定差異：非原論文條件** | 會改變輸入或模型，不能只稱執行支援，也不能歸入原論文方法 | GPT-6 Luna取代GPT-4、本機額外percentile clipping、至少一組自訓encoder的部分替換範圍 |
| **公開流程＋本次支援／驗證** | 執行作者公開的處理或訓練流程，同時加入本次工具或驗收 | 四階段LLM、y／mask更新、五seed訓練、raw處理、TS2Vec／下游執行；流程與新增支援各自區分 |

OAuth與DPAPI是本次新增的登入／憑證保護方式，**與論文方法無關**；Luna模型替換則另屬實驗條件差異。percentile clipping是會改變模型輸入的本機處理差異，不能被歸為只加紀錄。標準差fallback已移除，不作為後續工作項目。

本文件所有「驗收条件／完成證據／待驗證方法／失敗處理」都是本次重現管理與驗證要求，**不是論文演算法的新增步驟**。其中引用的指標與公開流程仍須按原程式及論文原文核對；保存或檢查它們的工具不列為論文方法。

## 「Luna 全量標註」的意思

「全量」的分母是選樣檔中的100個故障案例／子圖，並非整個 CCF AIOps 原始資料集。每個子圖含多個 resource entities；同一 entity 可以在不同故障案例中出現，所以「100案例」、「entity occurrences」、「API請求數」、「新增標籤數」是不同單位。

為了把案例中的觀測異常轉成分類器可使用的故障類型，流程依序執行：

| 階段 | 實際處理 | 產出及用途 |
|---|---|---|
| first | 對所選 node／pod，依CPU、disk、memory等觀測類別分開分析；類別依原 ent_files 設定 | 多份文字判斷，供下一階段整合；service不在此階段單獨呼叫 |
| second | 合併同一 node／pod 的各類判斷 | entity 層級分析文字 |
| third | 合併 entity 分析、子圖 entities 與關係 | 案例／子圖層級故障判斷及理由；可涵蓋 service |
| summarization | 要求將第三階段回答整理成指定 entity→exact_fault_type 格式 | 經解析與類別驗證後，才可更新 y／y_mask |

第三階段的分析文字是 explanation 的主要證據，須保留與最終標籤的對應。若原流程未提供獨立結構化 explanation 欄位，不宣稱已有該欄位。API一次成功也不代表 JSON 或標籤有效；四階段完成後仍需驗證。

## 共用驗收與依賴

| 共用子任務 | 必要性／行動 | 完成證據 |
|---|---|---|
| P-01 固定輸入 | **【執行支援：與論文方法無關】** 為避免續跑混入不同選樣、dataset或prompt，記錄實際路徑、SHA-256、source commit及設定 | run manifest；續跑時檢查 model／selection，prompt hash關聯請求 |
| P-02 固定正式比較條件 | **【重現驗證：非論文演算法】** k=0與k=1使用相同原始特徵、train／valid／test索引、GT、seed與前處理；只有新增LLM labels的訓練資訊不同 | 實際prepared dataset、split、preprocessing及checkpoint的可核對來源 |
| P-03 分開訓練與評估資料 | **【重現驗證：非論文演算法】** GT用於分析與評估；不得被新增到LLM prompts或用來自動修正LLM labels | prompt來源檢查；label update差異；test與valid未變 |
| P-04 保存可恢復結果（與論文方法無關） | **【執行支援：與論文方法無關】** 本次新增的實驗執行輔助功能：成功請求續用，失敗保留狀態；不把中斷回答寫成標籤 | request cache、stage logs、status；恢復不重付已成功請求；不列為論文方法或重現成果 |
| P-05 區分程式與實驗 | **【重現驗證：非論文演算法】** 依「未開始／工具完成／部分執行／實驗完成」記錄；只有產出齊全才驗收 | 本文件的任務狀態與實際run目錄一致 |

依賴順序：06→07→08；09從06同步收集、用07更新結果補齊影響分析。10可獨立進行；11使用released processed dataset時不必等待10，使用raw重建資料時才依賴10。本次至少完成一組encoder採前者。

## 0C-06 Labeling Method Verification

### 目標與必要性

確認公開選樣的100個案例能經四階段Luna流程產生可追溯的故障標籤，並量化執行失敗與格式問題。為了讓07安全更新dataset，不能只保存最後一段回答或把API成功等同有效標籤。

### 子任務與要求

| ID | 工作 | 驗收條件 |
|---|---|---|
| 06-A | **【重現驗證：非論文演算法】** 檢查選樣、第一階段prompt與entity對應；核對所有預期prompt檔 | 100個sample_index可定位；所需node／pod觀測檔存在；不重選案例 |
| 06-B | **【本次OAuth／相容性修正＋公開流程驗證；非論文方法】** 驗證OAuth、四階段單例與UTF-8讀寫 | Luna實際回傳成功；四階段串接；同一prompt路徑可讀；原始文字未因編碼損壞 |
| 06-C | **【公開流程＋本次支援／驗證】** 續跑全部100案例，保存每階段prompt／response及成功請求 | 100個案例均有明確狀態；未完成、失敗与完成分開；認證／額度失敗不連續轟炸請求 |
| 06-D | **【重現驗證：非論文演算法】** 解析摘要並核對entity keys與exact_fault_type | 缺漏、額外entity、非字串／list、未知類別、JSON失敗逐項計數；有效標籤有case／entity locator |
| 06-E | **【執行支援：與論文方法無關】** 彙整request／returned model、usage、duration與成本資訊 | 分別列case完成率、可解析率、有效entity標籤比例；統計實際成功請求usage，不把cache hits算新請求；費率／計費資訊不可得時明列不可得，不能填0 |

### 程式、產出與現況

入口：`code/llm/run_labeling.py`、四個stage scripts、`luna_oauth.py`。產出：`runs/lasrca/luna_20261004/{manifest.json,status.json,requests,prompts,responses}`，後續補解析与用量報告。

工具及單例驗證已完成；本文件讀取狀態時完成6／100案例（0、5、6、7、8、12），仍在續跑。這是動態快照；正式完成數以status檔為準。全量完成的驗收要求是100案例執行狀態與全部格式／類別問題可核對，不要求模型判斷必然正確。

## 0C-07 Classifier Retraining

### 目標與必要性

將06通過驗證的LLM labels加入獨立訓練dataset，確認哪些entity新增了可用監督資訊，再用seeds405–409完成k=1訓練。`y`代表故障類別；`y_mask`代表該entity標籤是否可供訓練使用，兩者必須一起檢查。

### 子任務與要求

| ID | 工作 | 驗收條件 |
|---|---|---|
| 07-A | **【公開流程＋本次支援／驗證】** 凍結更新前prepared dataset與100cases回答；將LLM故障名稱映射到數值類別 | mapping／已知名稱別名明確；No fault有明確值；未知或非法值不冒充正常 |
| 07-B | **【公開流程＋本次支援／驗證】** 只更新選中unlabeled case/entity的y／y_mask，另存k1_luna.pkl | 原檔不覆寫；漏標／無效標籤保留原值与mask；不新增random-labeling副作用 |
| 07-C | **【重現驗證：非論文演算法】** 驗證dataset差異與統計 | features、topology、train／valid／test索引及valid／test labels不變；列更新前後y／mask、新增mask數、覆寫數、忽略原因、故障類別分布 |
| 07-D | **【公開流程＋本次支援／驗證】** 以seed405跑完整設定的單seed，檢查實際讀取獨立dataset | loss、gradient、parameter與prediction finite；500epochs完成；實際prepared dataset hash可核對，不能只記上游raw hash |
| 07-E | **【公開流程＋本次支援／驗證】** 相同設定完成405–409，保存五組模型與訓練證據 | 各seed都有checkpoint／SHA-256、完整loss與duration／exit status；不得用released模型替代失敗訓練；已完成405可直接算入五組 |

### 程式、產出與現況

入口：`llm/build_labeled_dataset.py`及`tasks/las_rca.py --prepared_dataset_path`。产出：`dataset/k1_luna.pkl`、`label_changes.json`、dataset summary、五seed獨立training runs與checkpoints。

更新工具與隔離输入已完成；正式更新與五seed訓練等待06。依公開程式的補標後訓練流程執行，不另設權重載入要求。正式dataset只能由完整100cases結果建立；partial模式僅作隔離診斷。

## 0C-08 Retrained Classifier Evaluation Comparison

### 目標與必要性

在一致測試條件下量化補標前後的分類器效果差異。定位回答「哪個entity是根因」，分類回答「該entity是哪種故障」；兩者需要各自指標。不能把模型替換或前處理變化造成的差異全部歸因於新增labels。

### 子任務與要求

| ID | 工作 | 驗收條件 |
|---|---|---|
| 08-A | **【本次設定修正後的基準驗證；非論文新增方法】** 重跑不含std fallback的k=0五seed基準 | 同07的features、split、seed與clipping設定；舊fallback結果僅保存為歷史 |
| 08-B | **【重現驗證：非論文演算法】** 評估同seed的k=0與Luna k=1，保存逐案例結果 | 兩組checkpoint與prepared dataset來源明確；同一test案例／entity與GT；有實際ranking／prediction可抽查 |
| 08-C | **【重現驗證：非論文演算法】** 分service／pod／node計算localization及classification | AC@1／3／5及Avg@5；Avg@5核對AC@1～5平均；Micro／Macro Precision、Recall、F1的類別與No fault處理沿用既有定義 |
| 08-D | **【重現驗證：非論文演算法】** 統計逐seed及五seed彙整 | 成對seed齊全；mean與母體std明確；ratio或percent单位一致；絕對差用百分點，相對差為(k1−k0)/k0，基準0標N/A |
| 08-E | **【重現驗證：非論文演算法】** 對照論文／released參考結果並解釋差異 | 明列Luna取代GPT-4、clipping與實驗條件差異；論文值需核對原文Table／row，不只抄簡報；改善、下降、無明顯差異均可為有效結果 |

### 程式、產出與現況

入口：既有evaluation輸出與`experiments/retraining_comparison.py`。產出：逐seed metrics、paired comparison JSON／Markdown、五seed彙整与論文對照表。

成對比較工具已完成，正式結果未完成。待驗證实际prepared dataset、split及preprocessing的hash是否進入評估證據；只有上游dataset與GT hash相同不足以保證比較條件一致。

## 0C-09 Labeling Errors Summarization

### 目標與必要性

分開分析執行／格式問題與模型判斷錯誤，並追蹤其對label update的實際影響。GT只用于分析，不回灌prompt或自動修正本次LLM labels；否則08測得的不再是Luna直接補標的效果。

### 子任務與要求

| ID | 工作 | 驗收條件 |
|---|---|---|
| 09-A | **【重現驗證：非論文演算法】** 逐case/entity對照GT與最終標籤，同步讀06格式與執行狀態 | 區分API／路徑失敗、不可解析、缺標、未知類別、多值標籤、錯entity、誤報與漏報；執行失敗不算成故障類別誤判 |
| 09-B | **【重現驗證：非論文演算法】** 整理10～20個實際錯誤或格式異常案例 | case、entity、時間／日期locator、GT來源／值、LLM值、原始回答、stage paths及錯誤類型齊全；同一case多entity明確標示，不能冒充多個獨立case |
| 09-C | **【重現驗證：非論文演算法】** 關聯07的實際y／mask差異 | 區分錯標被採用、格式異常被忽略、原mask保留；目前partial分析只可稱模擬影響，正式更新後換成實際diff |
| 09-D | **【重現驗證：非論文演算法】** 統計與因果說明 | 分母分別列案例數與可評估entity occurrences；格式／缺標與判斷錯誤分開；歸因某stage時有對應回答證據，無證據只列假設 |

### 程式、產出與現況

入口：`llm/audit_labels.py`。产出：audit summary、errors JSON與可讀報告，連回原response和label_changes。

工具與前2cases的分析已完成：15entities中1個與GT不同。該結果不能外推全100cases；新增已完成案例尚需重跑audit。若全量實際錯誤不足10個，報告全部、實際數與不足原因，不造例。API失败如無entity label不混入有效標籤誤判率。

## 0C-10 Dataset Preprocessing（Stretch）

### 目標與必要性

從作者提供的raw archives建立可重新執行的前處理流程，保留每步數量／schema／耗時与失敗證據，再與released temp_data對齊比較。目標是確認資料如何形成模型輸入；只生成一個pkl或讓程式exit0不代表與released一致。

### 子任務與要求

| ID | 工作 | 驗收條件 |
|---|---|---|
| 10-A | **【重現驗證：非論文演算法】** 盤點normal.tar、faults.zip、test_data.7z与GT、日期／cloudbed範圍 | 來源与檔案hash、解壓manifest、預期檔案清單、磁碟容量；原始archive不改寫；抽樣與全量范围分開 |
| 10-B | **【相容性修正：非論文方法】** 修復公開入口的產生／讀取依賴 | node／container／service／istio產出完整；原公開入口漏istio的證據保存；修改使用既有process函式，不造資料 |
| 10-C | **【公開流程＋本次支援／驗證】** 完成抽樣Metric流程并核對標準化 | 每類schema、timestamp、entity、NaN/Inf與數量；只處理istio的腳本狀態與released数值核對；未處理／零std／全NaN分支不能沿用上一特徵結果 |
| 10-D | **【公開流程＋本次支援／驗證】** 完成Trace、Log、topology与time-window抽樣流程 | Trace依同時間粒度聚合並核對統計；Log parsing／template／TF-IDF來源和fit範圍明確；topology edge端點有效；GT日期與時區正確 |
| 10-E | **【重現驗證：非論文演算法】** 組裝抽樣final dataset並同locator對照released | modalities与特徵順序、shape、labels、topology、實際数值差異；抽樣fit的統計與全量不同不能直接宣稱演算法錯誤 |
| 10-F | **【公開流程＋本次支援／驗證】** 在抽樣驗證後擴展normal／train_valid／test全部範圍 | 各stage輸入輸出数量／schema／duration／exit status／失敗清單；日期与cloudbed完整；test不混入不該fit的統計；缺檔有明確處置 |
| 10-G | **【重現驗證：非論文演算法】** 彙整final temp_data manifest及抽樣數值比較 | 所有產物路径／大小／hash，資料coverage與缺值摘要；一致、不同、未比對分開列；差異原因可追溯至stage或列待驗證 |

### 程式、產出與現況

入口：`experiments/raw_pipeline.py`与`data_filter/CCF_AIOps_challenge_2022/{dao,service}`。产出獨立`runs/lasrca/raw_20261004`，包含inputs、generated、config、pipeline_status、各stage logs及artifact manifest；全量擴展另存，避免抽樣／全量cache混用。

目前使用2022-03-19 cloudbed-1 normal与2022-03-20 cloudbed-1 fault，尚無test。topology／entity edges／time windows成功，raw Metric曾成功但漏istio，下游缺檔失敗。已補istio并保存修正前status/log，正重新執行，尚未宣稱抽樣完整。

**公開腳本與released差異：**raw資料與released同名Istio中間CSV均存在；generate入口漏呼叫，load入口卻要求讀取。標準化階段的四類清單被註解，當前只啟用istio。作者可能分批改腳本處理、之後使用已保存temp_data；這是有跡象支持的推測，沒有執行紀錄可確認。修正前後結果需對照released，不能把推測当作既定事实。

## 0C-11 TS2Vec embedding Training（Stretch）

### 目標與必要性

至少自訓一組observation encoder，確認它能產生可供下游使用的embedding，再比較自訓／released embedding與下游效果。embedding的座標可因隨機訓練改變，MAE不直接代表模型品質；需要相同下游條件的評估。

### 子任務與要求

| ID | 工作 | 驗收條件 |
|---|---|---|
| 11-A | **【公開流程＋本次支援／驗證】** 固定entity／模態组合与training输入 | 本次service、原loader的Metric+Trace+Log資料路線、seed405；實際input維度與組合由loader／metadata核對；train仅normal与train_valid，不fit test |
| 11-B | **【公開流程＋本次支援／驗證】** 完成至少一組600epochs，保存模型與loss | 原TS2Vec算法；input_dims8、output_dims320、batch32、lr0.001、max_train_length3000；完整loss／duration／checkpoint hash与finite檢查 |
| 11-C | **【公開流程＋本次支援／驗證】** 相同source encoding設定產生全部所需embeddings | causal、sliding_length、padding与released encoding來源核對；所有split/date/entity的timestamps、shape與feature順序可對齊；資料coverage完整 |
| 11-D | **【公開流程＋本次支援／驗證】** 比較embedding且建立隔離下游dataset | 對齊后報finite、shape、差異摘要；只替換service encoder時，其他entity embeddings沿用released并明列部分替換；cache不能重用舊embedding製成的dataset |
| 11-E | **【公開流程＋本次支援／驗證】** paired released／self-trained下游訓練与評估 | 同split、labels、seed、epochs、optimizer等；至少一seed作可驗收的下游對照，若報mean±std則需完整指定seed集合；保存各checkpoint与embedding／dataset hash |
| 11-F | **【重現驗證：非論文演算法】** 核對下游指標範圍與報告 | 現有fine-tuning入口主要提供故障類型分類；若需求包含localization，需實作／驗證合理ranking與相同GT評估。沒有定位結果時不得把classification-only寫成完整RCA比較 |

### 程式、產出與現況

入口：`experiments/ts2vec_run.py`、`pretrain` loader／encoding、`tasks/fine_tuning_fault_type_classification.py`；後兩步仍需補隔離cache與配對執行。

`runs/lasrca/ts2vec_20261004`已完成600epochs，耗時約3162秒，保存loss、設定、progress与checkpoint。單一test adservice序列為1440×320、finite，与released MAE約0.2264；這只驗證一段序列，11-C～F未完成。TS2Vec屬pretrain+fine-tuning路線，與07的LasRCA端到端classifier訓練分開。

## 待驗證項目：證據、必要性與未通過時的處理

| ID | 待驗證項目 | 為何必要／驗證方式 | 影響與未通過處理 |
|---|---|---|---|
| V-01 | **【重現驗證：非論文演算法】** 100cases所需第一階段prompt齊全且與選樣對應 | 對sample/entity檢查檔案與原內容來源 | 缺檔先補生成步驟，不能算完成或換案例 |
| V-02 | **【重現驗證：非論文演算法】** prompts未新增GT或使用評估標籤修正回答 | 查生成來源與template內容；保留原prompt語義 | 有新增洩漏則修正並隔離重跑受影響案例 |
| V-03 | **【重現驗證：非論文演算法】** 完成stage的回答是否可解析、entity及故障名稱合法 | 全部summaries驗證，另算有效標籤比例 | 格式問題保留原mask，記錄影響；不得靜默填No fault |
| V-04 | **【重現驗證：非論文演算法】** usage／returned model／成本可追溯 | 核對completed request metadata、重用與新請求 | 缺usage或費率明列缺失，不能宣稱精確成本 |
| V-05 | **【重現驗證：非論文演算法】** prepared dataset／split與實際模型讀取一致 | hash實際cache与索引，抽查run輸入 | 正式07／08暫停，修正入口與provenance |
| V-06 | **【重現驗證：非論文演算法】** 更新是否僅限所選unlabeled y／mask | 全dataset差異，features／topology／valid／test不變 | 不符合則拒絕正式訓練，修復更新範圍 |
| V-07 | **【重現驗證：非論文演算法】** clipping-only能否完成五seed訓練 | 移除std fallback後完整單seed再五seed，檢查finite | 保留失敗證據與診斷；不自行恢復已移除fallback |
| V-08 | **【重現驗證：非論文演算法】** k=0／k=1可公平成對比較 | 相同features、split、GT、seed與前處理，labels差異明确 | 条件不同先重跑相應基準，不直接比較歷史結果 |
| V-09 | **【重現驗證：非論文演算法】** AC@k／Avg@5與micro／macro定義對齊論文 | 核對code、逐案例計算與原文Table row | 定義不同分開報告；簡報表格只當整理參考 |
| V-10 | **【重現驗證：非論文演算法】** 實際錯誤案例數與stage歸因是否足夠 | 全量audit與原stage回答／實際label diff關聯 | 不足10例如實報告；因果證據不足不指定根因stage |
| V-11 | **【重現驗證：非論文演算法】** raw缺少的Istio中間檔能由原函式生成 | 修正入口後核對四類产物與讀取成功 | 若仍缺檔，按raw來源／config／函式分支診斷 |
| V-12 | **【重現驗證：非論文演算法】** 只標準化Istio是否对应released產出 | 同日期／entity／feature对照raw、統計與released | 不能直接推定四類同處理；確認後才補完整入口 |
| V-13 | **【重現驗證：非論文演算法】** 零std、全NaN、缺feature分支是否正確 | 針對邊界輸入檢查update_metric_data等變數 | 未賦值或沿用前特徵則修復並回歸測試 |
| V-14 | **【重現驗證：非論文演算法】** 抽樣fit與全量fit造成的差異 | 記錄统计／Log template的fit範圍与date coverage | 抽樣結果只驗證流程；全量後再判斷數值重現 |
| V-15 | **【重現驗證：非論文演算法】** Trace／Log／時區／topology在raw重建中完整 | 同locator核對time windows、entity索引與features | 不用released檔補空缺来冒充重建成功 |
| V-16 | **【重現驗證：非論文演算法】** test是否進入不應fit的統計或encoder训练 | 讀loader与各analysis stage範圍并記錄 | 源程式若如此需如實聲明與分開處理，不靜默稱無洩漏 |
| V-17 | **【重現驗證：非論文演算法】** TS2Vec全序列encoding與released可對齊 | 逐split/date/entity確認shape、timestamps与設定 | 單序列通過不足；缺coverage先補encoding |
| V-18 | **【重現驗證：非論文演算法】** embedding替換是否被舊fine-tuning cache忽略 | 隔離兩路cache，核對實際讀取embedding hash | 修正dataset routing並重新建立cache |
| V-19 | **【重現驗證：非論文演算法】** 下游能提供哪些RCA指標 | 查fine-tuning输出与ranking／GT，分類與定位分列 | 缺定位時補可驗證評估，或如實標明未完成 |
| V-20 | **【重現驗證：非論文演算法】** 模型差異如何限制論文比較 | 明列Luna／GPT-4、前處理与raw重建差異 | 不把本次數值視為GPT-4原條件的精確重現 |

## 完成時應交付的六份結果

1. 06：100cases的stage證據、有效標籤／失敗統計、model与usage／成本資訊。
2. 07：独立更新後dataset、完整y／mask差異與五seed訓練產物。
3. 08：一致設定k=0／k=1的逐seed和彙整比較、論文條件差異說明。
4. 09：真實錯誤案例、分類統計与實際dataset update影響，數量不足如實說明。
5. 10：全量raw前處理产物、每step統計与manifest、對齊released的差異報告。
6. 11：自訓encoder、全序列embedding与隔離下游paired結果，明列替換与指標範圍。

因此「全部完成」需要六項的實驗證據齊全；網路恢復與單一缺檔修正只讓工作可以繼續，不等於提前保證上述所有驗證通過。
