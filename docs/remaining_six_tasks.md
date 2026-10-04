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
| 08-C | **【重現驗證：非論文演算法】** 分service／pod／node計算localization及classification | 原始需求為AC@1／3／5與Micro／Macro Precision、Recall、F1；額外保存AC@2／4與Avg@5作輔助檢查，不能列為原始08新增要求。類別與No fault處理沿用既有定義 |
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
| 11-A | **【公開流程＋本次支援／驗證】** 固定entity／模態组合与training输入 | 本次service、seed405；來源檔名為metric_trace_log，但service實際輸入只有8個Metric特徵，不能因檔名宣稱此encoder使用三模態。train僅normal與train_valid，不fit test |
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

## 原始文件「保存／記錄／回報」要求逐項對照

以下逐句對照2026-10-04重新讀取的原始0C-06～11。**本節是本次重現證據保存要求，與論文演算法無關。** 原需求已指定要保存或回報的內容不取消；欄位與檔名是本次具體化的實作約定。已有檔名按現有程式核對；標「待產生／待補工具」的檔案不能被當成已存在。

### 路徑與狀態讀法

以下路徑相對於 `E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA`：

- `L`＝`runs/lasrca/luna_20261004`，100cases標註與label update。
- `K1(s)`＝`runs/lasrca/retraining_luna/seed_<s>`，s為405～409；正式run尚未生成，啟動時可加timestamp，但manifest須記實際絕對路徑。
- `K0(s)`＝`runs/lasrca/baseline_no_std/seed_<s>`，移除fallback後的配對基準；正式run尚未生成。
- `C`＝`runs/lasrca/comparison_luna`，配對評估與論文比較；尚未生成。
- `R`＝`runs/lasrca/raw_20261004`，目前raw抽樣；全量另用獨立run並在manifest記錄，不能沿用抽樣統計當全量。
- `T`＝`runs/lasrca/ts2vec_20261004`，已完成encoder訓練。
- `D`＝`runs/lasrca/ts2vec_downstream`，embedding全量與下游配對；尚未生成。

「部分已有」只表示目前完成部分有檔案；「工具已有／待正式執行」不等於有完整正式結果；「待補工具」表示現有程式還不能完整輸出這項要求。原始status文件中的GPT-4依使用者決定替換為Luna，保存時仍明列這個條件差異。

### 06：每階段、標籤、錯誤、模型與費用

| 原始要求 | 記錄單位與必需內容 | 明確輸出 | 目前覆蓋與驗收 |
|---|---|---|---|
| 各階段prompt | 每case／stage／entity／觀測類別；保存實際送出的完整UTF-8文字。first記node或pod與CPU等類別，second記entity，third與summary記case | `L/prompts/stage-1/<case>/<entity_index>/<type>_<category>.txt`；`stage-2/<case>/<entity_index>.txt`；`stage-3/<case>.txt`；`summarization/<case>.txt` | 部分已有；100cases全部預期prompt能定位，與實際request文字一致 |
| 各階段response | 與prompt相同單位，保存完整原始回答；另關聯request hash、model與duration，不能用解析結果取代原文 | `L/responses/`同上層級；`L/requests/<hash>.json` | 部分已有；每成功stage有原文，失敗／中斷不冒充完整回答 |
| 解析後exact_fault_type | 每case/entity：`case_index,entity_index,entity_name,raw_exact_fault_type,normalized_fault_type,label_id,parse_status,validation_status,response_path`；未知或缺漏保留原值與原因 | **待產生／待補完整匯出**：`L/labels/parsed_labels.jsonl`；可讀CSV存flatten後相同欄位 | builder已有解析與部分label_changes欄位，但尚無完整獨立parsed labels表；逐entity可回查摘要原文 |
| explanation | 每case/entity連回第三階段的實際理由。欄位：`case_index,entity_name,explanation_text,source_stage,source_path,extraction_status`；只有case層級理由時標`case_level`，無法可靠抽取entity理由時標缺失，不自行生成新理由 | 原文部分已有：`L/responses/stage-3/<case>.txt`；**待匯出**：`L/labels/explanations.jsonl`與parsed labels關聯 | 目前audit有explanation_path，尚非獨立解析後explanation；驗收须保存實際理由文字或明確缺失狀態与原文來源 |
| 完成率 | case分母100；`completed_cases,failed_cases,pending_cases,total_cases,execution_completion_rate`。另列`parseable_cases,total_expected_entities,valid_entity_labels,missing_entity_labels,valid_label_rate`；兩種完成率不混用 | 現有`L/status.json`／`summary.json`；**待補彙整**：`L/labeling_report.json`及`.md` | case狀態部分已有，summary於runner結束寫出；格式／entity完成率仍待補；三種case數合計100 |
| API／路徑錯誤 | 每失敗attempt：`case_index,stage,entity_or_request_if_known,error_category,error_type,message,time,status`；category區分auth、quota、network／API、missing_prompt／path、其他；保存可取得的HTTP status，無值標null | 現有status含case／stage／exception type／message；**待補attempt明細**：`L/errors/execution_errors.jsonl` | 未有完整timestamp／HTTP與category匯出；失敗不能被後續成功覆蓋而完全失去歷史 |
| 無法解析／格式不符數量 | 每case/entity錯誤明細：`json_parse_failed,missing_entity,unexpected_entity,invalid_type,unknown_fault`；彙總須分case與entity計數，並說明一項可有多種問題 | **待彙整**：`L/labels/validation_errors.jsonl`、`L/labeling_report.json`；builder已有`dataset/summary.json.parse_errors`与label_changes.status | 解析工具已有；完整表待全量；格式錯誤不計成No fault |
| 模型版本 | 每實際請求記`requested_model,returned_model`，run manifest記固定模型；returned值缺失標null，不能用請求值假裝回傳版本 | `L/manifest.json.model`、`L/requests/<hash>.json.model`及`metadata.returned_model`；報告彙整不同returned值與數量 | metadata已有；正式彙整待產生；不得只寫GPT-4歷史檔名字尾 |
| token用量 | 每成功request：`input_tokens,output_tokens,total_tokens`与API提供的cached input／reasoning細項；case／stage關聯後彙整總數，cache重用不算新request | `L/requests/<hash>.json.metadata.usage`；**待產生**：`L/usage/request_usage.csv`、`L/usage/summary.json` | request原始usage已有；case／stage關聯表與總量未匯出；缺失usage數另列 |
| 成本 | 明列`cost_kind(actual_or_estimate),currency,pricing_source,pricing_date,input_rate,output_rate,cached_rate,token_basis,cost,missing_reason`；採usage乘適用費率時稱估算，不稱帳單實付 | **待產生**：`L/usage/cost.json`及可讀報告 | 尚未完成；無法取得費率／實付資訊時標不可得，不填0、不宣稱精確成本已驗收 |

### 07：更新前後、標籤數、分布及五個seed產物

| 原始要求 | 記錄單位與必需內容 | 明確輸出 | 目前覆蓋與驗收 |
|---|---|---|---|
| 更新前後y／y_mask | 保存更新前dataset路徑／hash与完整原陣列、更新後独立dataset；逐selected case/entity記`y_before,y_after,mask_before,mask_after,llm_label,status,reason`，額外entity／未知值不省略 | 原prepared source保持唯讀；`L/dataset/k1_luna.pkl`、`label_changes.json`、`summary.json`；**待補完整陣列快照**：`labels_before.npz`／`labels_after.npz`含各split y及y_mask | 工具已有／正式檔待執行；完整快照匯出待補；不只列前幾行diff，全部變更可核對 |
| 新增label數 | `new_mask_count`定義mask0→1的entity occurrences；另列`applied,already_labeled,changed_y_count,ignored_count`及忽略原因，不把正常No fault排除 | builder summary已有applied／new_mask_count；**待補**：`L/dataset/update_statistics.json` | 部分統計工具已有；正式結果及補充統計待產生；新增數可由逐entitydiff重算 |
| fault-type分布 | 更新前／後按`entity_type,fault_id,fault_name`列`labeled_count_before,labeled_count_after,newly_labeled_count,changed_to_count,ignored_count`；No fault單列；masked與可用labels分開 | **待補工具／產生**：`L/dataset/fault_type_distribution.csv`与JSON | 現有builder沒有完整分布匯出；各類計數合計與mask總數一致 |
| seeds405–409、k=1 | 每run：`seed,k,actual_model_labeling_strategy,dataset_path/hash,prepared_dataset_path/hash,split_hash,preprocessing,hyperparameters,requested/completed_epochs,exit_code` | `K1(s)/manifest.json`与`metrics/training_summary.json`；source label字尾與實際Luna策略分開 | 工具大部分已有；split hash／全hyperparameters須補足manifest；五組不得混用不同dataset |
| 各seed checkpoint | 實際checkpoint檔＋`seed,checkpoint_path,bytes,sha256,completed_epochs`；保存artifact不只路徑 | `K1(s)/models/model_seed_<s>_k_1.pkl`，實際路徑依CLI model_dir；summary記同檔hash | 待正式訓練；五檔可讀且hash重算一致，失敗run不算完成 |
| 各seed duration | 分開`training_duration_seconds`與`wall_clock_duration_seconds`，单位秒；start/end timestamp保存時區 | training summary的duration_seconds；runner manifest的總duration／timestamp | 工具已有／正式結果待執行；五seed都有時間，不能用單seed時間乘5替代 |
| 各seed訓練log | 每epoch `epoch,total_loss,labeled_loss,iterative_loss,learning_rate,duration_seconds`，另保存完整stdout/stderr與錯誤 | `K1(s)/metrics/training_history.json`／`.csv`，`stdout.log`／`stderr.log`，`training_summary.json` | 工具已有／正式執行待開始；500epochs連續且與completed_epochs相符，失敗log保留 |

### 08：逐seed、統計摘要、絕對／相對差與論文方向

| 原始要求 | 記錄單位與必需內容 | 明確輸出 | 目前覆蓋與驗收 |
|---|---|---|---|
| 相同切分與seeds | 每seed配對記`before_run,after_run,seed,entity_type,GT_hash,split_hash,features_hash,preprocessing,checkpoint_hash`；labels差異另外保留 | **待產生／補條件檢查**：`C/pairing_manifest.json` | compare工具現在只嚴格核對seed／entity集合、GT與metric欄位，不能當作已驗證split／features／前處理一致 |
| localization AC@1／3／5 | 每strategy(k0/k1)×seed×entity_type記三項數值與test_case_count；保存ranking與GT以可重算 | `K0(s)`／`K1(s)`評估的`metrics/per_seed_metrics.json`／`.csv`；**待補**：`evaluation/case_predictions.jsonl`（case、GT、ranking） | metrics工具已有；正式結果與逐案例匯出待產生。原始08本次重讀未列Avg@5；現工具另存AC@2／4與Avg@5，標為追加分析，不冒充原要求 |
| fault-type Precision／Recall／F1 | 同單位分Micro／Macro記P／R／F1，保存類別集合、No fault與support定義；逐case/entity prediction與GT供重算 | 同上per_seed_metrics六欄：`micro_precision_score,micro_recall_score,micro_f1_score,macro_precision_score,macro_recall_score,macro_f1_score` | 工具已有／正式結果未有；不可只報單一F1或只報service |
| 逐seed結果 | 一列對應seed×entity_type×metric，列k0值、k1值、配對來源 | `C/comparison.json.per_seed`；**待補可讀CSV**：`C/per_seed_comparison.csv` | paired JSON工具已有；五seed与三entity types覆蓋一致 |
| mean±std | 每entity_type×metric×strategy保存`count=5,mean,std,std_definition=population(ddof0)`与5個原值；不能平均先四捨五入值 | 各evaluation summary JSON／CSV；`C/comparison.json.summary`与`comparison.md` | 工具已有／正式彙整待結果；標std不是標準誤，兩策略分別計算 |
| 絕對／相對差 | 每seed与彙整列`delta_percentage_points=100*(k1−k0)`、`relative_percent=100*(k1−k0)/k0`；k0為0時null／N/A，說明原因 | `C/comparison.json`与`.md`，上述CSV同步 | 工具已有；先固定metrics為0～1再轉百分點，不能混比例與百分比 |
| 與論文提升方向比較 | 每表格row：`paper_source,page/table/row,dataset/entity_type,metric,paper_k0,paper_k1,paper_delta,local_k0,local_k1,local_delta,direction_match,condition_differences` | **待產生／工具待補**：`C/paper_comparison.csv`与`paper_comparison.md` | 現comparison工具沒有論文值／方向表；需核對原文，Luna／clipping與paper条件不同明列；無法對應的row標未比較 |

### 09：10～20實際案例與dataset update影響

| 原始要求 | 記錄單位與必需內容 | 明確輸出 | 目前覆蓋與驗收 |
|---|---|---|---|
| 故障案例／entity | 每錯誤實例記`error_id,case_index,date/cloudbed,start/end_time,entity_index,entity_name,entity_type`；同case多entity明列 | 現有`L/audit/errors.json.entity_errors`；**待補定位欄位及CSV**：`L/audit/error_cases.csv` | case/entity已有；日期／時間locator待補。列10～20真實例，不足列全部與不足原因 |
| GT label與LLM label | `gt_id,gt_name,gt_source_path,gt_split/case/entity_locator,llm_raw_value,llm_normalized_name,llm_id`；GT不是LLM可用label來源 | errors JSON已有GT值／名与LLM值；**待補精確GT來源及locator** | 部分已有；每GT可從來源重取，不只依entity名稱猜日期 |
| 原始response | 完整摘要回答、response_path与第三階段原文來源；必要時引用first／second定位原因 | errors JSON的raw_response／response_path／explanation_path；`L/responses`保存完整stage原文 | 部分已有；報告可節錄，但原文不可只保存節錄；無法歸因stage標未知 |
| 錯誤類型 | 每例`error_types`可多標籤，固定分類名稱与定義；parse、missing、unknown、invalid type與fault mismatch分開 | 現有errors JSON、summary error_type_counts；**待補分類定義**：`L/audit/error_taxonomy.json` | 工具部分已有；同例多標籤造成加總大於案例數時解釋 |
| 對dataset update影響 | 實際更新後記`update_status,y_before/y_after,mask_before/mask_after,applied_or_ignored,ignore_reason,dataset_hash`；連回07 diff；未正式更新須標simulation | 現audit all_label_changes含模擬值；**待關聯**：`L/audit/update_impact.jsonl`与正式label_changes | 現在只有模擬，不能標已採用；正式07完成後核對錯誤是否進入訓練 |
| 各錯誤類型數量 | `error_type,entity_occurrence_count,distinct_case_count,denominator,rate`，另列parse失敗、不可評估GT與無label數；格式問題与可評估標籤錯判分母分開 | summary現有部分counts；**待補**：`L/audit/error_type_counts.csv`及`report.md` | 已有前2case分析；全量統計待產生，不外推部分比例 |

### 10：各script輸入／輸出數量、schema、耗時、失敗與manifest

| 原始要求 | 記錄單位與必需內容 | 明確輸出 | 目前覆蓋與驗收 |
|---|---|---|---|
| 每script輸入／輸出筆數 | 每stage×split×date×cloudbed×modality：`input_files,input_count,input_unit,output_files,output_count,output_unit`；Metric取樣值／CSV rows、Trace spans、Log messages、GT故障事件、windows故障案例、topology entities/edges、final dataset cases各用對應單位 | **待補工具**：`R/stage_counts.csv`与JSON；全量run同格式 | 現raw runner只記duration／exit，不記完整數量；不能用檔案bytes冒充筆數；聚合前後不同單位不直接相減 |
| 每script schema | CSV記欄名／dtype／timestamp單位／entity key，JSON記必要keys與型別，tensor／pkl記split／modality／axes／shape／dtype／NaN/Inf與缺模態；記實際field count | **待補工具**：`R/stage_schemas.json`；各stage項目連回產物path | 目前沒有全stage schema匯出；每種類輸出均有schema，不只final shape |
| 每script duration | `module,attempt_id,started_at,ended_at,time_zone,duration_seconds,exit_code,config_path/hash,log_path`；不同重跑attempt分開 | 現有`R/pipeline_status.json`含module／command／duration／exit；logs與修正前備份；**待補attempt明細**：`R/stage_runs.jsonl` | 耗時部分已有；timestamp／attempt連續歷史待補；不能只留最后成功時長 |
| 失敗案例 | `stage,attempt_id,split,date,cloudbed,input_path,entity/window_if_known,error_type,message,status/action,log_path`；若stage在案例生成前失敗，不編造case_id | 原失敗log與status已保存；**待補表**：`R/failures.jsonl`／`.csv` | 已有缺Istio例的原log，結構化完整列表未有；失败项與后续恢復可关联 |
| 最終temp_data manifest | 每artifact：`relative_path,artifact_kind,split/date/cloudbed/modality,bytes,sha256,row_or_case_count,schema_ref,producing_stage`；scope列抽樣／全量与预期coverage | 現有collect_artifacts输出path／bytes／hash至`R/artifact_manifest.json`；**待補欄位**：`R/final_manifest.json` | manifest僅完成runner各指定stage後生成；當前不能當最終完成。每final依賴均在manifest，路徑可讀 |
| 自建vs released shape | 同split/date/cloudbed/entity/window/modality記`own_path,released_path,own_shape,released_shape,feature_order_match,status` | **待補工具**：`R/comparison/shapes.csv` | 未完整生成；只比對共同coverage，缺日期另列不能跳過不報 |
| label與topology比較 | labels記case時間／entity／fault_id／mask差異；topology記entity順序、edge數、實際edge集合差、dangling edges、方向／self-loop設定 | **待補工具**：`R/comparison/labels.csv`、`topology.json` | 未完成；只比較同locator。label分布相同不代表逐case label相同 |
| Metric／Trace／Log特徵比較 | 每同locator與feature記`own_value,released_value,abs_diff,NaN_status,tolerance,status`，摘要列max/mean abs diff与超過容差數；統計fit範圍与template版本不同另列原因 | **待補工具**：`R/comparison/features.csv`、`summary.json`、`report.md` | 未完成；先確認單位／尺度／feature順序。抽樣fit差異不直接當程式錯誤；不得只報shape相同 |

### 11：encoder訓練紀錄、embedding及下游比較

| 原始要求 | 記錄單位與必需內容 | 明確輸出 | 目前覆蓋與驗收 |
|---|---|---|---|
| dataset／模態組合 | 每encoder run：`dataset_path,sha256,entity_type,modality_combination,input_shape,input_feature_order,training_splits,fit_scope`；組合須由實際loader确认，不只依据pkl名字 | 現`T/config.json`／`summary.json`記dataset、entity、shape、splits；**待補**feature／modal明細至`T/input_manifest.json` | 訓練input來源已有；精確模態欄位對照尚需補，不混07 encoder |
| seed | 每run保存數值seed與隨機初始化設定來源，模型與input對應 | `T/config.json.seed`／`summary.json.seed` | 已保存405；如追加seed另run，不覆盖 |
| hyperparameters | `input_dims,output_dims,batch_size,lr,max_train_length,epochs`，另外記encoder架構／depth、optimizer、device、source commit与encoding設定以核對預設值 | 已有前六項：`T/config.json.config`与epochs；**待補預設／環境完整快照**：`T/training_configuration.json` | 核心參數已有，完整default來源与encoding設定待補；不把padding當訓練超參數 |
| loss curve | 每epoch `epoch,loss,elapsed_seconds`完整600點；同資料產生線圖與說明，loss非下游accuracy | 已有`T/loss.csv`／`progress.json`；**待產生圖**：`T/loss_curve.png` | 完整數值已有，圖待產生；圖的點數／終值與CSV一致 |
| duration | 單位秒；分training、encoding與total duration，記start/end時區；目前summary總時長不能全部稱純訓練 | 已有`T/summary.json.duration_seconds`是訓練加單序列encoding總耗時；progress最後elapsed近似訓練結束；**待補**`T/timing.json` | 總時長已有；精確分段歷史若未記不得虛填，用可取得值与限制說明 |
| checkpoint | 實際model檔与`path,bytes,sha256,completed_epochs`，中途checkpoint可另存 | 已有`T/model.pkl`、每20epochs中途檔及summary hash | 已完成600epochs；驗收重算hash与可載入，不能只保存檔名 |
| 自訓vs released embedding差異 | 每split/date/entity：兩來源／hash、timestamps、shape、finite、MAE／max abs diff、比較設定；全覆盖摘要另外計數 | 已有`T/sample_embedding.pkl`及summary的單序列comparison；**待補全量**：`D/embedding_comparison.csv`与`encoding_manifest.json` | 單test序列已完成；全量與feature/modal對應未完成，不把MAE直接解讀為品質優劣 |
| 下游RCA指標差異 | 每paired seed/entity/metric記released與self-trained值、delta、embedding／dataset／checkpoint hash与split／labels／training設定。分類与定位分别列；無定位输出標pending而非填0 | **待產生／工具待補**：`D/released/`與`D/self_trained/`run artifacts、`D/downstream_comparison.json`／`.csv`／`.md` | 全部待下游；若只一seed不報五seed mean±std；classification-only不足以宣稱完整RCA比較 |

### 核對結論與具體缺口

原始文件指定的保存／回報項目已逐項列在以上六張表，每項有欄位、單位、位置與驗收，沒有用「保留完整證據」代替具體內容。**這是記錄需求已具體化，不是說上述檔案全部已存在。**

此處46條為逐項驗收規格；各表的「待補」是規格制定時的狀態，最新執行狀態以[工作紀錄](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/docs/unattended_progress.md)及實際run artifacts為準。已新增parsed labels／explanation、unique request usage與API等值成本估算、完整y／mask快照及類別分布、逐entity prediction保存、經觀測內容核對的時間locator、各stage counts／schema與結構化失敗、全序列encoding與paired下游工具。仍須以實際完成的實驗輸出逐項驗收，不能只因工具存在而勾選。
