# LasRCA 後六項任務介紹與結果草稿 v2

2026-10-11。依 [簡報歸納原則](task_introduction_principles_20261011.md) 撰寫，涵蓋0C-06～11。2026-10-12補齊原始要求的結果與附錄，原第二版結構及0C-08小數呈現保留。每項保留「介紹正文」，新增「結果正文」，講稿備註交代必要性、名詞、來源及解讀限制。第一版保留於six_tasks_introduction_draft_20261011.md。這是完整文字草稿，尚未決定一頁放多少內容，也未將技術細節從正文刪除。實驗已按核准範圍完成，以下目標與要求用於介紹工作，不代表要再執行一輪。

沿用公開程式的100 cases／subgraphs；LLM採使用者核准的GPT-6 Luna OAuth，原07／08的GPT-4條件因此有替代設定差異。原始進度文件與PPTX均未修改。OAuth與新增紀錄／恢復功能屬與論文演算法無關的執行支援。

## 0C-06 Labeling Method Verification｜LLM標註流程驗證

### 介紹正文

**目標**

- 確認所選故障案例能完成四階段LLM分析，取得可供分類器使用的entity故障類型標籤。
- 檢查回答能否解析、名稱與故障類型是否合法，並保存模型判斷的實際理由。
- 記錄執行錯誤、模型版本、token用量及成本，說明此次標註的完成範圍。

**要求**

- 沿用已選出的100個cases／subgraphs，逐案例保存first、second、third及summarization的完整prompt與response。
- first按node／pod的Metric類別分析，second整合同一entity的判斷，third結合子圖關係分析，summarization整理為entity名稱與`exact_fault_type`。
- 保存解析標籤及stage-3的實際explanation，分別統計案例完成率、格式異常及合法entity labels數。
- 記錄每個請求的requested／returned model、usage與API／路徑錯誤。成本估算須標明計算依據，OAuth實付不可得時明列不可得。

**程式變更**

- 以OAuth接入GPT-6 Luna，保持公開程式四階段流程與prompt語義。這是模型與呼叫方式的替代設定，不代表原GPT-4結果重現。
- 新增請求與案例／階段的關聯、原文保存、格式驗證及中斷恢復，讓錯誤與成功產物可追查。上述功能屬執行支援，與論文演算法無關。

### 結果正文

| 驗證項目 | 本輪結果 |
|---|---|
| 四階段完成 | 100／100 cases，完成率100%；各階段prompt與response已保存 |
| 摘要解析 | 100／100可解析，JSON parse errors=0 |
| Entity labels | 653 occurrences，640合法（98.01%）、13 unknown（1.99%） |
| 模型版本 | 2479筆成功unique requests的returned model均為gpt-6-luna |
| Token用量 | Input 3,801,843，output 737,533，total 4,539,376；成功請求usage無缺漏 |
| 成本 | API牌價等值估算USD0.66810344；OAuth實付不可得 |
| 執行錯誤 | 記錄到1次歷史OAuth／API失敗，後續恢復；目前failed／pending cases皆0 |
| Explanation | 保存完整stage-3 case層級理由與來源，不額外生成逐entity理由 |

**結果解讀**：四階段可正常走完，取得640個可供更新的標籤。合法率衡量名稱與格式是否可用，不是標籤正確率，正確性另由09核對。快取重用不算新請求，歷史失敗attempt記錄不完整，無法將1次當成全部失敗數；失敗請求的token用量也不推定為零。

**資料範圍**：LLM直接分析node／pod的Metric，第三階段加入子圖entity與關係；沒有直接讀取Trace／Log。Service標籤可由第三階段案例分析產生。

**錯誤分類與保存位置**：歷史可恢復錯誤僅能辨認case44／second_stage／OAuthError，HTTP status及實際發生時間未保存，不能進一步判定為quota、授權或網路問題。現有錯誤匯出未列出missing_prompt／path錯誤，但舊attempt history不完整，因此全歷史路徑錯誤總數為未知，不報0。恢復後100案例均完成。逐case四階段原文在luna_20261004/prompts與responses，解析後exact_fault_type在labels/parsed_labels.json，理由在labels/explanations.json；usage與錯誤明細分別在usage及errors/execution_errors.json。

### 講稿備註

頁面目的：交代LLM回答如何成為下一項訓練的輸入。entity是待判斷的node、pod或service；subgraph是該案例選取的entities及其關係。prompt是實際送給模型的提示內容，response是模型回答；`exact_fault_type`是摘要中待解析的故障名稱。OAuth是帳號授權呼叫方式，token是服務回報的輸入／輸出文字計量單位。

因為一句自然語言判斷還不能直接填入訓練資料，流程先按Metric類別分析node／pod，再合併同一entity的判斷。第三階段才結合子圖中的entities及關係，形成案例層級的判斷與理由，可涵蓋service。摘要階段將回答整理成固定格式，程式再檢查entity是否存在、故障名稱是否在合法集合內。不同stage請求數並不相同，不能用100 cases推定只有400次請求。GT不新增至prompt，也不用來修正回答。

本輪100/100案例摘要可解析，653 entity occurrences中640合法、13 unknown。occurrence指「某案例中的某entity」，同一entity出現在不同案例須分開計數。100%的案例解析完成率不表示標籤全對。第三階段理由按實際case層級保存，不編造逐entity explanation。

證據：`runs/lasrca/luna_20261004/labeling_report.json`、`labels/{parsed_labels.json,explanations.json,validation_errors.json}`、`prompts`、`responses`、`usage/{request_usage.csv,cost.json}`、`errors`。四階段對象與流程依 `docs/remaining_six_tasks.md` 的四階段表、`code/llm/run_labeling.py` 及其實際呼叫的公開labeling程式核對。API等值成本約USD0.6681，實際OAuth費用不可得。

銜接：合法回答能進入資料更新，但還需確認更新範圍及訓練是否成功。

## 0C-07 Classifier Retraining｜補標後的分類器重訓

### 介紹正文

**目標**

- 將LLM產生的合法標籤加入訓練資料，確認新增監督資訊能用於small classifier重訓。
- 檢查資料更新僅影響所選未標註entities，保留原始特徵、拓樸及評估資料。
- 使用五組seed完成k=1訓練，保存每次實際讀取的資料與模型，供前後比較。

**要求**

- 保存更新前後的完整`y`／`y_mask`、逐entity變更、新增label數及fault-type分布。
- 未知／無法解析的標籤保留原`y`／`y_mask`，記錄忽略原因，不能自動填成No fault。
- 核對features、split、topology及受保護labels不變，明確記錄新增標籤的範圍。
- 固定seeds405～409，每組完成500 epochs；保存dataset來源、訓練設定、checkpoint及SHA-256、loss、duration與完整log。

**程式變更**

- 新增標籤快照、分布與全資料差異核對，讓每個新增標籤都能追到LLM原回答。這些是與論文演算法無關的保存／驗證功能。
- 修正跨split共用label row的問題，更新前建立獨立可寫的label列，避免train更新連帶改到其他split。
- 沿用已移除標準差fallback的訓練路徑，保留Trace IQR=0時的第1／99百分位clipping。clipping是本次與公開原路徑的數值處理差異，兩組比較須一致。

### 結果正文

正式dataset已產生：640個mask由0變1，73個y值改變，13個unknown保留原值；已核對原features、split及受保護labels不變。73是更新前後類別值不同的數量，不是新增label數，與640不能相加。

| Seed | Completed epochs | 最後total loss | Run duration秒 | Checkpoint |
|---|---:|---:|---:|---|
| 405 | 500 | 0.184366 | 342.015 | model_seed_405_k_1_Luna.pkl |
| 406 | 500 | 0.096405 | 296.531 | model_seed_406_k_1_Luna.pkl |
| 407 | 500 | 0.043164 | 283.797 | model_seed_407_k_1_Luna.pkl |
| 408 | 500 | 0.137405 | 287.031 | model_seed_408_k_1_Luna.pkl |
| 409 | 500 | 0.198918 | 281.016 | model_seed_409_k_1_Luna.pkl |

五seed均完成500 epochs，checkpoint SHA-256、設定與完整history已保存。表中loss取history最後一列total_loss，epoch使用程式的0起算索引（最後499）；duration取training_summary.duration_seconds，屬run量測，不另推定純optimizer時間。Loss衡量訓練目標，不代表測試成效。

**問題及處理**：跨split共用label row曾使更新越界，保護檢查攔下後修正，重新生成正式資料並完成訓練。舊失敗保留，結果採恢復後的run。

**Log的使用**：label更新本身讀LLM摘要，不讀Log；後續small classifier的pod輸入仍包含Metric／Trace／Log數值特徵，node／service只用Metric。

**具體產物**：k1_luna.pkl及前後NPZ快照、label_changes.json、fault_type_distribution.csv、五組checkpoint／training_history；實際訓練輸入為manifest的prepared_dataset_path。

**Fault-type分布結果**：下表只統計本輪unlabeled split中mask=1的可用標籤。更新前這些位置尚未標註，所以before皆0，不能把原y內的參考值當成可用監督標籤。未更新的13個unknown不列入after；其他split完整前後表見來源CSV。

| Entity | Fault type | 更新前可用labels | 更新後可用labels | 新增labels |
|---|---|---:|---:|---:|
| node | No fault | 0 | 2 | 2 |
| node | Node CPU Failure | 0 | 6 | 6 |
| node | Node CPU Climb | 0 | 2 | 2 |
| node | Node Memory Consumption | 0 | 1 | 1 |
| node | Node Disk Read IO Consumption | 0 | 2 | 2 |
| node | Node Disk Write IO Consumption | 0 | 7 | 7 |
| node | Node Disk Space Consumption | 0 | 5 | 5 |
| node | K8s CPU Load | 0 | 0 | 0 |
| node | K8s Memory Load | 0 | 0 | 0 |
| node | K8s Network Delay | 0 | 0 | 0 |
| node | K8s Network Packet Loss | 0 | 0 | 0 |
| node | K8s Network Packet Corruption | 0 | 0 | 0 |
| node | K8s Network Packet Duplication | 0 | 0 | 0 |
| node | K8s Disk Read IO Load | 0 | 0 | 0 |
| node | K8s Disk Write IO Load | 0 | 0 | 0 |
| node | K8s Process Terminated | 0 | 0 | 0 |
| service | No fault | 0 | 198 | 198 |
| service | Node CPU Failure | 0 | 0 | 0 |
| service | Node CPU Climb | 0 | 0 | 0 |
| service | Node Memory Consumption | 0 | 0 | 0 |
| service | Node Disk Read IO Consumption | 0 | 0 | 0 |
| service | Node Disk Write IO Consumption | 0 | 0 | 0 |
| service | Node Disk Space Consumption | 0 | 0 | 0 |
| service | K8s CPU Load | 0 | 9 | 9 |
| service | K8s Memory Load | 0 | 3 | 3 |
| service | K8s Network Delay | 0 | 2 | 2 |
| service | K8s Network Packet Loss | 0 | 0 | 0 |
| service | K8s Network Packet Corruption | 0 | 7 | 7 |
| service | K8s Network Packet Duplication | 0 | 0 | 0 |
| service | K8s Disk Read IO Load | 0 | 5 | 5 |
| service | K8s Disk Write IO Load | 0 | 4 | 4 |
| service | K8s Process Terminated | 0 | 3 | 3 |
| pod | No fault | 0 | 231 | 231 |
| pod | Node CPU Failure | 0 | 0 | 0 |
| pod | Node CPU Climb | 0 | 0 | 0 |
| pod | Node Memory Consumption | 0 | 0 | 0 |
| pod | Node Disk Read IO Consumption | 0 | 0 | 0 |
| pod | Node Disk Write IO Consumption | 0 | 0 | 0 |
| pod | Node Disk Space Consumption | 0 | 0 | 0 |
| pod | K8s CPU Load | 0 | 41 | 41 |
| pod | K8s Memory Load | 0 | 14 | 14 |
| pod | K8s Network Delay | 0 | 10 | 10 |
| pod | K8s Network Packet Loss | 0 | 1 | 1 |
| pod | K8s Network Packet Corruption | 0 | 28 | 28 |
| pod | K8s Network Packet Duplication | 0 | 2 | 2 |
| pod | K8s Disk Read IO Load | 0 | 24 | 24 |
| pod | K8s Disk Write IO Load | 0 | 20 | 20 |
| pod | K8s Process Terminated | 0 | 13 | 13 |

**y／y_mask實際例子**：case5的productcatalogservice-1原y=14、mask=0，LLM給No fault後y=0、mask=1；這展示「新增可用label」同時可能改變類別值。此例與GT不符，09將其列為漏判，不回填修正。完整labels_before.npz／labels_after.npz保留每split的y與y_mask，label_changes.json逐項可核對。

**資料／訓練證據**：dataset/k1_luna.pkl SHA-256=6e42fe9cfd49a5ad5173449bdb5001dcfd83c4743554a1d666efa86ca89cb3d8；五seed均使用該prepared dataset。sweep_status.json逐seed指向timestamped run，每run的checkpoints、metrics/training_history.json/.csv、stdout.log／stderr.log及manifest保存模型、完整訓練log與來源。結果使用Luna，不宣稱完成原GPT-4設定。

### 講稿備註

頁面目的：區分「模型產生標籤」與「標籤正確進入訓練」。`y`保存故障類別，`y_mask`表示該位置是否有可用監督標籤。mask由0變1代表新增可用標籤，即使類別是No fault也應計入。split是程式使用的資料分組／索引，seed是固定隨機過程的設定，epoch是一次訓練循環，checkpoint是保存的模型參數，SHA-256用來辨認檔案版本。

本輪先將640個合法標籤更新到所選位置，13個unknown不更新。完整前後快照與差異核對能確認labels流向，避免用少量抽查漏掉其他split的變動。實際遇到共用label row造成更新越界，保護檢查攔下後修正，才生成正式dataset並完成五seed訓練。這個修正是讓更新符合既定範圍，沒有用GT把LLM錯標改成正解。

k=0表示補標前，k=1表示本輪補標後。這裡「重訓」只交代實際dataset與500 epochs設定，不額外聲稱論文要求特定接續訓練方式。IQR是中間50%數值的範圍，clipping是限制極端數值的處理；此設定及其影響須與k0對照共同記錄。

證據：`luna_20261004/dataset/{labels_before.npz,labels_after.npz,label_changes.json,input_signature.json,update_statistics.json,fault_type_distribution.csv}`、`luna_k1_no_std/sweep_status.json`所指五個run的manifest／checkpoints／training history。此處及以下run路徑均相對 `runs/lasrca`。

銜接：五組模型都完成，只能證明可訓練，效果是否改變須用相同條件比較。

## 0C-08 Retrained Classifier Evaluation Comparison｜補標前後成效比較

### 介紹正文

**目標**

- 比較補標前k=0與Luna補標後k=1的故障定位及分類效果。
- 固定資料與訓練條件，讓前後差異可以對應到本輪標籤更新。
- 比較五seed結果與論文提升方向，說明提升、下降及設定差異。

**要求**

- k0／k1配對使用相同features、split、GT、前處理及seeds405～409，兩組各500 epochs。
- 對node、pod、service回報AC@1／3／5，以及Micro／Macro Precision、Recall、F1。
- 保存逐seed結果及mean ± std，明列std採五seed的母體標準差。
- 回報絕對差與相對差，標明小數絕對差或相對百分比；基準為0時相對差列不可計算。
- 保存逐entity probability、GT及案例ranking以供重算，與論文對應表格逐項比較方向及條件。

**程式變更**

- 新增輸入配對核對、checkpoint重評估與逐案例預測匯出，確認比較使用實際完成的模型。
- 新增逐seed／統計摘要及論文方向表。以上是與論文演算法無關的評估與保存功能。

### 結果正文

k0／k1各五seed、各500 epochs，使用相同features、split、GT與前處理。每格按A／Service、B／Pod、C／Node排列。k0與k1沿用舊PPT的0～1小數，呈現mean ± 母體std；提升大小保留正負號，負值表示下降，並非所有指標都提升。

| Metric | k0（A／Service、B／Pod、C／Node） | k1（A／Service、B／Pod、C／Node） | 該指標提升大小（絕對／相對） | 論文該指標提升大小（絕對／相對） |
|---|---|---|---|---|
| AC@1 | A：0.7886 ± 0.0531<br>B：0.5628 ± 0.0631<br>C：0.7940 ± 0.0520 | A：0.7955 ± 0.0487<br>B：0.5837 ± 0.0680<br>C：0.7642 ± 0.0593 | A：+0.0068／+0.86%<br>B：+0.0209／+3.72%<br>C：-0.0299／-3.76% | A：不可計算／不可計算<br>B：不可計算／不可計算<br>C：不可計算／不可計算 |
| AC@3 | A：0.8682 ± 0.0318<br>B：0.6721 ± 0.0438<br>C：0.8955 ± 0.0189 | A：0.8977 ± 0.0287<br>B：0.7023 ± 0.0463<br>C：0.8806 ± 0.0443 | A：+0.0295／+3.40%<br>B：+0.0302／+4.50%<br>C：-0.0149／-1.67% | A：不可計算／不可計算<br>B：不可計算／不可計算<br>C：不可計算／不可計算 |
| AC@5 | A：0.9227 ± 0.0376<br>B：0.7116 ± 0.0371<br>C：0.9254 ± 0.0250 | A：0.9250 ± 0.0293<br>B：0.7651 ± 0.0200<br>C：0.9045 ± 0.0396 | A：+0.0023／+0.25%<br>B：+0.0535／+7.52%<br>C：-0.0209／-2.26% | A：不可計算／不可計算<br>B：不可計算／不可計算<br>C：不可計算／不可計算 |
| Micro Precision | A：0.7537 ± 0.0691<br>B：0.7747 ± 0.0542<br>C：0.5848 ± 0.0173 | A：0.6685 ± 0.1055<br>B：0.6645 ± 0.0160<br>C：0.4784 ± 0.0710 | A：-0.0852／-11.30%<br>B：-0.1103／-14.23%<br>C：-0.1064／-18.19% | A：-0.1926／-25.64%<br>B：-0.3881／-48.95%<br>C：+0.1126／+20.62% |
| Micro Recall | A：0.2636 ± 0.0317<br>B：0.2831 ± 0.0184<br>C：0.2687 ± 0.0313 | A：0.4682 ± 0.0243<br>B：0.5014 ± 0.0210<br>C：0.4209 ± 0.0257 | A：+0.2045／+77.59%<br>B：+0.2183／+77.10%<br>C：+0.1522／+56.67% | A：+0.2750／+119.83%<br>B：+0.3817／+139.56%<br>C：+0.1791／+70.60% |
| Micro F1 | A：0.3900 ± 0.0416<br>B：0.4136 ± 0.0175<br>C：0.3670 ± 0.0312 | A：0.5449 ± 0.0252<br>B：0.5709 ± 0.0081<br>C：0.4451 ± 0.0342 | A：+0.1548／+39.70%<br>B：+0.1573／+38.04%<br>C：+0.0780／+21.27% | A：+0.1745／+49.87%<br>B：+0.0911／+22.43%<br>C：+0.1784／+52.29% |
| Macro Precision | A：0.6426 ± 0.0811<br>B：0.7752 ± 0.0229<br>C：0.6910 ± 0.0133 | A：0.5963 ± 0.0448<br>B：0.7145 ± 0.0498<br>C：0.5697 ± 0.0961 | A：-0.0463／-7.21%<br>B：-0.0607／-7.83%<br>C：-0.1213／-17.56% | A：-0.0417／-6.86%<br>B：-0.2481／-32.63%<br>C：+0.0504／+7.37% |
| Macro Recall | A：0.2920 ± 0.0324<br>B：0.3096 ± 0.0171<br>C：0.2843 ± 0.0349 | A：0.5342 ± 0.0314<br>B：0.5456 ± 0.0198<br>C：0.3907 ± 0.0205 | A：+0.2422／+82.96%<br>B：+0.2359／+76.20%<br>C：+0.1064／+37.44% | A：+0.3016／+122.35%<br>B：+0.3810／+128.02%<br>C：+0.1431／+52.94% |
| Macro F1 | A：0.3619 ± 0.0341<br>B：0.4014 ± 0.0174<br>C：0.3601 ± 0.0348 | A：0.5176 ± 0.0290<br>B：0.5622 ± 0.0097<br>C：0.4105 ± 0.0326 | A：+0.1557／+43.03%<br>B：+0.1608／+40.05%<br>C：+0.0504／+14.01% | A：+0.2106／+65.53%<br>B：+0.1821／+47.02%<br>C：+0.1519／+45.59% |

絕對差＝k1−k0，保留正負號並以小數表示，不取絕對值；相對差＝100×(k1−k0)/k0，以百分比表示。k0、k1、std及絕對差顯示四位小數，相對差顯示兩位小數，均從未四捨五入的原值計算。

**論文比較依據**：分類使用Table 4的Small Classifier（V2）與Small Classifier + LLM（V1），未加入SRE correction。論文沒有另外列提升大小表，上欄是本次依原數值計算。Table 2的定位對照只有k1，缺少可配對的k0，因此AC@1／3／5的論文絕對與相對變化均列不可計算，不填0。

**結果解讀**：node的AC@1／3／5皆下降，pod／service皆提高；三類Micro／Macro Recall與F1提高，Precision下降。分類18個方向中16個與論文相同，兩個不同為C／Node的Micro／Macro Precision。不能描述為全面提升。

**比較限制與來源**：本次Luna替代論文GPT-4，Trace clipping及Macro F1定義差異另列，不能把差異全部歸因於LLM替換。本表取自runs/lasrca/luna_k0_k1_comparison/paper_comparison.csv；逐seed數值、checkpoint重評估與論文原始值／locator保留於同run的per_seed_comparison.csv、pairing_manifest.json及paper_comparison.md。

**逐seed結果**：本草稿[附錄A](#附錄a逐seed比較)直接列出五seed×三entity×原始九項metric的135列結果，包括k0、k1、絕對與相對差。完整CSV另含AC@2／4及Avg@5追加指標，不混為原要求。


### 講稿備註

AC@u衡量實際故障entity是否進入模型前u名定位結果。Precision衡量預測某故障類型的結果中有多少正確，Recall衡量該故障類型中有多少被找出，F1是兩者的調和平均。Micro先合併類別計數再算指標，Macro先按類別計算再平均。公開程式的Macro F1是逐類F1平均，與論文文字及舊簡報notes所述的Macro P／R調和平均須分開。GT是評估用參考標籤，probability是類別機率，ranking是定位排序。

為了避免把資料或前處理變動誤當成補標效果，兩組除新增LLM labels外保持相同條件。各seed先配對，再彙整五組平均與母體std。絕對差為k1−k0，使用與原指標相同的小數尺度；相對百分比為100×(k1−k0)/k0，兩者不能混用。

本輪三類F1與Recall均提高，Precision均下降；node定位下降，pod／service定位提高。分類18個方向有16個與論文一致，兩個不同是node的Micro／Macro Precision。這支持本條件下補標效果有取捨，不能宣稱每個錯標造成某個指標變化的獨立因果證明。公開GPT-4模型的歷史evaluation與本輪Luna五seed比較屬不同實驗，不混成同一baseline。

證據：`luna_k0_k1_comparison/{pairing_manifest.json,comparison.json,per_seed_comparison.csv,summary_comparison.csv,paper_comparison.json,paper_comparison.md}`；兩個sweep的 `prediction_verification` 與各run的 `predictions`。論文表格對應及來源頁碼以 `paper_comparison` 的原文locator為準，Luna與clipping差異維持明列。

銜接：整體指標顯示升降，下一項回到實際回答，檢查哪些錯標進入了訓練。

## 0C-09 Labeling Errors Summarization｜標註錯誤與更新影響

### 介紹正文

**目標**

- 檢查LLM labels與GT不符或格式異常的情況，區分錯標與無效回答。
- 追蹤錯誤是否實際更新至dataset，說明新增監督資訊的風險。
- 以真實案例與完整回答整理錯誤類型，避免僅憑總完成率判斷標註品質。

**要求**

- 全量核對LLM labels與GT，列出10～20個不同的實際錯誤／格式異常案例。
- 每例記錄案例時間與entity、GT及來源位置、LLM label、完整response與錯誤類型。
- 關聯正式dataset diff，保存`y`／`y_mask`前後值、採用或忽略狀態及原因。
- 分開統計錯誤cases、entity occurrences及錯誤類型，交代分母與分類是否重疊。

**程式變更**

- 新增案例時間／GT定位、錯誤分類與原response對照表，再關聯正式更新結果。
- 原先模擬更新影響改以正式dataset diff核對。這些是離線重現驗證，與論文演算法無關，不用GT回填或修正LLM labels。

### 結果正文

全653 entity occurrences核對，發現86異常occurrences，分布在36個不同cases；詳細報告選20個不同cases並保存原回答及正式更新影響。

| 類型 | Entity occurrences | 正式更新影響 |
|---|---:|---|
| 漏判 | 50 | 合法但與GT不符的標籤，按規則更新 |
| 誤報 | 16 | 合法但與GT不符的標籤，按規則更新 |
| 故障類別錯判 | 7 | 合法但與GT不符的標籤，按規則更新 |
| Unknown fault | 13 | 未更新，保留原y／mask |
| 合計 | 86 | 73個合法錯標進入更新，13個unknown忽略 |

本表四類採互斥細分類，加總為86；上層label_disagrees_with_ground_truth統計包含前三類，不能再加一次。合法標籤與GT一致為567／640（88.59%）；若以全653為分母則567／653（86.83%）。兩者皆不同於06的98.01%合法率，也不同於案例層級正確率。

**真實案例**：case_index=5、2022-03-24／cloudbed-3的productcatalogservice-1。GT為K8s Disk Write IO Load，LLM摘要給No fault。正式更新y由14變0、mask由0變1，update_verified=True。這是漏判標籤實際進入監督資料的例子，沒有用GT修正。

**案例來源**：audit/error_cases.csv的case5／entity_index45；摘要原文responses/summarization/5.txt；GT來源與時間locator按CSV同列追溯。此例能證明錯標流入dataset，不能單獨證明它造成08某項指標下降。

**20案例的完整回答與正式更新值**：本草稿[附錄B](#附錄b20個錯誤案例)收錄既有case_details中的20個不同案例，逐例包含日期／時間locator、entity、GT、LLM label、錯誤類型與完整stage-3原回答；[附錄C](#附錄c20案例的正式更新明細)補每個相關異常entity的y／mask前後值及update_verified。完整摘要response亦按各例連結保留，原因未經逐stage證明者不自行指定。


### 講稿備註

為了判斷錯誤對訓練輸入的影響，先分兩種情況：合法故障名稱但與GT不同的錯標，會按既定更新規則成為監督訊號；unknown等無法使用的回答則保留原mask。漏判是把實際故障判為無故障，誤報是把無故障判為有故障，類別錯判是找到故障但類型不同。No fault是合法類別，unknown不是其替代寫法。

本輪653 occurrences中發現86異常entities，分布在36 cases。73個合法錯標包含50漏判、16誤報及7類別錯判，另有13 unknown。詳細報告選20個不同cases，同案例的多個entities分列，不能把20 entities當成20 cases。對原文可追查到的stage才討論形成原因，未有充分證據時標原因未確認。

本項證明哪些錯誤流入dataset，不單獨證明其對下游指標的大小或方向。進入訓練的合法錯標與未進入訓練的unknown應分開說明。

證據：`luna_20261004/audit/{errors.json,error_cases.csv,case_details.md,error_taxonomy.json,error_type_counts.csv,update_impact.jsonl,summary.json}`；GT時間／檔案locator與stage-3原回答按各案例條目定位，更新來源為 `luna_20261004/dataset/label_changes.json`。

銜接：前四項使用公開processed資料，下一項檢查從raw能否重建相應輸入。

## 0C-10 Dataset Preprocessing｜原始資料前處理重建

### 介紹正文

**目標**

- 從raw CCF AIOps 2022資料重走前處理，確認能建立分類器所需的輸入。
- 檢查各script讀寫的資料內容與數量，找出公開入口缺漏及重建差異。
- 比較自建與作者released temp_data的結構及特徵。此項是原清單的stretch goal。

**要求（依原始0C-10）**

- 從raw CCF AIOps 2022資料重新執行preprocessing。
- 保存各script的輸入／輸出內容數量及單位、schema、duration與失敗案例。
- 保存最終自建temp_data manifest，列明產物與位置。
- 抽樣比較自建與released temp_data的shape、label、topology及Metric／Trace／Log特徵。

**本次執行範圍與追加驗證（非原始新增要求）**

固定normal／train_valid／test的日期、cloudbed與GT來源，在獨立目錄執行十scripts；除原要求的抽樣比較外，另做覆蓋範圍內全量labels／topology核對。獨立目錄與記錄功能是與論文演算法無關的執行支援。

**程式變更**

- 補齊test GT JSON至CSV的無損格式轉換，啟用原入口漏跑的Istio擷取及四類Metric標準化，處理重跑目錄已存在的情況。
- 修正全NaN／零變異Metric分支沿用前一特徵值的問題，明確產生零值。此為數值行為差異，須記錄對released比較的影響。
- 新增逐script數量與產物歸屬核對，分開觀測列、feature cells、時間窗、label values與edges。上述補齊、修正與紀錄不列為論文提出的演算法。

### 結果正文

抽樣及全量各10 scripts全部exit0；全量manifest有5191 artifacts（含4份configuration inputs）、抽樣717，unknown producer=0，inspection failures=[]。

| Script | 唯一輸入檔 | 輸出檔 | Duration秒 | Exit |
|---|---:|---:|---:|---:|
| dao.topology_dao | 18 | 15 | 0.265 | 0 |
| service.ent_edge_index_generator | 18 | 1 | 0.719 | 0 |
| service.time_interval_label_generator | 16 | 6 | 3.078 | 0 |
| dao.metric_dao | 408 | 1440 | 7222.297 | 0 |
| service.metric_generator | 1445 | 2 | 1395.562 | 0 |
| dao.trace_dao | 34 | 16 | 3359.813 | 0 |
| service.trace_generator | 21 | 3 | 317.484 | 0 |
| dao.log_dao | 21 | 33 | 11628.828 | 0 |
| service.log_generator | 43 | 9 | 39.469 | 0 |
| service.dataset_generator | 1447 | 1 | 7.109 | 0 |

檔案數不能代替內容數量。完整逐script／field數量、單位及schema保留在stage_count_summary.csv與stage_input_output_counts.csv；以下列主要內容結果。

| 檢查對象 | 結果 | 範圍／解讀 |
|---|---|---|
| Window size9 labels | 4714 windows，4714 label vectors，263984 entity label values；GT無差 | 覆蓋範圍全量核對；不同window sizes分列 |
| Topology | 15組covered edge sets無差；15份輸出共2460 stored directed edges | 不含公開入口額外生成的30份out-of-scope topology entries |
| Final observations | Processed 1,209,600 entity-minute rows、44,582,400 feature cells；raw欄位另同量保存 | rows／cells分開，raw與processed不相加當案例數 |
| Final metadata edges | 7380 stored directed edges | 儲存結構含重複引用，不等於7380唯一邊 |
| 抽樣shape／timestamps | 9份DataFrame皆1440 timestamps對齊；node1440×25、pod1440×47、service1440×9 | normal／train_valid／test各第一date/cloud、各類第一entity |
| Metric／Trace／Log數值 | 234 feature比較列中228在1e-6容許內、6不同 | node72／service24皆符合；pod138中6項Istio不同，最大差約19.617 |
| Log coverage | 全量fit後9個Log features齊全 | 抽樣fit缺欄已補；名稱相同但C#與Java／Python欄位順序不同 |

**結果解讀**：流程完成與結構對齊成立，並非全量所有特徵逐值一致。6個差異是三split的Istio request_messages.source／response_messages.source；Log欄位應依名稱對齊後才能混用矩陣。全NaN／零變異分支的修正會改變部分Metric數值，已獨立揭露。

**Log的實際用途**：Log DAO解析事件templates，generator產生時間特徵並組入pod資料。此處重新生成Log特徵；07／08使用的是作者released processed資料的Log特徵，不把raw重建結果混入主比較。

**保存與限制**：舊計數表保留在accounting_before_correction_20261005。計數依程式讀寫位置與保留schema重建，非歷史逐次I/O tracing。歷史中斷留snapshot／logs；全量沒有獨立failures.jsonl，不能將缺檔描述為已保存。作者可能手動改前處理入口仍是推測。

**原始要求的完成位置**：自建final temp_data為runs/lasrca/raw_full_20261004/generated，最終dataset為generated/dataset/final/metric_trace_log.pkl（SHA-256=9d6b132b1bc769dcea249f9804628bddd6fd162067409d962c28d79812e04074），清單為同run的final_manifest.json。此結果沒有取代作者released資料，也尚未用來做自建資料的下游RCA成效驗證。

**各script輸入／輸出內容數量與schema**：[附錄D](#附錄d前處理逐script內容數量)按script、input/output、artifact family、單位列出完整stage_count_summary.csv的數量，包含不同window size各自的counts；正文前表的檔案數僅是輔助資訊。stage_input_output_counts.csv提供逐檔／field細節，stage_schemas.json提供schema，[附錄E](#附錄e前處理schema例子)列各script代表輸出的kind／shape／欄位。這是程式依賴及產物內容統計，非歷史逐次讀取量測。

**具體中斷紀錄**：2026-10-04恢復檢查時，已完成topology、edge index與time windows；Metric DAO仍未有完成狀態。當時資料、設定、Metric log與pipeline狀態保留於interruption_snapshot_20261004_154516。恢復後Metric DAO的完整attempt於07:45:45～09:46:07 UTC完成，exit0；其餘stage接續完成。這是中斷／恢復位置，未保存足夠證據判定當時中斷的精確原因；不能把inspection failures=[]當作從未有執行中斷。
**三模態抽樣比較**：以下分類依feature_coverage.json的模態metadata，並以split／date／entity／feature名稱關聯數值比較；Istio既有Metric也有Log來源，不能只按工具名稱歸類。每列對應一個split／entity／feature比較，不是唯一feature種類數。

| 模態 | 比較列數 | 數值差超過1e-6的列數 | 觀察 |
|---|---:|---:|---|
| Metric | 189 | 6 | 6列為pod Istio request_messages.source／response_messages.source |
| Trace | 18 | 0 | 依名稱及timestamps對齊後，抽樣數值在容許範圍內 |
| Log | 27 | 0 | 抽樣數值在容許範圍內；9欄名稱集合相同，欄位順序不同 |


### 講稿備註

raw是本次讀入的公開原始觀測來源，released temp_data是作者已完成前處理的產物。Metric是時間序列量測，Trace記錄服務呼叫，Log是事件文字；schema描述欄位／結構，shape描述矩陣尺寸，manifest列產物路徑與版本識別。cloudbed是資料內的部署環境分組。stretch goal表示超出前段僅載入作者產物的重現深度。

為了確認分類器輸入如何產生，先固定原始資料範圍並建立entities、關係與故障時間窗，再從三模態生成可用特徵，最後組裝dataset。不同script使用不同資料單位，不能都稱「筆數」或把檔案數當觀測數。計數依公開程式讀寫位置與保存schema重建，表示唯一依賴檔案／內容數量，沒有歷史逐次I/O tracing。node／service的首CSV選擇依現存資料夾順序推定，限制須明列。

抽樣與全量各10 scripts皆exit0、unknown producer=0。全量覆蓋4714時間窗及15組拓樸，labels／edge sets無差。抽查9份DataFrame的shape及1440 timestamps對齊，234 feature比較列中6個pod Istio數值有差；9個Log features全量fit後齊全，但欄位順序仍須對齊。fit是由資料估計統計量或template，抽樣與全量fit的範圍不同，不能用抽樣缺欄直接判定全流程失敗。

來源程式是否曾由作者手動修改入口仍是推測。補齊CSV及入口後能跑完，不等於已還原作者執行歷史。此次raw重建資料也沒有用於前面Luna主比較或TS2Vec兩輪自訓，不能將其數值差異直接歸因為那些模型的效果變化。

證據：`raw_full_20261004/{config.json,stage_script_summary.json,stage_count_summary.csv,stage_input_output_counts.csv,stage_schemas.json,stage_runs.jsonl,pipeline_status.json,evidence_failures.json,final_manifest.json}`、各script logs及 `comparison/{shapes.csv,feature_summary.csv,labels.json,topology.json}`；抽樣在 `raw_20261004`。全量沒有獨立failures.jsonl，歷史中斷保留在snapshot及logs。十script名單與執行順序見 `code/experiments/raw_pipeline.py`。

銜接：下一項獨立採作者公開processed資料，檢查自行訓練encoder後的向量與下游結果。

## 0C-11 TS2Vec embedding Training｜觀測encoder自訓與對照

### 介紹正文

**目標**

- 至少自行訓練一組TS2Vec觀測encoder，檢查觀測序列能否轉為下游使用的embedding。
- 比較自訓embedding與作者公開embedding，以及替換後的RCA指標差異。
- 明確區分作者提供的向量、自訓模型與下游分類器。此項是原清單的stretch goal。

**要求**

- 以作者公開processed資料訓練service encoder，固定8個Metric輸入及特徵順序；node／pod沿用作者embedding。
- 依公開service設定訓練600 epochs，保存dataset／SHA-256、seed、batch32、lr0.001、320維輸出、最大訓練長度3000，以及完整defaults。
- 保存loss curve、duration與encoder checkpoint，對全150段service序列檢查coverage、shape及NaN／Inf。
- 替換service embedding，以相同下游split／labels／seed405各訓練500 epochs，比較embedding與classification／localization指標。
- 保存原seed405結果，追加encoder seed406對照；下游seed保持405，記錄兩次自訓與公開基準的差異。

**程式變更**

- 新增作者archive／processed input來源與實際設定核對、訓練紀錄、全序列encoding及逐序列比較。
- 兩組下游使用獨立cache，核對實際讀入的embedding，避免舊資料快取使替換未生效。
- 新增下游定位評估與三版本對照，補足原路線的比較證據。以上保存、隔離及評估功能與論文演算法無關；追加seed406屬使用者要求的額外對照。

### 結果正文

作者公開包包含embedding_600.pkl及下游模型，沒有TS2Vec encoder權重。自訓seed405、406皆使用同一作者released processed資料（SHA-256與archive entry一致），service只含8個Metric；node／pod沿用作者embedding。

| 執行檢查 | 結果 |
|---|---|
| Encoder訓練 | 405／406各600 epochs，checkpoint、完整loss與設定已保存 |
| 全序列encoding | 兩輪皆150 service序列，1440×320，coverage／finite檢查通過 |
| 下游比較 | 公開／自訓兩路各500 epochs，固定下游seed405、split／labels一致 |
| 公開基準重跑 | 36項指標與上一輪完全一致 |
| Seed405耗時 | 訓練含載入及單序列檢查總3161.953秒，全150序列encoding 3225.640秒 |
| Timing界線 | 純訓練／單序列encoding歷史未獨立量測，保存null |

以下為下游seed405的百分比指標；405／406是encoder seed。此表不是五seed平均，故不報mean±std。最後兩欄為各自訓版本相對公開embedding的百分點差。

#### node

| Metric | 公開embedding (%) | Encoder405 (%) | Encoder406 (%) | 405差pp | 406差pp |
|---|---:|---:|---:|---:|---:|
| AC@1 | 35.8209 | 32.8358 | 37.3134 | -2.9851 | +1.4925 |
| AC@3 | 67.1642 | 62.6866 | 64.1791 | -4.4776 | -2.9851 |
| AC@5 | 79.1045 | 70.1493 | 76.1194 | -8.9552 | -2.9851 |
| Micro P | 0.9131 | 0.9156 | 0.9048 | +0.0025 | -0.0083 |
| Micro R | 68.6567 | 68.6567 | 68.6567 | 0.0000 | 0.0000 |
| Micro F1 | 1.8022 | 1.8071 | 1.7861 | +0.0049 | -0.0161 |
| Macro P | 1.1676 | 1.1681 | 1.1689 | +0.0005 | +0.0013 |
| Macro R | 70.4606 | 70.4606 | 70.4606 | 0.0000 | 0.0000 |
| Macro F1 | 2.2633 | 2.2643 | 2.2642 | +0.0010 | +0.0009 |

#### pod

| Metric | 公開embedding (%) | Encoder405 (%) | Encoder406 (%) | 405差pp | 406差pp |
|---|---:|---:|---:|---:|---:|
| AC@1 | 29.0698 | 27.9070 | 30.2326 | -1.1628 | +1.1628 |
| AC@3 | 50.0000 | 46.5116 | 47.6744 | -3.4884 | -2.3256 |
| AC@5 | 60.4651 | 55.8140 | 54.6512 | -4.6512 | -5.8140 |
| Micro P | 0.7808 | 0.7769 | 0.7856 | -0.0039 | +0.0048 |
| Micro R | 38.1279 | 37.8995 | 38.3562 | -0.2284 | +0.2283 |
| Micro F1 | 1.5302 | 1.5225 | 1.5397 | -0.0077 | +0.0095 |
| Macro P | 2.8210 | 2.8250 | 2.8325 | +0.0040 | +0.0115 |
| Macro R | 37.3703 | 37.1524 | 37.5337 | -0.2179 | +0.1634 |
| Macro F1 | 4.9541 | 4.9589 | 4.9769 | +0.0048 | +0.0228 |

#### service

| Metric | 公開embedding (%) | Encoder405 (%) | Encoder406 (%) | 405差pp | 406差pp |
|---|---:|---:|---:|---:|---:|
| AC@1 | 34.0909 | 35.2273 | 34.0909 | +1.1364 | 0.0000 |
| AC@3 | 56.8182 | 55.6818 | 55.6818 | -1.1364 | -1.1364 |
| AC@5 | 68.1818 | 72.7273 | 70.4545 | +4.5455 | +2.2727 |
| Micro P | 0.5772 | 0.5800 | 0.5731 | +0.0028 | -0.0041 |
| Micro R | 31.8182 | 34.0909 | 30.6818 | +2.2727 | -1.1364 |
| Micro F1 | 1.1338 | 1.1407 | 1.1252 | +0.0069 | -0.0086 |
| Macro P | 0.8697 | 0.8426 | 0.9070 | -0.0271 | +0.0373 |
| Macro R | 33.2099 | 36.2346 | 33.2099 | +3.0247 | 0.0000 |
| Macro F1 | 1.6335 | 1.6073 | 1.6930 | -0.0262 | +0.0595 |

**結果解讀**：兩個自訓encoder的service AC@5皆提高，node／pod AC@5皆下降；AC@1與分類指標的方向會隨encoder seed改變。service Macro F1只有約1.6～1.7%，微小差異不能描述為良好分類能力。只替換service向量仍會影響其他entities的下游結果。

**因果界線**：固定公開資料與下游條件、公開基準重跑一致，支持差異與重新學得的embedding及下游互動有關。兩次都未使用新raw資料，所以不能將這兩輪效果差異歸因於新raw；也不能因此證明新raw沒有問題。兩個encoder seeds／單一下游seed不支持穩定性或統計顯著性結論。

**Embedding數值比較**：以下由各encoding_manifest的150個序列差異彙整，每個序列等權。MAE指對齊位置的平均絕對差，數值沒有accuracy單位，也不表示品質優劣。

| Encoder seed | 序列數 | 序列MAE平均 | 最小／最大序列MAE | 全部位置最大絕對差 | 全量encoding秒 |
|---|---:|---:|---:|---:|---:|
| 405 | 150 | 0.223489 | 0.201143／2.055089 | 47.510788 | 3225.640 |
| 406 | 150 | 0.231620 | 0.207767／1.985122 | 46.720703 | 3052.812 |

**Embedding差異來源**：逐序列shape／MAE等數值保存在第一輪encoding_manifest.json與追加encoding產物，完整下游36指標見三版本CSV。Embedding數值差異不直接等於模型品質。

**實際訓練設定與產物**：兩輪讀入作者dataset/final/metric_trace_log.pkl，資料SHA-256=c594cdf9ba66c5ff493985a98ff9fdc258e6a3e45fc52d5b69051e8b54b0795b；訓練使用normal與train_valid，輸入100×1440×8，encoding覆蓋150序列。Service僅Metric，Trace／Log為0。

| 設定 | 實際值 |
|---|---|
| Encoder seeds | 405、406 |
| Epochs | 各600 |
| Input／output dimensions | 8／320 |
| Hidden dimensions／depth | 64／10 |
| Batch size／learning rate | 32／0.001 |
| Max train length／temporal unit | 3000／0 |
| Device | cuda:0 |
| 全序列encoding | causal=true，sliding_length=1，sliding_padding=10 |

| Seed | Loss首epoch | Loss末epoch | Loss點數 | Run duration秒 | Checkpoint |
|---|---:|---:|---:|---:|---|
| 405 | 210.386100 | 2.050352 | 600 | 3161.953 | runs/lasrca/ts2vec_20261004/model.pkl |
| 406 | 245.771042 | 1.307805 | 600 | 3587.844 | runs/lasrca/encoder_public_recheck_20261005/ts2vec_seed406/model.pkl |

Checkpoint SHA-256（seed405）：`bf61481604d24beb2ba2eafe6efd31cc889d95ccfd8374c8bc24a6591e03d0fc`。

Checkpoint SHA-256（seed406）：`06710ca02c0ef1cb3813c269b743d3d942778564559292458f41a8c777989c93`。

Run duration包含輸入載入及樣本encoding等run工作，不冒稱純訓練耗時。兩輪loss均由首epoch下降至末epoch；這只說明訓練目標變化，不代替下游成效，也不直接證明loss全程單調下降。

**Loss curve（seed405，600個epoch）**

![Seed405 TS2Vec loss curve](../runs/lasrca/ts2vec_20261004/loss_curve.png)

Seed406完整600點loss列於[附錄F](#附錄fencoder-seed406-loss-curve)的可繪圖數值摘要與原CSV連結；第一輪PNG／PDF及兩輪完整loss.csv均保留，不能宣稱seed406原本也有獨立PNG。

### 講稿備註

TS2Vec是將觀測時間序列轉成向量的encoder。checkpoint保存模型參數，embedding保存模型算出的向量，兩者不能互稱。作者下載包的 `model.zip` 提供下游模型，沒有TS2Vec權重；`embedding_600.pkl` 是作者已算好的embedding。因此公開基準使用作者向量，自訓路線訓練我們的encoder再產生向量。下游程式直接讀入固定embedding，沒有在此次下游訓練中端到端更新TS2Vec。

本輪只自訓service的8個Metric，沒有把Trace／Log加入service輸入。先固定資料與特徵順序，使用作者公開設定訓練600 epochs，再以相同encoding設定生成150段序列的1440×320向量。coverage表示預期序列皆有輸出，NaN／Inf是非有限值；loss顯示訓練目標的變化，不能直接當RCA accuracy。batch、lr與最大訓練長度分別指每次訓練的序列數、參數更新步幅及訓練序列長度上限。

為了比較下游效果，只替換service embedding，保持node／pod作者向量、split、labels與下游seed相同。隔離cache讓程式讀入正確版本。service向量可經圖模型與下游重訓影響node／pod結果，所以「只替換service」不代表只有service指標會變。

seed405及追加406的encoder都使用同一作者公開processed input，其SHA與archive entry一致，均未使用本次raw重建資料。公開基準在同下游seed重跑的36指標一致；兩個自訓encoder的下游結果仍有升有降。這支持encoder隨機性與重新學得的embedding影響結果，不能推定新raw資料導致下降，也不能因此證明新raw沒有問題。作者encoder seed未知，兩個encoder seeds加單一下游seed不足以宣稱穩定性或精確還原作者模型。

證據：`ts2vec_20261004/{input_manifest.json,loss.csv,loss_curve.png,timing.json,model.pkl}`、`ts2vec_downstream/{encoding_manifest.json,service_replaced.pkl}`、`encoder_pair_20261004/comparison.json`；追加run `encoder_public_recheck_20261005/{protocol.json,public_input_provenance.json,status.json}` 、`downstream/comparison.json`、run根目錄的 `three_variant_comparison.csv` 與 `verification_and_three_variants.json`。公開設定來源為 `code/pretrain.sh` 與 `code/pretrain/train.py`，下載包與實際輸入的核對見 [encoder來源報告](encoder_public_provenance.md)。未獨立量測的歷史耗時保持null，不把載入／樣本encoding總耗時全稱純訓練時間。

銜接至結論：六項完成代表既定流程與保存／比較要求完成。Luna替代設定、錯標、raw特徵差異及encoder對照範圍，仍是解讀實驗結果時必須保留的界線。

## 後續製作結果頁時的素材

本版已加入六項結果。完整逐seed／逐案例資料可從 [六項結案報告](six_tasks_closure_20261005.md)、[第一輪結果](one_round_results_20261004.md) 與 [encoder來源／追加結果](encoder_public_provenance.md) 取用數值與來源。LLM標註率、五seed重訓表、k0／k1比較、真實錯誤案例、raw對照與encoder三版本比較應分開呈現，避免用一張「全部完成」表取代必要的結果及限制。


## 附錄A：逐seed比較

對應原要求的AC@1／3／5及Micro／Macro P/R/F1，共135列。數值取未四捨五入的per_seed_comparison.csv；絕對差採小數，相對差採百分比。

| Seed | Dataset／Entity | Metric | k0 | k1 | 絕對差 | 相對差 |
|---|---|---|---:|---:|---:|---:|
| 405 | A／Service | AC@1 | 0.8864 | 0.8409 | -0.0455 | -5.13％ |
| 405 | A／Service | AC@3 | 0.9205 | 0.9318 | +0.0114 | +1.23％ |
| 405 | A／Service | AC@5 | 0.9773 | 0.9432 | -0.0341 | -3.49％ |
| 405 | A／Service | macro_f1_score | 0.3035 | 0.5082 | +0.2047 | +67.44％ |
| 405 | A／Service | macro_precision_score | 0.4987 | 0.5261 | +0.0274 | +5.50％ |
| 405 | A／Service | macro_recall_score | 0.2389 | 0.5790 | +0.3401 | +142.38％ |
| 405 | A／Service | micro_f1_score | 0.3248 | 0.5366 | +0.2118 | +65.21％ |
| 405 | A／Service | micro_precision_score | 0.6552 | 0.5789 | -0.0762 | -11.63％ |
| 405 | A／Service | micro_recall_score | 0.2159 | 0.5000 | +0.2841 | +131.58％ |
| 405 | B／Pod | AC@1 | 0.6860 | 0.5116 | -0.1744 | -25.42％ |
| 405 | B／Pod | AC@3 | 0.7558 | 0.6860 | -0.0698 | -9.23％ |
| 405 | B／Pod | AC@5 | 0.7791 | 0.7558 | -0.0233 | -2.99％ |
| 405 | B／Pod | macro_f1_score | 0.4100 | 0.5581 | +0.1480 | +36.10％ |
| 405 | B／Pod | macro_precision_score | 0.7700 | 0.6364 | -0.1337 | -17.36％ |
| 405 | B／Pod | macro_recall_score | 0.3087 | 0.5483 | +0.2396 | +77.62％ |
| 405 | B／Pod | micro_f1_score | 0.4212 | 0.5703 | +0.1491 | +35.40％ |
| 405 | B／Pod | micro_precision_score | 0.7697 | 0.6558 | -0.1139 | -14.80％ |
| 405 | B／Pod | micro_recall_score | 0.2900 | 0.5046 | +0.2146 | +74.02％ |
| 405 | C／Node | AC@1 | 0.7761 | 0.7015 | -0.0746 | -9.62％ |
| 405 | C／Node | AC@3 | 0.8806 | 0.8358 | -0.0448 | -5.08％ |
| 405 | C／Node | AC@5 | 0.8955 | 0.8507 | -0.0448 | -5.00％ |
| 405 | C／Node | macro_f1_score | 0.3571 | 0.4485 | +0.0914 | +25.59％ |
| 405 | C／Node | macro_precision_score | 0.6786 | 0.7140 | +0.0354 | +5.22％ |
| 405 | C／Node | macro_recall_score | 0.2829 | 0.3998 | +0.1169 | +41.31％ |
| 405 | C／Node | micro_f1_score | 0.3673 | 0.4874 | +0.1200 | +32.68％ |
| 405 | C／Node | micro_precision_score | 0.5806 | 0.5577 | -0.0230 | -3.95％ |
| 405 | C／Node | micro_recall_score | 0.2687 | 0.4328 | +0.1642 | +61.11％ |
| 406 | A／Service | AC@1 | 0.7273 | 0.7386 | +0.0114 | +1.56％ |
| 406 | A／Service | AC@3 | 0.8295 | 0.8636 | +0.0341 | +4.11％ |
| 406 | A／Service | AC@5 | 0.8864 | 0.8977 | +0.0114 | +1.28％ |
| 406 | A／Service | macro_f1_score | 0.3797 | 0.5148 | +0.1351 | +35.59％ |
| 406 | A／Service | macro_precision_score | 0.6847 | 0.5827 | -0.1021 | -14.91％ |
| 406 | A／Service | macro_recall_score | 0.3031 | 0.4877 | +0.1846 | +60.90％ |
| 406 | A／Service | micro_f1_score | 0.4034 | 0.5547 | +0.1514 | +37.53％ |
| 406 | A／Service | micro_precision_score | 0.7742 | 0.7755 | +0.0013 | +0.17％ |
| 406 | A／Service | micro_recall_score | 0.2727 | 0.4318 | +0.1591 | +58.33％ |
| 406 | B／Pod | AC@1 | 0.5233 | 0.5116 | -0.0116 | -2.22％ |
| 406 | B／Pod | AC@3 | 0.6628 | 0.6395 | -0.0233 | -3.51％ |
| 406 | B／Pod | AC@5 | 0.7209 | 0.7442 | +0.0233 | +3.23％ |
| 406 | B／Pod | macro_f1_score | 0.4120 | 0.5672 | +0.1552 | +37.69％ |
| 406 | B／Pod | macro_precision_score | 0.7401 | 0.7311 | -0.0089 | -1.21％ |
| 406 | B／Pod | macro_recall_score | 0.3377 | 0.5424 | +0.2047 | +60.63％ |
| 406 | B／Pod | micro_f1_score | 0.4283 | 0.5736 | +0.1453 | +33.92％ |
| 406 | B／Pod | micro_precision_score | 0.6904 | 0.6607 | -0.0296 | -4.29％ |
| 406 | B／Pod | micro_recall_score | 0.3105 | 0.5068 | +0.1963 | +63.24％ |
| 406 | C／Node | AC@1 | 0.7612 | 0.7910 | +0.0299 | +3.92％ |
| 406 | C／Node | AC@3 | 0.8806 | 0.8955 | +0.0149 | +1.69％ |
| 406 | C／Node | AC@5 | 0.9403 | 0.9254 | -0.0149 | -1.59％ |
| 406 | C／Node | macro_f1_score | 0.3965 | 0.3862 | -0.0103 | -2.59％ |
| 406 | C／Node | macro_precision_score | 0.6889 | 0.4299 | -0.2590 | -37.60％ |
| 406 | C／Node | macro_recall_score | 0.3253 | 0.4117 | +0.0865 | +26.58％ |
| 406 | C／Node | micro_f1_score | 0.3960 | 0.4255 | +0.0295 | +7.45％ |
| 406 | C／Node | micro_precision_score | 0.5882 | 0.4054 | -0.1828 | -31.08％ |
| 406 | C／Node | micro_recall_score | 0.2985 | 0.4478 | +0.1493 | +50.00％ |
| 407 | A／Service | AC@1 | 0.7841 | 0.8523 | +0.0682 | +8.70％ |
| 407 | A／Service | AC@3 | 0.8409 | 0.9091 | +0.0682 | +8.11％ |
| 407 | A／Service | AC@5 | 0.8750 | 0.9318 | +0.0568 | +6.49％ |
| 407 | A／Service | macro_f1_score | 0.3446 | 0.5494 | +0.2049 | +59.46％ |
| 407 | A／Service | macro_precision_score | 0.6270 | 0.6180 | -0.0090 | -1.43％ |
| 407 | A／Service | macro_recall_score | 0.2722 | 0.5370 | +0.2648 | +97.28％ |
| 407 | A／Service | micro_f1_score | 0.3621 | 0.5616 | +0.1996 | +55.12％ |
| 407 | A／Service | micro_precision_score | 0.7500 | 0.7069 | -0.0431 | -5.75％ |
| 407 | A／Service | micro_recall_score | 0.2386 | 0.4659 | +0.2273 | +95.24％ |
| 407 | B／Pod | AC@1 | 0.5233 | 0.6628 | +0.1395 | +26.67％ |
| 407 | B／Pod | AC@3 | 0.6279 | 0.7209 | +0.0930 | +14.81％ |
| 407 | B／Pod | AC@5 | 0.6744 | 0.7674 | +0.0930 | +13.79％ |
| 407 | B／Pod | macro_f1_score | 0.3679 | 0.5475 | +0.1796 | +48.82％ |
| 407 | B／Pod | macro_precision_score | 0.8117 | 0.7604 | -0.0514 | -6.33％ |
| 407 | B／Pod | macro_recall_score | 0.2877 | 0.5199 | +0.2322 | +80.71％ |
| 407 | B／Pod | micro_f1_score | 0.3864 | 0.5575 | +0.1711 | +44.27％ |
| 407 | B／Pod | micro_precision_score | 0.7500 | 0.6844 | -0.0656 | -8.75％ |
| 407 | B／Pod | micro_recall_score | 0.2603 | 0.4703 | +0.2100 | +80.70％ |
| 407 | C／Node | AC@1 | 0.8806 | 0.8358 | -0.0448 | -5.08％ |
| 407 | C／Node | AC@3 | 0.9104 | 0.9254 | +0.0149 | +1.64％ |
| 407 | C／Node | AC@5 | 0.9403 | 0.9552 | +0.0149 | +1.59％ |
| 407 | C／Node | macro_f1_score | 0.3751 | 0.4488 | +0.0737 | +19.64％ |
| 407 | C／Node | macro_precision_score | 0.6841 | 0.6302 | -0.0539 | -7.88％ |
| 407 | C／Node | macro_recall_score | 0.2949 | 0.3899 | +0.0951 | +32.24％ |
| 407 | C／Node | micro_f1_score | 0.3762 | 0.4828 | +0.1065 | +28.31％ |
| 407 | C／Node | micro_precision_score | 0.5588 | 0.5714 | +0.0126 | +2.26％ |
| 407 | C／Node | micro_recall_score | 0.2836 | 0.4179 | +0.1343 | +47.37％ |
| 408 | A／Service | AC@1 | 0.7614 | 0.7386 | -0.0227 | -2.99％ |
| 408 | A／Service | AC@3 | 0.8750 | 0.8636 | -0.0114 | -1.30％ |
| 408 | A／Service | AC@5 | 0.9318 | 0.8864 | -0.0455 | -4.88％ |
| 408 | A／Service | macro_f1_score | 0.3835 | 0.5457 | +0.1622 | +42.30％ |
| 408 | A／Service | macro_precision_score | 0.6609 | 0.6630 | +0.0020 | +0.31％ |
| 408 | A／Service | macro_recall_score | 0.3204 | 0.5142 | +0.1938 | +60.50％ |
| 408 | A／Service | micro_f1_score | 0.4194 | 0.5714 | +0.1521 | +36.26％ |
| 408 | A／Service | micro_precision_score | 0.7222 | 0.7692 | +0.0470 | +6.51％ |
| 408 | A／Service | micro_recall_score | 0.2955 | 0.4545 | +0.1591 | +53.85％ |
| 408 | B／Pod | AC@1 | 0.5233 | 0.5698 | +0.0465 | +8.89％ |
| 408 | B／Pod | AC@3 | 0.6628 | 0.6860 | +0.0233 | +3.51％ |
| 408 | B／Pod | AC@5 | 0.6977 | 0.7558 | +0.0581 | +8.33％ |
| 408 | B／Pod | macro_f1_score | 0.4014 | 0.5614 | +0.1600 | +39.85％ |
| 408 | B／Pod | macro_precision_score | 0.7735 | 0.7658 | -0.0077 | -0.99％ |
| 408 | B／Pod | macro_recall_score | 0.2977 | 0.5370 | +0.2393 | +80.37％ |
| 408 | B／Pod | micro_f1_score | 0.4000 | 0.5703 | +0.1703 | +42.57％ |
| 408 | B／Pod | micro_precision_score | 0.8169 | 0.6804 | -0.1365 | -16.71％ |
| 408 | B／Pod | micro_recall_score | 0.2648 | 0.4909 | +0.2260 | +85.35％ |
| 408 | C／Node | AC@1 | 0.8209 | 0.8060 | -0.0149 | -1.82％ |
| 408 | C／Node | AC@3 | 0.9254 | 0.9254 | 0.0000 | 0.00％ |
| 408 | C／Node | AC@5 | 0.9552 | 0.9254 | -0.0299 | -3.13％ |
| 408 | C／Node | macro_f1_score | 0.3767 | 0.4001 | +0.0234 | +6.22％ |
| 408 | C／Node | macro_precision_score | 0.7167 | 0.5312 | -0.1855 | -25.88％ |
| 408 | C／Node | macro_recall_score | 0.2981 | 0.3998 | +0.1017 | +34.13％ |
| 408 | C／Node | micro_f1_score | 0.3878 | 0.4296 | +0.0419 | +10.80％ |
| 408 | C／Node | micro_precision_score | 0.6129 | 0.4265 | -0.1864 | -30.42％ |
| 408 | C／Node | micro_recall_score | 0.2836 | 0.4328 | +0.1493 | +52.63％ |
| 409 | A／Service | AC@1 | 0.7841 | 0.8068 | +0.0227 | +2.90％ |
| 409 | A／Service | AC@3 | 0.8750 | 0.9205 | +0.0455 | +5.19％ |
| 409 | A／Service | AC@5 | 0.9432 | 0.9659 | +0.0227 | +2.41％ |
| 409 | A／Service | macro_f1_score | 0.3981 | 0.4697 | +0.0716 | +18.00％ |
| 409 | A／Service | macro_precision_score | 0.7417 | 0.5916 | -0.1501 | -20.24％ |
| 409 | A／Service | macro_recall_score | 0.3253 | 0.5531 | +0.2278 | +70.02％ |
| 409 | A／Service | micro_f1_score | 0.4407 | 0.5000 | +0.0593 | +13.46％ |
| 409 | A／Service | micro_precision_score | 0.8667 | 0.5119 | -0.3548 | -40.93％ |
| 409 | A／Service | micro_recall_score | 0.2955 | 0.4886 | +0.1932 | +65.38％ |
| 409 | B／Pod | AC@1 | 0.5581 | 0.6628 | +0.1047 | +18.75％ |
| 409 | B／Pod | AC@3 | 0.6512 | 0.7791 | +0.1279 | +19.64％ |
| 409 | B／Pod | AC@5 | 0.6860 | 0.8023 | +0.1163 | +16.95％ |
| 409 | B／Pod | macro_f1_score | 0.4158 | 0.5769 | +0.1611 | +38.74％ |
| 409 | B／Pod | macro_precision_score | 0.7807 | 0.6789 | -0.1018 | -13.04％ |
| 409 | B／Pod | macro_recall_score | 0.3163 | 0.5802 | +0.2639 | +83.43％ |
| 409 | B／Pod | micro_f1_score | 0.4320 | 0.5828 | +0.1508 | +34.92％ |
| 409 | B／Pod | micro_precision_score | 0.8467 | 0.6411 | -0.2056 | -24.28％ |
| 409 | B／Pod | micro_recall_score | 0.2900 | 0.5342 | +0.2443 | +84.25％ |
| 409 | C／Node | AC@1 | 0.7313 | 0.6866 | -0.0448 | -6.12％ |
| 409 | C／Node | AC@3 | 0.8806 | 0.8209 | -0.0597 | -6.78％ |
| 409 | C／Node | AC@5 | 0.8955 | 0.8657 | -0.0299 | -3.33％ |
| 409 | C／Node | macro_f1_score | 0.2951 | 0.3691 | +0.0740 | +25.08％ |
| 409 | C／Node | macro_precision_score | 0.6869 | 0.5432 | -0.1437 | -20.91％ |
| 409 | C／Node | macro_recall_score | 0.2202 | 0.3522 | +0.1320 | +59.97％ |
| 409 | C／Node | micro_f1_score | 0.3077 | 0.4000 | +0.0923 | +30.00％ |
| 409 | C／Node | micro_precision_score | 0.5833 | 0.4310 | -0.1523 | -26.11％ |
| 409 | C／Node | micro_recall_score | 0.2090 | 0.3731 | +0.1642 | +78.57％ |

## 附錄B：20個錯誤案例

以下直接收錄已保存的真實案例及完整stage-3原文。LLM回答中的推論是模型原回答，不是本草稿認定的故障因果。

### Luna 錯誤案例與資料更新影響

本次列出20個不同案例，最多20例；少於10例時保留實際數量。
「漏標／誤標」均以公開Ground Truth為判定基準，不能只據此推定實際物理故障影響。分類器沒有參與這份差異判定。
下列第三階段文字是案例層級原回答；因果判斷以可見階段結果為界，不能把理由原文當成已證實的故障因果。

#### Case 5

來源：2022-03-24／cloudbed-3，時間窗1648066260～1648066800；公開GT索引5，注入entity productcatalogservice-1。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/5.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/5.txt)。

- productcatalogservice-1：GT=K8s Disk Write IO Load；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

| Entity | Classification |
|---|---|
| productcatalogservice | No fault |
| productcatalogservice-0 | No fault |
| productcatalogservice-1 | No fault |
| productcatalogservice-2 | No fault |
| productcatalogservice2-0 | No fault |
| recommendationservice | No fault |
| frontend | No fault |
| checkoutservice | No fault |

**Reasoning:** Only `productcatalogservice-1` shows a fault characteristic: K8s Disk Write IO Load. The other three associated pods show no fault, so this service has only one fault-indicating pod. Under Rule 1, the service is classified as No fault; Rule 4 then classifies the remaining entities as No fault. Thus, the isolated pod-level indication does not result in a fault classification for the pod or its service.

#### Case 18

來源：2022-03-24／cloudbed-3，時間窗1648095000～1648095540；公開GT索引19，注入entity emailservice。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/18.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/18.txt)。

- node-4：GT=No Fault；Luna=Node CPU Failure；類型=label_disagrees_with_ground_truth, false_positive_fault。摘要提供可解析故障類別，原程式會以此類別更新y並令mask=1；因此GT不一致標籤會成為新增監督訊號。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

1. **node-4: Node CPU Failure**

2. The observation describes a brief, synchronized spike in both CPU metrics followed by a sharp drop, and identifies **Node CPU Failure** as the most probable fault type. The service-and-pod rules do not apply because no service or pod entities are provided.

#### Case 19

來源：2022-03-24／cloudbed-3，時間窗1648098120～1648098660；公開GT索引21，注入entity node-6。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/19.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/19.txt)。

- node-4：GT=No Fault；Luna=Node CPU Failure；類型=label_disagrees_with_ground_truth, false_positive_fault。摘要提供可解析故障類別，原程式會以此類別更新y並令mask=1；因此GT不一致標籤會成為新增監督訊號。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

1. **node-4: Node CPU Failure**
2. The final data point shows a sharp, simultaneous increase in CPU usage and CPU user metrics. The spike lasts only one point, so this classification is tentative. The service-and-pod rules do not apply to the listed entity, which is a node.

#### Case 20

來源：2022-03-24／cloudbed-3，時間窗1648099980～1648100520；公開GT索引22，注入entity cartservice-1。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/20.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/20.txt)。

- cartservice-1：GT=K8s Network Packet Loss；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

1. **Exact type of each entity**

| Entity | Classification |
|---|---|
| cartservice | No fault |
| frontend | No fault |
| checkoutservice | No fault |
| cartservice-0 | No fault |
| cartservice-1 | No fault |
| cartservice-2 | No fault |
| cartservice2-0 | No fault |

2. **Reasons**

Only **cartservice-1** shows a candidate fault characteristic: a brief disk-read spike classified as **K8s Disk Read IO Load**. The other three associated pods—cartservice-0, cartservice-2, and cartservice2-0—are classified as No fault. Thus, only one of the four pods displays fault characteristics, satisfying Rule 1: the service must be classified as **No fault**. Rule 4 then classifies the remaining entities as **No fault** as well.

#### Case 24

來源：2022-03-24／cloudbed-3，時間窗1648104660～1648105200；公開GT索引26，注入entity checkoutservice-1。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/24.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/24.txt)。

- checkoutservice-1：GT=K8s CPU Load；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

##### 1. Entity classifications

| Entity | Type |
|---|---|
| checkoutservice | No fault |
| shippingservice | No fault |
| productcatalogservice | No fault |
| paymentservice | No fault |
| frontend | No fault |
| emailservice | No fault |
| checkoutservice-0 | No fault |
| checkoutservice-1 | No fault |
| checkoutservice-2 | No fault |
| checkoutservice2-0 | No fault |

##### 2. Reasons

Only **checkoutservice-1** shows a fault characteristic: its CPU metrics rise together and persist, consistent with **K8s CPU Load**. The other three observed pods are classified as no fault. Because only one of the four pods displays that fault, **Rule 1** requires the associated service, checkoutservice, to be classified as **No fault**. No service has three or four pods exhibiting the same fault, so Rule 2 does not apply.

Under Rule 4, the remaining entities are classified as **No fault**. Thus, the isolated fault pattern on checkoutservice-1 does not result in any entity being classified with a fault type.

#### Case 28

來源：2022-03-24／cloudbed-3，時間窗1648117260～1648117800；公開GT索引31，注入entity emailservice。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/28.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/28.txt)。

- emailservice：GT=K8s Network Packet Corruption；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。
- emailservice-0：GT=K8s Network Packet Corruption；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。
- emailservice-1：GT=K8s Network Packet Corruption；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。
- emailservice-2：GT=K8s Network Packet Corruption；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。
- emailservice2-0：GT=K8s Network Packet Corruption；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。
- checkoutservice：GT=No Fault；Luna=Unknown；類型=unknown_fault。摘要未通過已知類別／entity驗證，因此保留原y與mask；不把無效名稱換成No fault。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

| Entity | Classification |
|---|---|
| emailservice | No fault |
| checkoutservice | Unknown |
| emailservice-0 | No fault |
| emailservice-1 | No fault |
| emailservice-2 | No fault |
| emailservice2-0 | No fault |
| node-4 | No fault |

**Reasons:** emailservice-0 and emailservice-1 have weak indications of K8s Network Packet Duplication, while emailservice-2 has an intermittent indication of K8s Network Delay. No fault type is shared by three or more of the four associated pods, so Rule 2 is not met; the observations therefore do not support assigning a fault to emailservice or its pods. The other emailservice pod and node-4 also show no supported fault.

checkoutservice has no associated pod observations, so there is insufficient information to classify it and it is **Unknown** under Rule 5.

#### Case 33

來源：2022-03-24／cloudbed-3，時間窗1648124520～1648125060；公開GT索引37，注入entity emailservice-1。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/33.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/33.txt)。

- emailservice-1：GT=K8s Disk Read IO Load；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

1. **Exact type of each entity**
   - **emailservice:** No fault
   - **checkoutservice:** No fault
   - **emailservice-0:** No fault
   - **emailservice-1:** No fault
   - **emailservice-2:** No fault
   - **emailservice2-0:** No fault

2. **Reasons**
   - Only **emailservice-1** shows a fault characteristic: elevated filesystem reads consistent with **K8s Disk Read IO Load**. The other three pods do not show that fault, so the condition that three or four pods share a fault is not met.
   - Under Rule 1, when only one pod displays fault characteristics, the associated service is classified as **No fault**. Rule 4 then classifies the remaining entities as **No fault**.
   - No second fault type appears across the pods, so there is no basis to classify either service under Rule 3.

#### Case 36

來源：2022-03-24／cloudbed-3，時間窗1648129980～1648130520；公開GT索引40，注入entity paymentservice-1。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/36.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/36.txt)。

- paymentservice-1：GT=K8s Disk Write IO Load；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。
- node-5：GT=No Fault；Luna=Node CPU Climb；類型=label_disagrees_with_ground_truth, false_positive_fault。摘要提供可解析故障類別，原程式會以此類別更新y並令mask=1；因此GT不一致標籤會成為新增監督訊號。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

1. **Exact type of each entity**
   - **paymentservice:** No fault
   - **checkoutservice:** No fault
   - **paymentservice-0:** No fault
   - **paymentservice-1:** No fault
   - **paymentservice-2:** No fault
   - **paymentservice2-0:** No fault
   - **node-5:** Node CPU Climb

2. **Reasons**
   - Only **paymentservice-1** shows a pod-level fault characteristic, a tentative K8s Disk Write IO Load pattern. Because it is the only affected pod among paymentservice’s four pods, Rule 1 classifies the service as **No fault**; the pod-level anomaly does not meet the rule for assigning that fault type to the service and all four pods.
   - **checkoutservice** has no associated pod observations establishing a fault, and the remaining entities are classified as **No fault** under Rule 4.
   - **node-5** has a sustained upward CPU trend, matching **Node CPU Climb**.

#### Case 37

來源：2022-03-24／cloudbed-3，時間窗1648131480～1648132020；公開GT索引41，注入entity currencyservice-1。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/37.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/37.txt)。

- currencyservice-1：GT=K8s CPU Load；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

1. **Entity classifications**
   - **currencyservice:** No fault
   - **frontend:** No fault
   - **checkoutservice:** No fault
   - **currencyservice-0:** No fault
   - **currencyservice-1:** No fault
   - **currencyservice-2:** No fault
   - **currencyservice2-0:** No fault

2. **Reasons**
   - Of the four pods associated with **currencyservice**, only **currencyservice-1** shows a possible fault pattern: **K8s CPU Load**. The other three pods show no fault. Under Rule 1, a fault in only one pod means the service is classified as **No fault**; the isolated pod is also classified as **No fault** under Rule 4.
   - No fault type is consistently displayed by three or four pods, so Rule 2 does not apply.
   - There is no other service-level pattern to identify. Under Rule 4, the remaining entities are classified as **No fault**.

#### Case 48

來源：2022-03-21／cloudbed-2，時間窗1647794520～1647795060；公開GT索引52，注入entity frontend-2。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/48.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/48.txt)。

- frontend-2：GT=K8s Disk Read IO Load；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

##### Entity classifications

| Entity | Type |
|---|---|
| frontend | No fault |
| frontend-0 | No fault |
| frontend-1 | No fault |
| frontend-2 | No fault |
| frontend2-0 | No fault |
| shippingservice | No fault |
| recommendationservice | No fault |
| productcatalogservice | No fault |
| currencyservice | No fault |
| checkoutservice | No fault |

##### Reasons

- **frontend:** Only `frontend-2` shows a fault characteristic—K8s Disk Read IO Load—while `frontend-0` and `frontend-1` show no fault. Under Rule 1, a service with only one faulting pod is classified as **No fault**. Rule 4 classifies the remaining entities as **No fault** once Rule 1 applies.
- **Other entities:** Rule 4 applies to the remaining entities, so they are classified as **No fault**, including services without individual pod observations.

#### Case 55

來源：2022-03-21／cloudbed-2，時間窗1647811080～1647811620；公開GT索引60，注入entity productcatalogservice-0。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/55.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/55.txt)。

- productcatalogservice-0：GT=K8s Disk Write IO Load；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

1. **Entity classifications**

| Entity | Type |
|---|---|
| productcatalogservice | No fault |
| recommendationservice | No fault |
| frontend | No fault |
| checkoutservice | No fault |
| productcatalogservice-0 | No fault |
| productcatalogservice-1 | No fault |
| productcatalogservice-2 | No fault |
| productcatalogservice2-0 | No fault |

2. **Reasons**

Only **productcatalogservice-0** shows a possible fault characteristic: a brief disk-usage spike that most closely matches **K8s Disk Write IO Load**. The other three associated pods show no fault. Since only one of the four pods displays that characteristic, **Rule 1** requires classifying the service as **No fault**, rather than assigning the fault to the service or its pods. **Rule 4** classifies the remaining entities as **No fault**.

#### Case 67

來源：2022-03-21／cloudbed-2，時間窗1647839580～1647840120；公開GT索引75，注入entity shippingservice-2。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/67.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/67.txt)。

- shippingservice-2：GT=K8s Disk Read IO Load；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

| Entity | Classification |
|---|---|
| shippingservice | No fault |
| frontend | No fault |
| checkoutservice | No fault |
| shippingservice-0 | No fault |
| shippingservice-1 | No fault |
| shippingservice-2 | No fault |
| shippingservice2-0 | No fault |

**Reasoning:** Of the four pods associated with `shippingservice`, only `shippingservice-2` shows a fault characteristic: **K8s Disk Read IO Load**. The other three show no fault. Under Rule 1, when only one pod displays fault characteristics, the service is classified as **No fault**. Rule 4 then classifies the remaining entities as **No fault**.

#### Case 79

來源：2022-03-21／cloudbed-2，時間窗1647866160～1647866700；公開GT索引89，注入entity emailservice-0。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/79.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/79.txt)。

- emailservice-0：GT=K8s Network Packet Corruption；Luna=K8s Network Packet Loss；類型=label_disagrees_with_ground_truth, wrong_fault_type。摘要提供可解析故障類別，原程式會以此類別更新y並令mask=1；因此GT不一致標籤會成為新增監督訊號。已逐項核對正式更新。
- checkoutservice：GT=No Fault；Luna=Unknown；類型=unknown_fault。摘要未通過已知類別／entity驗證，因此保留原y與mask；不把無效名稱換成No fault。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

| Entity | Classification |
|---|---|
| emailservice | **No fault** |
| emailservice-0 | **K8s Network Packet Loss** |
| emailservice-1 | **No fault** |
| emailservice-2 | **No fault** |
| emailservice2-0 | **No fault** |
| checkoutservice | **Unknown** |

**Reasoning:** emailservice-0 is the only pod with a sustained, fault-like pattern: elevated transmit packet counts across several points, with other mixed supporting changes. The brief, isolated fluctuation in emailservice2-0 is not enough to count as a second fault characteristic. Under Rule 1, when only one pod displays fault characteristics, the service is classified as **No fault**; the pod’s individual classification remains **K8s Network Packet Loss**. The other emailservice pods are **No fault**. No pod observations are provided for checkoutservice, so it is **Unknown** under Rule 5.

#### Case 90

來源：2022-03-21／cloudbed-2，時間窗1647849840～1647850380；公開GT索引100，注入entity adservice-0。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/90.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/90.txt)。

- adservice-0：GT=K8s Network Packet Loss；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。
- frontend：GT=No Fault；Luna=Unknown；類型=unknown_fault。摘要未通過已知類別／entity驗證，因此保留原y與mask；不把無效名稱換成No fault。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

1. **Exact type of each entity**

| Entity | Type |
|---|---|
| adservice | No fault |
| frontend | Unknown |
| adservice-0 | No fault |
| adservice-1 | No fault |
| adservice-2 | No fault |
| adservice2-0 | No fault |

2. **Reasons**

- The four listed pods are associated with **adservice**. Although **adservice-0** shows characteristics of K8s Network Delay and **adservice-2** shows characteristics of K8s CPU Load, neither fault type appears in three or four pods. The remaining two pods show no fault. Thus, the conditions for assigning a fault type to the service and all four pods are not met; the remaining entities are classified as **No fault**.
- **frontend** has no associated pod observations listed, so there is not enough information to determine its status. It is classified as **Unknown**.

#### Case 93

來源：2022-03-21／cloudbed-2，時間窗1647848460～1647849000；公開GT索引104，注入entity paymentservice。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/93.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/93.txt)。

- paymentservice：GT=K8s Network Packet Duplication；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。
- paymentservice-0：GT=K8s Network Packet Duplication；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。
- paymentservice-1：GT=K8s Network Packet Duplication；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。
- paymentservice-2：GT=K8s Network Packet Duplication；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。
- paymentservice2-0：GT=K8s Network Packet Duplication；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。
- checkoutservice：GT=No Fault；Luna=Unknown；類型=unknown_fault。摘要未通過已知類別／entity驗證，因此保留原y與mask；不把無效名稱換成No fault。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

| Entity | Classification |
|---|---|
| paymentservice | No fault |
| checkoutservice | Unknown |
| paymentservice-0 | No fault |
| paymentservice-1 | No fault |
| paymentservice-2 | No fault |
| paymentservice2-0 | No fault |

**Reasons:** None of the four listed pods shows a sustained fault pattern, so the paymentservice group is classified as **No fault**. No pods or observations are provided for checkoutservice, so there is insufficient information to determine its status; it is **Unknown**.

#### Case 96

來源：2022-03-21／cloudbed-1，時間窗1647796560～1647797100；公開GT索引107，注入entity productcatalogservice-2。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/96.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/96.txt)。

- productcatalogservice-2：GT=K8s Disk Read IO Load；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

##### Entity classifications

| Entity | Type |
|---|---|
| productcatalogservice | No fault |
| productcatalogservice-0 | No fault |
| productcatalogservice-1 | No fault |
| productcatalogservice-2 | No fault |
| productcatalogservice2-0 | No fault |
| recommendationservice | No fault |
| frontend | No fault |
| checkoutservice | No fault |

##### Reasons

`productcatalogservice-2` is the only pod showing a fault characteristic: elevated filesystem reads consistent with **K8s Disk Read IO Load**. The other three associated pods do not show that fault. Under Rule 1, when only one of a service’s four pods displays fault characteristics, the service is classified as **No fault**. No service has three or four pods exhibiting the same fault, so Rule 2 does not apply. Under Rule 4, the remaining entities are classified as **No fault**.

#### Case 104

來源：2022-03-21／cloudbed-1，時間窗1647818520～1647819060；公開GT索引115，注入entity adservice2-0。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/104.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/104.txt)。

- adservice2-0：GT=K8s Disk Read IO Load；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

1. **Exact type of each entity**
   - **adservice:** No fault
   - **frontend:** No fault
   - **adservice-0:** No fault
   - **adservice-1:** No fault
   - **adservice-2:** No fault
   - **adservice2-0:** No fault

2. **Reasons**
   The four listed pods have only one observed fault signature: **adservice2-0** shows characteristics of K8s CPU Load. The other three pods show no fault. Under Rule 1, when only one pod displays fault characteristics, the associated service is classified as **No fault**. Rule 4 then classifies the remaining entities as **No fault**.

#### Case 116

來源：2022-03-21／cloudbed-1，時間窗1647833760～1647834300；公開GT索引127，注入entity frontend。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/116.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/116.txt)。

- frontend：GT=K8s Memory Load；Luna=K8s Disk Write IO Load；類型=label_disagrees_with_ground_truth, wrong_fault_type。摘要提供可解析故障類別，原程式會以此類別更新y並令mask=1；因此GT不一致標籤會成為新增監督訊號。已逐項核對正式更新。
- frontend-0：GT=K8s Memory Load；Luna=K8s Disk Write IO Load；類型=label_disagrees_with_ground_truth, wrong_fault_type。摘要提供可解析故障類別，原程式會以此類別更新y並令mask=1；因此GT不一致標籤會成為新增監督訊號。已逐項核對正式更新。
- frontend-1：GT=K8s Memory Load；Luna=K8s Disk Write IO Load；類型=label_disagrees_with_ground_truth, wrong_fault_type。摘要提供可解析故障類別，原程式會以此類別更新y並令mask=1；因此GT不一致標籤會成為新增監督訊號。已逐項核對正式更新。
- frontend-2：GT=K8s Memory Load；Luna=K8s Disk Write IO Load；類型=label_disagrees_with_ground_truth, wrong_fault_type。摘要提供可解析故障類別，原程式會以此類別更新y並令mask=1；因此GT不一致標籤會成為新增監督訊號。已逐項核對正式更新。
- frontend2-0：GT=K8s Memory Load；Luna=K8s Disk Write IO Load；類型=label_disagrees_with_ground_truth, wrong_fault_type。摘要提供可解析故障類別，原程式會以此類別更新y並令mask=1；因此GT不一致標籤會成為新增監督訊號。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

| Entity | Classification |
|---|---|
| frontend | K8s Disk Write IO Load |
| frontend-0 | K8s Disk Write IO Load |
| frontend-1 | K8s Disk Write IO Load |
| frontend-2 | K8s Disk Write IO Load |
| frontend2-0 | K8s Disk Write IO Load |
| shippingservice | No fault |
| recommendationservice | No fault |
| productcatalogservice | No fault |
| currencyservice | No fault |
| checkoutservice | No fault |

**Reasoning:** Three of the four frontend pods—frontend-1, frontend-2, and frontend2-0—show the same clearest fault characteristic: a disk-write spike consistent with **K8s Disk Write IO Load**. Under Rule 2, that classifies the frontend service and all four associated pods as **K8s Disk Write IO Load**, including frontend-0, whose observations also mention a memory increase. The other services have no supplied pod observations establishing a consistent fault, so under Rule 4 they are classified as **No fault**.

#### Case 117

來源：2022-03-21／cloudbed-1，時間窗1647840900～1647841440；公開GT索引128，注入entity currencyservice。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/117.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/117.txt)。

- currencyservice：GT=K8s Memory Load；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。
- currencyservice-0：GT=K8s Memory Load；Luna=K8s Disk Write IO Load；類型=label_disagrees_with_ground_truth, wrong_fault_type。摘要提供可解析故障類別，原程式會以此類別更新y並令mask=1；因此GT不一致標籤會成為新增監督訊號。已逐項核對正式更新。
- currencyservice-2：GT=K8s Memory Load；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。
- currencyservice2-0：GT=K8s Memory Load；Luna=No fault；類型=label_disagrees_with_ground_truth, missed_fault。摘要提供可解析的No fault，原程式會將y改為0、mask改為1；因此此entity會作為新增的正常監督訊號進入訓練。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

| Entity | Classification |
|---|---|
| currencyservice | No fault |
| currencyservice-0 | No fault |
| currencyservice-1 | No fault |
| currencyservice-2 | No fault |
| currencyservice2-0 | No fault |
| frontend | No fault |
| checkoutservice | No fault |

The four pods associated with `currencyservice` do not show a shared fault: `currencyservice-0` shows disk-write load, `currencyservice-1` shows memory load, and the other two show no fault. No fault type appears in three or four pods, so the service does not meet the rule for assigning a fault to the service and all its pods. The remaining entities are classified as **No fault** under the stated rules.

#### Case 119

來源：2022-03-21／cloudbed-1，時間窗1647845700～1647846240；公開GT索引131，注入entity adservice。

[原摘要](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/summarization/119.txt)；[第三階段原回答](E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/runs/lasrca/luna_20261004/responses/stage-3/119.txt)。

- node-6：GT=No Fault；Luna=Node Memory Consumption；類型=label_disagrees_with_ground_truth, false_positive_fault。摘要提供可解析故障類別，原程式會以此類別更新y並令mask=1；因此GT不一致標籤會成為新增監督訊號。已逐項核對正式更新。

可觀察的流程界線：第三階段負責依子圖關係整合判斷，摘要階段將回答轉為標籤。下方原文可用來判定錯誤是否已出現在第三階段；若無逐階段對照，不進一步歸因到第一／第二階段。

##### 第三階段原回答（完整案例層級證據）

1. **node-6:** Node Memory Consumption

2. Both memory metrics rise together and remain elevated for three consecutive data points, which is consistent with Node Memory Consumption. The negative metric values are unusual and warrant validation, but the observed coordinated increase supports this classification. The service-and-pod rules do not apply because no service or pod entities are provided.



## 附錄C：20案例的正式更新明細

| Case | Entity | GT | LLM | 錯誤類型 | y前→後 | mask前→後 | Update verified |
|---|---|---|---|---|---|---|---|
| 5 | productcatalogservice-1 | K8s Disk Write IO Load | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 14→0 | 0→1 | True |
| 18 | node-4 | No Fault | Node CPU Failure | ['label_disagrees_with_ground_truth', 'false_positive_fault'] | 0→1 | 0→1 | True |
| 19 | node-4 | No Fault | Node CPU Failure | ['label_disagrees_with_ground_truth', 'false_positive_fault'] | 0→1 | 0→1 | True |
| 20 | cartservice-1 | K8s Network Packet Loss | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 10→0 | 0→1 | True |
| 24 | checkoutservice-1 | K8s CPU Load | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 7→0 | 0→1 | True |
| 28 | emailservice | K8s Network Packet Corruption | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 11→0 | 0→1 | True |
| 28 | emailservice-0 | K8s Network Packet Corruption | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 11→0 | 0→1 | True |
| 28 | emailservice-1 | K8s Network Packet Corruption | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 11→0 | 0→1 | True |
| 28 | emailservice-2 | K8s Network Packet Corruption | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 11→0 | 0→1 | True |
| 28 | emailservice2-0 | K8s Network Packet Corruption | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 11→0 | 0→1 | True |
| 28 | checkoutservice | No Fault | Unknown | ['unknown_fault'] | 0→0 | 0→0 | True |
| 33 | emailservice-1 | K8s Disk Read IO Load | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 13→0 | 0→1 | True |
| 36 | paymentservice-1 | K8s Disk Write IO Load | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 14→0 | 0→1 | True |
| 36 | node-5 | No Fault | Node CPU Climb | ['label_disagrees_with_ground_truth', 'false_positive_fault'] | 0→2 | 0→1 | True |
| 37 | currencyservice-1 | K8s CPU Load | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 7→0 | 0→1 | True |
| 48 | frontend-2 | K8s Disk Read IO Load | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 13→0 | 0→1 | True |
| 55 | productcatalogservice-0 | K8s Disk Write IO Load | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 14→0 | 0→1 | True |
| 67 | shippingservice-2 | K8s Disk Read IO Load | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 13→0 | 0→1 | True |
| 79 | emailservice-0 | K8s Network Packet Corruption | K8s Network Packet Loss | ['label_disagrees_with_ground_truth', 'wrong_fault_type'] | 11→10 | 0→1 | True |
| 79 | checkoutservice | No Fault | Unknown | ['unknown_fault'] | 0→0 | 0→0 | True |
| 90 | adservice-0 | K8s Network Packet Loss | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 10→0 | 0→1 | True |
| 90 | frontend | No Fault | Unknown | ['unknown_fault'] | 0→0 | 0→0 | True |
| 93 | paymentservice | K8s Network Packet Duplication | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 12→0 | 0→1 | True |
| 93 | paymentservice-0 | K8s Network Packet Duplication | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 12→0 | 0→1 | True |
| 93 | paymentservice-1 | K8s Network Packet Duplication | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 12→0 | 0→1 | True |
| 93 | paymentservice-2 | K8s Network Packet Duplication | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 12→0 | 0→1 | True |
| 93 | paymentservice2-0 | K8s Network Packet Duplication | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 12→0 | 0→1 | True |
| 93 | checkoutservice | No Fault | Unknown | ['unknown_fault'] | 0→0 | 0→0 | True |
| 96 | productcatalogservice-2 | K8s Disk Read IO Load | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 13→0 | 0→1 | True |
| 104 | adservice2-0 | K8s Disk Read IO Load | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 13→0 | 0→1 | True |
| 116 | frontend | K8s Memory Load | K8s Disk Write IO Load | ['label_disagrees_with_ground_truth', 'wrong_fault_type'] | 8→14 | 0→1 | True |
| 116 | frontend-0 | K8s Memory Load | K8s Disk Write IO Load | ['label_disagrees_with_ground_truth', 'wrong_fault_type'] | 8→14 | 0→1 | True |
| 116 | frontend-1 | K8s Memory Load | K8s Disk Write IO Load | ['label_disagrees_with_ground_truth', 'wrong_fault_type'] | 8→14 | 0→1 | True |
| 116 | frontend-2 | K8s Memory Load | K8s Disk Write IO Load | ['label_disagrees_with_ground_truth', 'wrong_fault_type'] | 8→14 | 0→1 | True |
| 116 | frontend2-0 | K8s Memory Load | K8s Disk Write IO Load | ['label_disagrees_with_ground_truth', 'wrong_fault_type'] | 8→14 | 0→1 | True |
| 117 | currencyservice | K8s Memory Load | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 8→0 | 0→1 | True |
| 117 | currencyservice-0 | K8s Memory Load | K8s Disk Write IO Load | ['label_disagrees_with_ground_truth', 'wrong_fault_type'] | 8→14 | 0→1 | True |
| 117 | currencyservice-2 | K8s Memory Load | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 8→0 | 0→1 | True |
| 117 | currencyservice2-0 | K8s Memory Load | No fault | ['label_disagrees_with_ground_truth', 'missed_fault'] | 8→0 | 0→1 | True |
| 119 | node-6 | No Fault | Node Memory Consumption | ['label_disagrees_with_ground_truth', 'false_positive_fault'] | 0→3 | 0→1 | True |

## 附錄D：前處理逐script內容數量

以下完整匯入全量stage_count_summary.csv，保留family及unit，避免將不同單位或window sizes混加。同stage自身重讀的產物亦列input一次；array_elements是陣列元素，不是故障案例，configuration亦非raw觀測。input/output數量是檔案內容的依賴統計，不是逐次I/O量測。

| Script | Direction | Artifact family | Unit | Count |
|---|---|---|---|---:|
| dao.log_dao | input | config.json | array_elements | 16 |
| dao.log_dao | input | drain3.ini | opaque_files | 1 |
| dao.log_dao | input | istio_words.json | array_elements | 1368 |
| dao.log_dao | input | log_filebeat-testbed-log-service.csv | CSV_records | 79712508 |
| dao.log_dao | input | log_filebeat-testbed-log-service.csv | non_null_non_timestamp_cells | 318583312 |
| dao.log_dao | input | log_patterns.json | array_elements | 141 |
| dao.log_dao | input | metric_setting.json | array_elements | 109 |
| dao.log_dao | input | service_knowledge.json | array_elements | 10 |
| dao.log_dao | output | istio_word_count.csv | CSV_records | 21600 |
| dao.log_dao | output | istio_word_count.csv | non_null_non_timestamp_cells | 148802400 |
| dao.log_dao | output | istio_words.json | array_elements | 1368 |
| dao.log_dao | output | log_patterns.json | array_elements | 141 |
| dao.log_dao | output | log_patterns_count.csv | CSV_records | 21600 |
| dao.log_dao | output | log_patterns_count.csv | non_null_non_timestamp_cells | 21254400 |
| dao.metric_dao | input | config.json | array_elements | 16 |
| dao.metric_dao | input | kpi_cloudbed1_metric_0315.csv | CSV_records | 489717 |
| dao.metric_dao | input | kpi_cloudbed1_metric_0315.csv | non_null_non_timestamp_cells | 1469151 |
| dao.metric_dao | input | kpi_cloudbed1_metric_0319.csv | CSV_records | 492597 |
| dao.metric_dao | input | kpi_cloudbed1_metric_0319.csv | non_null_non_timestamp_cells | 1477791 |
| dao.metric_dao | input | kpi_cloudbed1_metric_0320.csv | CSV_records | 488241 |
| dao.metric_dao | input | kpi_cloudbed1_metric_0320.csv | non_null_non_timestamp_cells | 1464723 |
| dao.metric_dao | input | kpi_cloudbed1_metric_0321.csv | CSV_records | 489618 |
| dao.metric_dao | input | kpi_cloudbed1_metric_0321.csv | non_null_non_timestamp_cells | 1468854 |
| dao.metric_dao | input | kpi_cloudbed1_metric_0324.csv | CSV_records | 478656 |
| dao.metric_dao | input | kpi_cloudbed1_metric_0324.csv | non_null_non_timestamp_cells | 1435968 |
| dao.metric_dao | input | kpi_cloudbed2_metric_0319.csv | CSV_records | 491616 |
| dao.metric_dao | input | kpi_cloudbed2_metric_0319.csv | non_null_non_timestamp_cells | 1474848 |
| dao.metric_dao | input | kpi_cloudbed2_metric_0320.csv | CSV_records | 490176 |
| dao.metric_dao | input | kpi_cloudbed2_metric_0320.csv | non_null_non_timestamp_cells | 1470528 |
| dao.metric_dao | input | kpi_cloudbed2_metric_0321.csv | CSV_records | 490176 |
| dao.metric_dao | input | kpi_cloudbed2_metric_0321.csv | non_null_non_timestamp_cells | 1470528 |
| dao.metric_dao | input | kpi_cloudbed2_metric_0324.csv | CSV_records | 478656 |
| dao.metric_dao | input | kpi_cloudbed2_metric_0324.csv | non_null_non_timestamp_cells | 1435968 |
| dao.metric_dao | input | kpi_cloudbed2_metric_0325.csv | CSV_records | 487296 |
| dao.metric_dao | input | kpi_cloudbed2_metric_0325.csv | non_null_non_timestamp_cells | 1461888 |
| dao.metric_dao | input | kpi_cloudbed3_metric_0319.csv | CSV_records | 487344 |
| dao.metric_dao | input | kpi_cloudbed3_metric_0319.csv | non_null_non_timestamp_cells | 1462032 |
| dao.metric_dao | input | kpi_cloudbed3_metric_0320.csv | CSV_records | 486336 |
| dao.metric_dao | input | kpi_cloudbed3_metric_0320.csv | non_null_non_timestamp_cells | 1459008 |
| dao.metric_dao | input | kpi_cloudbed3_metric_0321.csv | CSV_records | 489096 |
| dao.metric_dao | input | kpi_cloudbed3_metric_0321.csv | non_null_non_timestamp_cells | 1467288 |
| dao.metric_dao | input | kpi_cloudbed3_metric_0324.csv | CSV_records | 478656 |
| dao.metric_dao | input | kpi_cloudbed3_metric_0324.csv | non_null_non_timestamp_cells | 1435968 |
| dao.metric_dao | input | kpi_cloudbed3_metric_0325.csv | CSV_records | 486096 |
| dao.metric_dao | input | kpi_cloudbed3_metric_0325.csv | non_null_non_timestamp_cells | 1458288 |
| dao.metric_dao | input | kpi_container_cpu_cfs_throttled_periods.csv | CSV_records | 863768 |
| dao.metric_dao | input | kpi_container_cpu_cfs_throttled_periods.csv | non_null_non_timestamp_cells | 2591304 |
| dao.metric_dao | input | kpi_container_cpu_cfs_throttled_seconds.csv | CSV_records | 863802 |
| dao.metric_dao | input | kpi_container_cpu_cfs_throttled_seconds.csv | non_null_non_timestamp_cells | 2591406 |
| dao.metric_dao | input | kpi_container_cpu_system_seconds.csv | CSV_records | 863876 |
| dao.metric_dao | input | kpi_container_cpu_system_seconds.csv | non_null_non_timestamp_cells | 2591628 |
| dao.metric_dao | input | kpi_container_cpu_usage_seconds.csv | CSV_records | 863864 |
| dao.metric_dao | input | kpi_container_cpu_usage_seconds.csv | non_null_non_timestamp_cells | 2591592 |
| dao.metric_dao | input | kpi_container_cpu_user_seconds.csv | CSV_records | 863886 |
| dao.metric_dao | input | kpi_container_cpu_user_seconds.csv | non_null_non_timestamp_cells | 2591658 |
| dao.metric_dao | input | kpi_container_fs_inodes.csv | CSV_records | 863886 |
| dao.metric_dao | input | kpi_container_fs_inodes.csv | non_null_non_timestamp_cells | 2591658 |
| dao.metric_dao | input | kpi_container_fs_reads_MB.csv | CSV_records | 827955 |
| dao.metric_dao | input | kpi_container_fs_reads_MB.csv | non_null_non_timestamp_cells | 2483865 |
| dao.metric_dao | input | kpi_container_fs_usage_MB.csv | CSV_records | 863886 |
| dao.metric_dao | input | kpi_container_fs_usage_MB.csv | non_null_non_timestamp_cells | 2591658 |
| dao.metric_dao | input | kpi_container_fs_writes_MB.csv | CSV_records | 830355 |
| dao.metric_dao | input | kpi_container_fs_writes_MB.csv | non_null_non_timestamp_cells | 2491065 |
| dao.metric_dao | input | kpi_container_memory_cache.csv | CSV_records | 863886 |
| dao.metric_dao | input | kpi_container_memory_cache.csv | non_null_non_timestamp_cells | 2591658 |
| dao.metric_dao | input | kpi_container_memory_mapped_file.csv | CSV_records | 863886 |
| dao.metric_dao | input | kpi_container_memory_mapped_file.csv | non_null_non_timestamp_cells | 2591658 |
| dao.metric_dao | input | kpi_container_memory_rss.csv | CSV_records | 863886 |
| dao.metric_dao | input | kpi_container_memory_rss.csv | non_null_non_timestamp_cells | 2591658 |
| dao.metric_dao | input | kpi_container_memory_usage_MB.csv | CSV_records | 863886 |
| dao.metric_dao | input | kpi_container_memory_usage_MB.csv | non_null_non_timestamp_cells | 2591658 |
| dao.metric_dao | input | kpi_container_memory_working_set_MB.csv | CSV_records | 863886 |
| dao.metric_dao | input | kpi_container_memory_working_set_MB.csv | non_null_non_timestamp_cells | 2591658 |
| dao.metric_dao | input | kpi_container_network_receive_MB.csv | CSV_records | 907013 |
| dao.metric_dao | input | kpi_container_network_receive_MB.csv | non_null_non_timestamp_cells | 2721039 |
| dao.metric_dao | input | kpi_container_network_receive_packets.csv | CSV_records | 907013 |
| dao.metric_dao | input | kpi_container_network_receive_packets.csv | non_null_non_timestamp_cells | 2721039 |
| dao.metric_dao | input | kpi_container_network_transmit_MB.csv | CSV_records | 907013 |
| dao.metric_dao | input | kpi_container_network_transmit_MB.csv | non_null_non_timestamp_cells | 2721039 |
| dao.metric_dao | input | kpi_container_network_transmit_packets.csv | CSV_records | 907013 |
| dao.metric_dao | input | kpi_container_network_transmit_packets.csv | non_null_non_timestamp_cells | 2721039 |
| dao.metric_dao | input | kpi_container_threads.csv | CSV_records | 863886 |
| dao.metric_dao | input | kpi_container_threads.csv | non_null_non_timestamp_cells | 2591658 |
| dao.metric_dao | input | kpi_istio_request_bytes.csv | CSV_records | 6428883 |
| dao.metric_dao | input | kpi_istio_request_bytes.csv | non_null_non_timestamp_cells | 19286649 |
| dao.metric_dao | input | kpi_istio_request_duration_milliseconds.csv | CSV_records | 6385743 |
| dao.metric_dao | input | kpi_istio_request_duration_milliseconds.csv | non_null_non_timestamp_cells | 19157229 |
| dao.metric_dao | input | kpi_istio_request_messages.csv | CSV_records | 2606009 |
| dao.metric_dao | input | kpi_istio_request_messages.csv | non_null_non_timestamp_cells | 7818027 |
| dao.metric_dao | input | kpi_istio_requests.csv | CSV_records | 6385743 |
| dao.metric_dao | input | kpi_istio_requests.csv | non_null_non_timestamp_cells | 19157229 |
| dao.metric_dao | input | kpi_istio_response_bytes.csv | CSV_records | 6342543 |
| dao.metric_dao | input | kpi_istio_response_bytes.csv | non_null_non_timestamp_cells | 19027629 |
| dao.metric_dao | input | kpi_istio_response_messages.csv | CSV_records | 2590889 |
| dao.metric_dao | input | kpi_istio_response_messages.csv | non_null_non_timestamp_cells | 7772667 |
| dao.metric_dao | input | metric_service.csv | CSV_records | 235560 |
| dao.metric_dao | input | metric_service.csv | non_null_non_timestamp_cells | 1177800 |
| dao.metric_dao | input | metric_setting.json | array_elements | 109 |
| dao.metric_dao | input | service_knowledge.json | array_elements | 10 |
| dao.metric_dao | output | adservice-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | adservice-0.csv | non_null_non_timestamp_cells | 624349 |
| dao.metric_dao | output | adservice-1.csv | CSV_records | 43200 |
| dao.metric_dao | output | adservice-1.csv | non_null_non_timestamp_cells | 624355 |
| dao.metric_dao | output | adservice-2.csv | CSV_records | 43200 |
| dao.metric_dao | output | adservice-2.csv | non_null_non_timestamp_cells | 619274 |
| dao.metric_dao | output | adservice.csv | CSV_records | 21600 |
| dao.metric_dao | output | adservice.csv | non_null_non_timestamp_cells | 171360 |
| dao.metric_dao | output | adservice2-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | adservice2-0.csv | non_null_non_timestamp_cells | 624211 |
| dao.metric_dao | output | cartservice-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | cartservice-0.csv | non_null_non_timestamp_cells | 530086 |
| dao.metric_dao | output | cartservice-1.csv | CSV_records | 43200 |
| dao.metric_dao | output | cartservice-1.csv | non_null_non_timestamp_cells | 529608 |
| dao.metric_dao | output | cartservice-2.csv | CSV_records | 43200 |
| dao.metric_dao | output | cartservice-2.csv | non_null_non_timestamp_cells | 523283 |
| dao.metric_dao | output | cartservice.csv | CSV_records | 21600 |
| dao.metric_dao | output | cartservice.csv | non_null_non_timestamp_cells | 85584 |
| dao.metric_dao | output | cartservice2-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | cartservice2-0.csv | non_null_non_timestamp_cells | 528006 |
| dao.metric_dao | output | checkoutservice-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | checkoutservice-0.csv | non_null_non_timestamp_cells | 666884 |
| dao.metric_dao | output | checkoutservice-1.csv | CSV_records | 43200 |
| dao.metric_dao | output | checkoutservice-1.csv | non_null_non_timestamp_cells | 666968 |
| dao.metric_dao | output | checkoutservice-2.csv | CSV_records | 43200 |
| dao.metric_dao | output | checkoutservice-2.csv | non_null_non_timestamp_cells | 666920 |
| dao.metric_dao | output | checkoutservice.csv | CSV_records | 21600 |
| dao.metric_dao | output | checkoutservice.csv | non_null_non_timestamp_cells | 85652 |
| dao.metric_dao | output | checkoutservice2-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | checkoutservice2-0.csv | non_null_non_timestamp_cells | 666949 |
| dao.metric_dao | output | currencyservice-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | currencyservice-0.csv | non_null_non_timestamp_cells | 538666 |
| dao.metric_dao | output | currencyservice-1.csv | CSV_records | 43200 |
| dao.metric_dao | output | currencyservice-1.csv | non_null_non_timestamp_cells | 534520 |
| dao.metric_dao | output | currencyservice-2.csv | CSV_records | 43200 |
| dao.metric_dao | output | currencyservice-2.csv | non_null_non_timestamp_cells | 534539 |
| dao.metric_dao | output | currencyservice.csv | CSV_records | 21600 |
| dao.metric_dao | output | currencyservice.csv | non_null_non_timestamp_cells | 85680 |
| dao.metric_dao | output | currencyservice2-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | currencyservice2-0.csv | non_null_non_timestamp_cells | 538596 |
| dao.metric_dao | output | emailservice-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | emailservice-0.csv | non_null_non_timestamp_cells | 624290 |
| dao.metric_dao | output | emailservice-1.csv | CSV_records | 43200 |
| dao.metric_dao | output | emailservice-1.csv | non_null_non_timestamp_cells | 624350 |
| dao.metric_dao | output | emailservice-2.csv | CSV_records | 43200 |
| dao.metric_dao | output | emailservice-2.csv | non_null_non_timestamp_cells | 624275 |
| dao.metric_dao | output | emailservice.csv | CSV_records | 21600 |
| dao.metric_dao | output | emailservice.csv | non_null_non_timestamp_cells | 85680 |
| dao.metric_dao | output | emailservice2-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | emailservice2-0.csv | non_null_non_timestamp_cells | 624303 |
| dao.metric_dao | output | frontend-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | frontend-0.csv | non_null_non_timestamp_cells | 624065 |
| dao.metric_dao | output | frontend-1.csv | CSV_records | 43200 |
| dao.metric_dao | output | frontend-1.csv | non_null_non_timestamp_cells | 624061 |
| dao.metric_dao | output | frontend-2.csv | CSV_records | 43200 |
| dao.metric_dao | output | frontend-2.csv | non_null_non_timestamp_cells | 624067 |
| dao.metric_dao | output | frontend.csv | CSV_records | 21600 |
| dao.metric_dao | output | frontend.csv | non_null_non_timestamp_cells | 85608 |
| dao.metric_dao | output | frontend2-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | frontend2-0.csv | non_null_non_timestamp_cells | 624034 |
| dao.metric_dao | output | node-1.csv | CSV_records | 21600 |
| dao.metric_dao | output | node-1.csv | non_null_non_timestamp_cells | 483840 |
| dao.metric_dao | output | node-2.csv | CSV_records | 21600 |
| dao.metric_dao | output | node-2.csv | non_null_non_timestamp_cells | 483600 |
| dao.metric_dao | output | node-3.csv | CSV_records | 21600 |
| dao.metric_dao | output | node-3.csv | non_null_non_timestamp_cells | 483840 |
| dao.metric_dao | output | node-4.csv | CSV_records | 21600 |
| dao.metric_dao | output | node-4.csv | non_null_non_timestamp_cells | 479343 |
| dao.metric_dao | output | node-5.csv | CSV_records | 21600 |
| dao.metric_dao | output | node-5.csv | non_null_non_timestamp_cells | 482688 |
| dao.metric_dao | output | node-6.csv | CSV_records | 21600 |
| dao.metric_dao | output | node-6.csv | non_null_non_timestamp_cells | 483840 |
| dao.metric_dao | output | paymentservice-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | paymentservice-0.csv | non_null_non_timestamp_cells | 538684 |
| dao.metric_dao | output | paymentservice-1.csv | CSV_records | 43200 |
| dao.metric_dao | output | paymentservice-1.csv | non_null_non_timestamp_cells | 529720 |
| dao.metric_dao | output | paymentservice-2.csv | CSV_records | 43200 |
| dao.metric_dao | output | paymentservice-2.csv | non_null_non_timestamp_cells | 537286 |
| dao.metric_dao | output | paymentservice.csv | CSV_records | 21600 |
| dao.metric_dao | output | paymentservice.csv | non_null_non_timestamp_cells | 85680 |
| dao.metric_dao | output | paymentservice2-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | paymentservice2-0.csv | non_null_non_timestamp_cells | 537236 |
| dao.metric_dao | output | productcatalogservice-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | productcatalogservice-0.csv | non_null_non_timestamp_cells | 624168 |
| dao.metric_dao | output | productcatalogservice-1.csv | CSV_records | 43200 |
| dao.metric_dao | output | productcatalogservice-1.csv | non_null_non_timestamp_cells | 624194 |
| dao.metric_dao | output | productcatalogservice-2.csv | CSV_records | 43200 |
| dao.metric_dao | output | productcatalogservice-2.csv | non_null_non_timestamp_cells | 624229 |
| dao.metric_dao | output | productcatalogservice.csv | CSV_records | 21600 |
| dao.metric_dao | output | productcatalogservice.csv | non_null_non_timestamp_cells | 85644 |
| dao.metric_dao | output | productcatalogservice2-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | productcatalogservice2-0.csv | non_null_non_timestamp_cells | 624186 |
| dao.metric_dao | output | recommendationservice-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | recommendationservice-0.csv | non_null_non_timestamp_cells | 667006 |
| dao.metric_dao | output | recommendationservice-1.csv | CSV_records | 43200 |
| dao.metric_dao | output | recommendationservice-1.csv | non_null_non_timestamp_cells | 667019 |
| dao.metric_dao | output | recommendationservice-2.csv | CSV_records | 43200 |
| dao.metric_dao | output | recommendationservice-2.csv | non_null_non_timestamp_cells | 667027 |
| dao.metric_dao | output | recommendationservice.csv | CSV_records | 21600 |
| dao.metric_dao | output | recommendationservice.csv | non_null_non_timestamp_cells | 85672 |
| dao.metric_dao | output | recommendationservice2-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | recommendationservice2-0.csv | non_null_non_timestamp_cells | 666987 |
| dao.metric_dao | output | shippingservice-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | shippingservice-0.csv | non_null_non_timestamp_cells | 624320 |
| dao.metric_dao | output | shippingservice-1.csv | CSV_records | 43200 |
| dao.metric_dao | output | shippingservice-1.csv | non_null_non_timestamp_cells | 624335 |
| dao.metric_dao | output | shippingservice-2.csv | CSV_records | 43200 |
| dao.metric_dao | output | shippingservice-2.csv | non_null_non_timestamp_cells | 624282 |
| dao.metric_dao | output | shippingservice.csv | CSV_records | 21600 |
| dao.metric_dao | output | shippingservice.csv | non_null_non_timestamp_cells | 85680 |
| dao.metric_dao | output | shippingservice2-0.csv | CSV_records | 43200 |
| dao.metric_dao | output | shippingservice2-0.csv | non_null_non_timestamp_cells | 624268 |
| dao.topology_dao | input | config.json | array_elements | 16 |
| dao.topology_dao | input | edge_index.pkl | stored_directed_edges | 2460 |
| dao.topology_dao | input | metric_setting.json | array_elements | 109 |
| dao.topology_dao | input | service_knowledge.json | array_elements | 10 |
| dao.topology_dao | output | edge_index.pkl | stored_directed_edges | 2460 |
| dao.trace_dao | input | config.json | array_elements | 16 |
| dao.trace_dao | input | metric_setting.json | array_elements | 109 |
| dao.trace_dao | input | service_knowledge.json | array_elements | 10 |
| dao.trace_dao | input | span_features.csv | CSV_records | 21600 |
| dao.trace_dao | input | span_features.csv | non_null_non_timestamp_cells | 5184000 |
| dao.trace_dao | input | trace_jaeger-span.csv | CSV_records | 135795577 |
| dao.trace_dao | input | trace_jaeger-span.csv | non_null_non_timestamp_cells | 1071886852 |
| dao.trace_dao | input | trace_patterns.json | array_elements | 100 |
| dao.trace_dao | output | span_features.csv | CSV_records | 21600 |
| dao.trace_dao | output | span_features.csv | non_null_non_timestamp_cells | 5184000 |
| dao.trace_dao | output | trace_patterns.json | array_elements | 100 |
| service.dataset_generator | input | adservice-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | adservice-0.csv | non_null_non_timestamp_cells | 624349 |
| service.dataset_generator | input | adservice-1.csv | CSV_records | 43200 |
| service.dataset_generator | input | adservice-1.csv | non_null_non_timestamp_cells | 624355 |
| service.dataset_generator | input | adservice-2.csv | CSV_records | 43200 |
| service.dataset_generator | input | adservice-2.csv | non_null_non_timestamp_cells | 619274 |
| service.dataset_generator | input | adservice.csv | CSV_records | 21600 |
| service.dataset_generator | input | adservice.csv | non_null_non_timestamp_cells | 171360 |
| service.dataset_generator | input | adservice2-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | adservice2-0.csv | non_null_non_timestamp_cells | 624211 |
| service.dataset_generator | input | all_log.pkl | processed_feature_cells | 15552000 |
| service.dataset_generator | input | all_log.pkl | processed_observation_rows | 1728000 |
| service.dataset_generator | input | all_metric.pkl | processed_feature_cells | 31622400 |
| service.dataset_generator | input | all_metric.pkl | processed_observation_rows | 2073600 |
| service.dataset_generator | input | all_trace.pkl | processed_feature_cells | 10368000 |
| service.dataset_generator | input | all_trace.pkl | processed_observation_rows | 1728000 |
| service.dataset_generator | input | cartservice-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | cartservice-0.csv | non_null_non_timestamp_cells | 530086 |
| service.dataset_generator | input | cartservice-1.csv | CSV_records | 43200 |
| service.dataset_generator | input | cartservice-1.csv | non_null_non_timestamp_cells | 529608 |
| service.dataset_generator | input | cartservice-2.csv | CSV_records | 43200 |
| service.dataset_generator | input | cartservice-2.csv | non_null_non_timestamp_cells | 523283 |
| service.dataset_generator | input | cartservice.csv | CSV_records | 21600 |
| service.dataset_generator | input | cartservice.csv | non_null_non_timestamp_cells | 85584 |
| service.dataset_generator | input | cartservice2-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | cartservice2-0.csv | non_null_non_timestamp_cells | 528006 |
| service.dataset_generator | input | checkoutservice-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | checkoutservice-0.csv | non_null_non_timestamp_cells | 666884 |
| service.dataset_generator | input | checkoutservice-1.csv | CSV_records | 43200 |
| service.dataset_generator | input | checkoutservice-1.csv | non_null_non_timestamp_cells | 666968 |
| service.dataset_generator | input | checkoutservice-2.csv | CSV_records | 43200 |
| service.dataset_generator | input | checkoutservice-2.csv | non_null_non_timestamp_cells | 666920 |
| service.dataset_generator | input | checkoutservice.csv | CSV_records | 21600 |
| service.dataset_generator | input | checkoutservice.csv | non_null_non_timestamp_cells | 85652 |
| service.dataset_generator | input | checkoutservice2-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | checkoutservice2-0.csv | non_null_non_timestamp_cells | 666949 |
| service.dataset_generator | input | config.json | array_elements | 16 |
| service.dataset_generator | input | currencyservice-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | currencyservice-0.csv | non_null_non_timestamp_cells | 538666 |
| service.dataset_generator | input | currencyservice-1.csv | CSV_records | 43200 |
| service.dataset_generator | input | currencyservice-1.csv | non_null_non_timestamp_cells | 534520 |
| service.dataset_generator | input | currencyservice-2.csv | CSV_records | 43200 |
| service.dataset_generator | input | currencyservice-2.csv | non_null_non_timestamp_cells | 534539 |
| service.dataset_generator | input | currencyservice.csv | CSV_records | 21600 |
| service.dataset_generator | input | currencyservice.csv | non_null_non_timestamp_cells | 85680 |
| service.dataset_generator | input | currencyservice2-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | currencyservice2-0.csv | non_null_non_timestamp_cells | 538596 |
| service.dataset_generator | input | emailservice-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | emailservice-0.csv | non_null_non_timestamp_cells | 624290 |
| service.dataset_generator | input | emailservice-1.csv | CSV_records | 43200 |
| service.dataset_generator | input | emailservice-1.csv | non_null_non_timestamp_cells | 624350 |
| service.dataset_generator | input | emailservice-2.csv | CSV_records | 43200 |
| service.dataset_generator | input | emailservice-2.csv | non_null_non_timestamp_cells | 624275 |
| service.dataset_generator | input | emailservice.csv | CSV_records | 21600 |
| service.dataset_generator | input | emailservice.csv | non_null_non_timestamp_cells | 85680 |
| service.dataset_generator | input | emailservice2-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | emailservice2-0.csv | non_null_non_timestamp_cells | 624303 |
| service.dataset_generator | input | ent_edge_index.pkl | array_elements | 14760 |
| service.dataset_generator | input | frontend-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | frontend-0.csv | non_null_non_timestamp_cells | 624065 |
| service.dataset_generator | input | frontend-1.csv | CSV_records | 43200 |
| service.dataset_generator | input | frontend-1.csv | non_null_non_timestamp_cells | 624061 |
| service.dataset_generator | input | frontend-2.csv | CSV_records | 43200 |
| service.dataset_generator | input | frontend-2.csv | non_null_non_timestamp_cells | 624067 |
| service.dataset_generator | input | frontend.csv | CSV_records | 21600 |
| service.dataset_generator | input | frontend.csv | non_null_non_timestamp_cells | 85608 |
| service.dataset_generator | input | frontend2-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | frontend2-0.csv | non_null_non_timestamp_cells | 624034 |
| service.dataset_generator | input | metric_setting.json | array_elements | 109 |
| service.dataset_generator | input | node-1.csv | CSV_records | 21600 |
| service.dataset_generator | input | node-1.csv | non_null_non_timestamp_cells | 483840 |
| service.dataset_generator | input | node-2.csv | CSV_records | 21600 |
| service.dataset_generator | input | node-2.csv | non_null_non_timestamp_cells | 483600 |
| service.dataset_generator | input | node-3.csv | CSV_records | 21600 |
| service.dataset_generator | input | node-3.csv | non_null_non_timestamp_cells | 483840 |
| service.dataset_generator | input | node-4.csv | CSV_records | 21600 |
| service.dataset_generator | input | node-4.csv | non_null_non_timestamp_cells | 479343 |
| service.dataset_generator | input | node-5.csv | CSV_records | 21600 |
| service.dataset_generator | input | node-5.csv | non_null_non_timestamp_cells | 482688 |
| service.dataset_generator | input | node-6.csv | CSV_records | 21600 |
| service.dataset_generator | input | node-6.csv | non_null_non_timestamp_cells | 483840 |
| service.dataset_generator | input | paymentservice-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | paymentservice-0.csv | non_null_non_timestamp_cells | 538684 |
| service.dataset_generator | input | paymentservice-1.csv | CSV_records | 43200 |
| service.dataset_generator | input | paymentservice-1.csv | non_null_non_timestamp_cells | 529720 |
| service.dataset_generator | input | paymentservice-2.csv | CSV_records | 43200 |
| service.dataset_generator | input | paymentservice-2.csv | non_null_non_timestamp_cells | 537286 |
| service.dataset_generator | input | paymentservice.csv | CSV_records | 21600 |
| service.dataset_generator | input | paymentservice.csv | non_null_non_timestamp_cells | 85680 |
| service.dataset_generator | input | paymentservice2-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | paymentservice2-0.csv | non_null_non_timestamp_cells | 537236 |
| service.dataset_generator | input | productcatalogservice-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | productcatalogservice-0.csv | non_null_non_timestamp_cells | 624168 |
| service.dataset_generator | input | productcatalogservice-1.csv | CSV_records | 43200 |
| service.dataset_generator | input | productcatalogservice-1.csv | non_null_non_timestamp_cells | 624194 |
| service.dataset_generator | input | productcatalogservice-2.csv | CSV_records | 43200 |
| service.dataset_generator | input | productcatalogservice-2.csv | non_null_non_timestamp_cells | 624229 |
| service.dataset_generator | input | productcatalogservice.csv | CSV_records | 21600 |
| service.dataset_generator | input | productcatalogservice.csv | non_null_non_timestamp_cells | 85644 |
| service.dataset_generator | input | productcatalogservice2-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | productcatalogservice2-0.csv | non_null_non_timestamp_cells | 624186 |
| service.dataset_generator | input | recommendationservice-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | recommendationservice-0.csv | non_null_non_timestamp_cells | 667006 |
| service.dataset_generator | input | recommendationservice-1.csv | CSV_records | 43200 |
| service.dataset_generator | input | recommendationservice-1.csv | non_null_non_timestamp_cells | 667019 |
| service.dataset_generator | input | recommendationservice-2.csv | CSV_records | 43200 |
| service.dataset_generator | input | recommendationservice-2.csv | non_null_non_timestamp_cells | 667027 |
| service.dataset_generator | input | recommendationservice.csv | CSV_records | 21600 |
| service.dataset_generator | input | recommendationservice.csv | non_null_non_timestamp_cells | 85672 |
| service.dataset_generator | input | recommendationservice2-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | recommendationservice2-0.csv | non_null_non_timestamp_cells | 666987 |
| service.dataset_generator | input | service_knowledge.json | array_elements | 10 |
| service.dataset_generator | input | shippingservice-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | shippingservice-0.csv | non_null_non_timestamp_cells | 624320 |
| service.dataset_generator | input | shippingservice-1.csv | CSV_records | 43200 |
| service.dataset_generator | input | shippingservice-1.csv | non_null_non_timestamp_cells | 624335 |
| service.dataset_generator | input | shippingservice-2.csv | CSV_records | 43200 |
| service.dataset_generator | input | shippingservice-2.csv | non_null_non_timestamp_cells | 624282 |
| service.dataset_generator | input | shippingservice.csv | CSV_records | 21600 |
| service.dataset_generator | input | shippingservice.csv | non_null_non_timestamp_cells | 85680 |
| service.dataset_generator | input | shippingservice2-0.csv | CSV_records | 43200 |
| service.dataset_generator | input | shippingservice2-0.csv | non_null_non_timestamp_cells | 624268 |
| service.dataset_generator | output | metric_trace_log.pkl | array_elements | 182 |
| service.dataset_generator | output | metric_trace_log.pkl | processed_feature_cells | 44582400 |
| service.dataset_generator | output | metric_trace_log.pkl | processed_observation_rows | 1209600 |
| service.dataset_generator | output | metric_trace_log.pkl | raw_feature_cells | 44582400 |
| service.dataset_generator | output | metric_trace_log.pkl | raw_observation_rows | 1209600 |
| service.dataset_generator | output | metric_trace_log.pkl | stored_directed_edges | 7380 |
| service.ent_edge_index_generator | input | config.json | array_elements | 16 |
| service.ent_edge_index_generator | input | edge_index.pkl | stored_directed_edges | 2460 |
| service.ent_edge_index_generator | input | metric_setting.json | array_elements | 109 |
| service.ent_edge_index_generator | input | service_knowledge.json | array_elements | 10 |
| service.ent_edge_index_generator | output | ent_edge_index.pkl | array_elements | 14760 |
| service.log_generator | input | config.json | array_elements | 16 |
| service.log_generator | input | container_log_selected_patterns.json | array_elements | 6 |
| service.log_generator | input | istio_log_tf_idf_statistic.json | array_elements | 4838400 |
| service.log_generator | input | istio_selected_words.json | array_elements | 3 |
| service.log_generator | input | istio_word_count.csv | CSV_records | 21600 |
| service.log_generator | input | istio_word_count.csv | non_null_non_timestamp_cells | 148802400 |
| service.log_generator | input | istio_words.json | array_elements | 1368 |
| service.log_generator | input | log_patterns.json | array_elements | 141 |
| service.log_generator | input | log_patterns_count.csv | CSV_records | 21600 |
| service.log_generator | input | log_patterns_count.csv | non_null_non_timestamp_cells | 21254400 |
| service.log_generator | input | metric_setting.json | array_elements | 109 |
| service.log_generator | input | service_knowledge.json | array_elements | 10 |
| service.log_generator | input | z_scored_container_log_features.pkl | processed_feature_cells | 10368000 |
| service.log_generator | input | z_scored_container_log_features.pkl | processed_observation_rows | 43200 |
| service.log_generator | input | z_scored_istio_features.pkl | processed_feature_cells | 5184000 |
| service.log_generator | input | z_scored_istio_features.pkl | processed_observation_rows | 43200 |
| service.log_generator | output | all_log.pkl | processed_feature_cells | 15552000 |
| service.log_generator | output | all_log.pkl | processed_observation_rows | 1728000 |
| service.log_generator | output | container_log_selected_patterns.json | array_elements | 6 |
| service.log_generator | output | istio_log_tf_idf_statistic.json | array_elements | 4838400 |
| service.log_generator | output | istio_selected_words.json | array_elements | 3 |
| service.log_generator | output | z_scored_container_log_features.pkl | processed_feature_cells | 10368000 |
| service.log_generator | output | z_scored_container_log_features.pkl | processed_observation_rows | 43200 |
| service.log_generator | output | z_scored_istio_features.pkl | processed_feature_cells | 5184000 |
| service.log_generator | output | z_scored_istio_features.pkl | processed_observation_rows | 43200 |
| service.metric_generator | input | adservice-0.csv | CSV_records | 43200 |
| service.metric_generator | input | adservice-0.csv | non_null_non_timestamp_cells | 624349 |
| service.metric_generator | input | adservice-1.csv | CSV_records | 43200 |
| service.metric_generator | input | adservice-1.csv | non_null_non_timestamp_cells | 624355 |
| service.metric_generator | input | adservice-2.csv | CSV_records | 43200 |
| service.metric_generator | input | adservice-2.csv | non_null_non_timestamp_cells | 619274 |
| service.metric_generator | input | adservice.csv | CSV_records | 21600 |
| service.metric_generator | input | adservice.csv | non_null_non_timestamp_cells | 171360 |
| service.metric_generator | input | adservice2-0.csv | CSV_records | 43200 |
| service.metric_generator | input | adservice2-0.csv | non_null_non_timestamp_cells | 624211 |
| service.metric_generator | input | all_metric.pkl | processed_feature_cells | 31622400 |
| service.metric_generator | input | all_metric.pkl | processed_observation_rows | 2073600 |
| service.metric_generator | input | cartservice-0.csv | CSV_records | 43200 |
| service.metric_generator | input | cartservice-0.csv | non_null_non_timestamp_cells | 530086 |
| service.metric_generator | input | cartservice-1.csv | CSV_records | 43200 |
| service.metric_generator | input | cartservice-1.csv | non_null_non_timestamp_cells | 529608 |
| service.metric_generator | input | cartservice-2.csv | CSV_records | 43200 |
| service.metric_generator | input | cartservice-2.csv | non_null_non_timestamp_cells | 523283 |
| service.metric_generator | input | cartservice.csv | CSV_records | 21600 |
| service.metric_generator | input | cartservice.csv | non_null_non_timestamp_cells | 85584 |
| service.metric_generator | input | cartservice2-0.csv | CSV_records | 43200 |
| service.metric_generator | input | cartservice2-0.csv | non_null_non_timestamp_cells | 528006 |
| service.metric_generator | input | checkoutservice-0.csv | CSV_records | 43200 |
| service.metric_generator | input | checkoutservice-0.csv | non_null_non_timestamp_cells | 666884 |
| service.metric_generator | input | checkoutservice-1.csv | CSV_records | 43200 |
| service.metric_generator | input | checkoutservice-1.csv | non_null_non_timestamp_cells | 666968 |
| service.metric_generator | input | checkoutservice-2.csv | CSV_records | 43200 |
| service.metric_generator | input | checkoutservice-2.csv | non_null_non_timestamp_cells | 666920 |
| service.metric_generator | input | checkoutservice.csv | CSV_records | 21600 |
| service.metric_generator | input | checkoutservice.csv | non_null_non_timestamp_cells | 85652 |
| service.metric_generator | input | checkoutservice2-0.csv | CSV_records | 43200 |
| service.metric_generator | input | checkoutservice2-0.csv | non_null_non_timestamp_cells | 666949 |
| service.metric_generator | input | config.json | array_elements | 16 |
| service.metric_generator | input | currencyservice-0.csv | CSV_records | 43200 |
| service.metric_generator | input | currencyservice-0.csv | non_null_non_timestamp_cells | 538666 |
| service.metric_generator | input | currencyservice-1.csv | CSV_records | 43200 |
| service.metric_generator | input | currencyservice-1.csv | non_null_non_timestamp_cells | 534520 |
| service.metric_generator | input | currencyservice-2.csv | CSV_records | 43200 |
| service.metric_generator | input | currencyservice-2.csv | non_null_non_timestamp_cells | 534539 |
| service.metric_generator | input | currencyservice.csv | CSV_records | 21600 |
| service.metric_generator | input | currencyservice.csv | non_null_non_timestamp_cells | 85680 |
| service.metric_generator | input | currencyservice2-0.csv | CSV_records | 43200 |
| service.metric_generator | input | currencyservice2-0.csv | non_null_non_timestamp_cells | 538596 |
| service.metric_generator | input | emailservice-0.csv | CSV_records | 43200 |
| service.metric_generator | input | emailservice-0.csv | non_null_non_timestamp_cells | 624290 |
| service.metric_generator | input | emailservice-1.csv | CSV_records | 43200 |
| service.metric_generator | input | emailservice-1.csv | non_null_non_timestamp_cells | 624350 |
| service.metric_generator | input | emailservice-2.csv | CSV_records | 43200 |
| service.metric_generator | input | emailservice-2.csv | non_null_non_timestamp_cells | 624275 |
| service.metric_generator | input | emailservice.csv | CSV_records | 21600 |
| service.metric_generator | input | emailservice.csv | non_null_non_timestamp_cells | 85680 |
| service.metric_generator | input | emailservice2-0.csv | CSV_records | 43200 |
| service.metric_generator | input | emailservice2-0.csv | non_null_non_timestamp_cells | 624303 |
| service.metric_generator | input | frontend-0.csv | CSV_records | 43200 |
| service.metric_generator | input | frontend-0.csv | non_null_non_timestamp_cells | 624065 |
| service.metric_generator | input | frontend-1.csv | CSV_records | 43200 |
| service.metric_generator | input | frontend-1.csv | non_null_non_timestamp_cells | 624061 |
| service.metric_generator | input | frontend-2.csv | CSV_records | 43200 |
| service.metric_generator | input | frontend-2.csv | non_null_non_timestamp_cells | 624067 |
| service.metric_generator | input | frontend.csv | CSV_records | 21600 |
| service.metric_generator | input | frontend.csv | non_null_non_timestamp_cells | 85608 |
| service.metric_generator | input | frontend2-0.csv | CSV_records | 43200 |
| service.metric_generator | input | frontend2-0.csv | non_null_non_timestamp_cells | 624034 |
| service.metric_generator | input | metric_setting.json | array_elements | 109 |
| service.metric_generator | input | node-1.csv | CSV_records | 21600 |
| service.metric_generator | input | node-1.csv | non_null_non_timestamp_cells | 483840 |
| service.metric_generator | input | node-2.csv | CSV_records | 21600 |
| service.metric_generator | input | node-2.csv | non_null_non_timestamp_cells | 483600 |
| service.metric_generator | input | node-3.csv | CSV_records | 21600 |
| service.metric_generator | input | node-3.csv | non_null_non_timestamp_cells | 483840 |
| service.metric_generator | input | node-4.csv | CSV_records | 21600 |
| service.metric_generator | input | node-4.csv | non_null_non_timestamp_cells | 479343 |
| service.metric_generator | input | node-5.csv | CSV_records | 21600 |
| service.metric_generator | input | node-5.csv | non_null_non_timestamp_cells | 482688 |
| service.metric_generator | input | node-6.csv | CSV_records | 21600 |
| service.metric_generator | input | node-6.csv | non_null_non_timestamp_cells | 483840 |
| service.metric_generator | input | paymentservice-0.csv | CSV_records | 43200 |
| service.metric_generator | input | paymentservice-0.csv | non_null_non_timestamp_cells | 538684 |
| service.metric_generator | input | paymentservice-1.csv | CSV_records | 43200 |
| service.metric_generator | input | paymentservice-1.csv | non_null_non_timestamp_cells | 529720 |
| service.metric_generator | input | paymentservice-2.csv | CSV_records | 43200 |
| service.metric_generator | input | paymentservice-2.csv | non_null_non_timestamp_cells | 537286 |
| service.metric_generator | input | paymentservice.csv | CSV_records | 21600 |
| service.metric_generator | input | paymentservice.csv | non_null_non_timestamp_cells | 85680 |
| service.metric_generator | input | paymentservice2-0.csv | CSV_records | 43200 |
| service.metric_generator | input | paymentservice2-0.csv | non_null_non_timestamp_cells | 537236 |
| service.metric_generator | input | productcatalogservice-0.csv | CSV_records | 43200 |
| service.metric_generator | input | productcatalogservice-0.csv | non_null_non_timestamp_cells | 624168 |
| service.metric_generator | input | productcatalogservice-1.csv | CSV_records | 43200 |
| service.metric_generator | input | productcatalogservice-1.csv | non_null_non_timestamp_cells | 624194 |
| service.metric_generator | input | productcatalogservice-2.csv | CSV_records | 43200 |
| service.metric_generator | input | productcatalogservice-2.csv | non_null_non_timestamp_cells | 624229 |
| service.metric_generator | input | productcatalogservice.csv | CSV_records | 21600 |
| service.metric_generator | input | productcatalogservice.csv | non_null_non_timestamp_cells | 85644 |
| service.metric_generator | input | productcatalogservice2-0.csv | CSV_records | 43200 |
| service.metric_generator | input | productcatalogservice2-0.csv | non_null_non_timestamp_cells | 624186 |
| service.metric_generator | input | recommendationservice-0.csv | CSV_records | 43200 |
| service.metric_generator | input | recommendationservice-0.csv | non_null_non_timestamp_cells | 667006 |
| service.metric_generator | input | recommendationservice-1.csv | CSV_records | 43200 |
| service.metric_generator | input | recommendationservice-1.csv | non_null_non_timestamp_cells | 667019 |
| service.metric_generator | input | recommendationservice-2.csv | CSV_records | 43200 |
| service.metric_generator | input | recommendationservice-2.csv | non_null_non_timestamp_cells | 667027 |
| service.metric_generator | input | recommendationservice.csv | CSV_records | 21600 |
| service.metric_generator | input | recommendationservice.csv | non_null_non_timestamp_cells | 85672 |
| service.metric_generator | input | recommendationservice2-0.csv | CSV_records | 43200 |
| service.metric_generator | input | recommendationservice2-0.csv | non_null_non_timestamp_cells | 666987 |
| service.metric_generator | input | service_knowledge.json | array_elements | 10 |
| service.metric_generator | input | shippingservice-0.csv | CSV_records | 43200 |
| service.metric_generator | input | shippingservice-0.csv | non_null_non_timestamp_cells | 624320 |
| service.metric_generator | input | shippingservice-1.csv | CSV_records | 43200 |
| service.metric_generator | input | shippingservice-1.csv | non_null_non_timestamp_cells | 624335 |
| service.metric_generator | input | shippingservice-2.csv | CSV_records | 43200 |
| service.metric_generator | input | shippingservice-2.csv | non_null_non_timestamp_cells | 624282 |
| service.metric_generator | input | shippingservice.csv | CSV_records | 21600 |
| service.metric_generator | input | shippingservice.csv | non_null_non_timestamp_cells | 85680 |
| service.metric_generator | input | shippingservice2-0.csv | CSV_records | 43200 |
| service.metric_generator | input | shippingservice2-0.csv | non_null_non_timestamp_cells | 624268 |
| service.metric_generator | output | all_metric.pkl | processed_feature_cells | 31622400 |
| service.metric_generator | output | all_metric.pkl | processed_observation_rows | 2073600 |
| service.time_interval_label_generator | input | config.json | array_elements | 16 |
| service.time_interval_label_generator | input | groundtruth-2022-05-01.csv | CSV_records | 45 |
| service.time_interval_label_generator | input | groundtruth-2022-05-01.csv | non_null_non_timestamp_cells | 135 |
| service.time_interval_label_generator | input | groundtruth-2022-05-03.csv | CSV_records | 50 |
| service.time_interval_label_generator | input | groundtruth-2022-05-03.csv | non_null_non_timestamp_cells | 150 |
| service.time_interval_label_generator | input | groundtruth-2022-05-05.csv | CSV_records | 46 |
| service.time_interval_label_generator | input | groundtruth-2022-05-05.csv | non_null_non_timestamp_cells | 138 |
| service.time_interval_label_generator | input | groundtruth-2022-05-07.csv | CSV_records | 50 |
| service.time_interval_label_generator | input | groundtruth-2022-05-07.csv | non_null_non_timestamp_cells | 150 |
| service.time_interval_label_generator | input | groundtruth-2022-05-09.csv | CSV_records | 50 |
| service.time_interval_label_generator | input | groundtruth-2022-05-09.csv | non_null_non_timestamp_cells | 150 |
| service.time_interval_label_generator | input | groundtruth-k8s-1-2022-03-20.csv | CSV_records | 37 |
| service.time_interval_label_generator | input | groundtruth-k8s-1-2022-03-20.csv | non_null_non_timestamp_cells | 111 |
| service.time_interval_label_generator | input | groundtruth-k8s-1-2022-03-21.csv | CSV_records | 43 |
| service.time_interval_label_generator | input | groundtruth-k8s-1-2022-03-21.csv | non_null_non_timestamp_cells | 129 |
| service.time_interval_label_generator | input | groundtruth-k8s-2-2022-03-20.csv | CSV_records | 33 |
| service.time_interval_label_generator | input | groundtruth-k8s-2-2022-03-20.csv | non_null_non_timestamp_cells | 99 |
| service.time_interval_label_generator | input | groundtruth-k8s-2-2022-03-21.csv | CSV_records | 55 |
| service.time_interval_label_generator | input | groundtruth-k8s-2-2022-03-21.csv | non_null_non_timestamp_cells | 165 |
| service.time_interval_label_generator | input | groundtruth-k8s-3-2022-03-20.csv | CSV_records | 31 |
| service.time_interval_label_generator | input | groundtruth-k8s-3-2022-03-20.csv | non_null_non_timestamp_cells | 93 |
| service.time_interval_label_generator | input | groundtruth-k8s-3-2022-03-21.csv | CSV_records | 51 |
| service.time_interval_label_generator | input | groundtruth-k8s-3-2022-03-21.csv | non_null_non_timestamp_cells | 153 |
| service.time_interval_label_generator | input | groundtruth-k8s-3-2022-03-24.csv | CSV_records | 50 |
| service.time_interval_label_generator | input | groundtruth-k8s-3-2022-03-24.csv | non_null_non_timestamp_cells | 150 |
| service.time_interval_label_generator | input | metric_setting.json | array_elements | 109 |
| service.time_interval_label_generator | input | service_knowledge.json | array_elements | 10 |
| service.time_interval_label_generator | input | time_interval_window_size_9.pkl | array_elements | 21020 |
| service.time_interval_label_generator | input | time_interval_window_size_9.pkl | entity_label_values | 263984 |
| service.time_interval_label_generator | input | time_interval_window_size_9.pkl | label_vectors | 4714 |
| service.time_interval_label_generator | input | time_interval_window_size_9.pkl | time_windows | 4714 |
| service.time_interval_label_generator | output | time_interval_window_size_11.pkl | array_elements | 20996 |
| service.time_interval_label_generator | output | time_interval_window_size_11.pkl | entity_label_values | 263648 |
| service.time_interval_label_generator | output | time_interval_window_size_11.pkl | label_vectors | 4708 |
| service.time_interval_label_generator | output | time_interval_window_size_11.pkl | time_windows | 4708 |
| service.time_interval_label_generator | output | time_interval_window_size_13.pkl | array_elements | 20972 |
| service.time_interval_label_generator | output | time_interval_window_size_13.pkl | entity_label_values | 263312 |
| service.time_interval_label_generator | output | time_interval_window_size_13.pkl | label_vectors | 4702 |
| service.time_interval_label_generator | output | time_interval_window_size_13.pkl | time_windows | 4702 |
| service.time_interval_label_generator | output | time_interval_window_size_15.pkl | array_elements | 20948 |
| service.time_interval_label_generator | output | time_interval_window_size_15.pkl | entity_label_values | 262976 |
| service.time_interval_label_generator | output | time_interval_window_size_15.pkl | label_vectors | 4696 |
| service.time_interval_label_generator | output | time_interval_window_size_15.pkl | time_windows | 4696 |
| service.time_interval_label_generator | output | time_interval_window_size_17.pkl | array_elements | 20924 |
| service.time_interval_label_generator | output | time_interval_window_size_17.pkl | entity_label_values | 262640 |
| service.time_interval_label_generator | output | time_interval_window_size_17.pkl | label_vectors | 4690 |
| service.time_interval_label_generator | output | time_interval_window_size_17.pkl | time_windows | 4690 |
| service.time_interval_label_generator | output | time_interval_window_size_7.pkl | array_elements | 21044 |
| service.time_interval_label_generator | output | time_interval_window_size_7.pkl | entity_label_values | 264320 |
| service.time_interval_label_generator | output | time_interval_window_size_7.pkl | label_vectors | 4720 |
| service.time_interval_label_generator | output | time_interval_window_size_7.pkl | time_windows | 4720 |
| service.time_interval_label_generator | output | time_interval_window_size_9.pkl | array_elements | 21020 |
| service.time_interval_label_generator | output | time_interval_window_size_9.pkl | entity_label_values | 263984 |
| service.time_interval_label_generator | output | time_interval_window_size_9.pkl | label_vectors | 4714 |
| service.time_interval_label_generator | output | time_interval_window_size_9.pkl | time_windows | 4714 |
| service.trace_generator | input | all_trace.pkl | processed_feature_cells | 10368000 |
| service.trace_generator | input | all_trace.pkl | processed_observation_rows | 1728000 |
| service.trace_generator | input | all_trace_features.pkl | processed_feature_cells | 5184000 |
| service.trace_generator | input | all_trace_features.pkl | processed_observation_rows | 21600 |
| service.trace_generator | input | config.json | array_elements | 16 |
| service.trace_generator | input | metric_setting.json | array_elements | 109 |
| service.trace_generator | input | service_knowledge.json | array_elements | 10 |
| service.trace_generator | input | span_features.csv | CSV_records | 21600 |
| service.trace_generator | input | span_features.csv | non_null_non_timestamp_cells | 5184000 |
| service.trace_generator | output | all_trace.pkl | processed_feature_cells | 10368000 |
| service.trace_generator | output | all_trace.pkl | processed_observation_rows | 1728000 |
| service.trace_generator | output | all_trace_features.pkl | processed_feature_cells | 5184000 |
| service.trace_generator | output | all_trace_features.pkl | processed_observation_rows | 21600 |

## 附錄E：前處理schema例子

各script列一份代表輸出，schema概要由已保存stage_schemas.json抽取。完整所有檔案與field schema保留在該JSON，逐檔對應見stage_counts.json的schema_ref。JSON／pickle的mapping_entries為結構鍵數，不當作觀測列。

| Script | 代表輸出（相對generated） | Schema概要 |
|---|---|---|
| dao.topology_dao | raw_data\normal\2022-03-19\cloudbed-1\resource_entity\edge_index.pkl | {"field_path":"","kind":"list","count":2,"unit":"items"}<br>{"field_path":"","kind":"ndarray","shape":[2,164],"dtype":"int32","count":328,"unit":"array elements","nan_count":0,"inf_count":0} |
| service.ent_edge_index_generator | dataset\ent_edge_index\ent_edge_index.pkl | {"field_path":"","kind":"dict","keys":["normal","train_valid","test"],"count":3,"unit":"keys"}<br>{"field_path":"/normal","kind":"dict","keys":["2022-03-19/cloudbed-1","2022-03-19/cloudbed-2","2022-03-19/cloudbed-3","2022-03-20/cloudbed-1","2022-03-20/cloudbed-2","2022-03-20/cloudbed-3","2022-03-21/cloudbed-1","2022-03-21/cloudbed-2","2022-03-21/cloudbed-3","2022-03-24/cloudbed-3","2022-05-01/cloudbed","2022-05-03/cloudbed","2022-05-05/cloudbed","2022-05-07/cloudbed","2022-05-09/cloudbed"],"count":15,"unit":"keys"}<br>{"field_path":"/normal/2022-03-19/cloudbed-1","kind":"list","count":2,"unit":"items"} |
| service.time_interval_label_generator | dataset\time_interval_and_label\time_interval_window_size_11.pkl | {"field_path":"","kind":"dict","keys":["time_interval","y","entity_type","template","cmdb_id","root_cause_type"],"count":6,"unit":"keys"}<br>{"field_path":"/time_interval","kind":"dict","keys":["normal","train_valid","test"],"count":3,"unit":"keys"}<br>{"field_path":"/time_interval/normal","kind":"list","count":4167,"unit":"items"} |
| dao.metric_dao | raw_data\normal\2022-03-19\cloudbed-1\raw_metric\container\adservice-0.csv | {"rows":1440,"columns":["timestamp","CPU/kpi_container_cpu_usage_seconds","CPU/kpi_container_cpu_user_seconds","CPU/kpi_container_cpu_system_seconds","CPU/kpi_container_cpu_cfs_throttled_seconds","CPU/kpi_container_cpu_cfs_throttled_periods","Memory/kpi_container_memory_cache","Memory/kpi_container_memory_mapped_file","Memory/kpi_container_memory_usage_MB","Memory/kpi_container_memory_working_set_MB","Memory/kpi_container_memory_rss","Disk/kpi_container_fs_inodes","Disk/kpi_container_fs_reads_MB","Disk/kpi_container_fs_usage_MB","Disk/kpi_container_fs_writes_MB","Thread/kpi_container_threads","Network/kpi_container_network_receive_packets","Network/kpi_container_network_receive_MB","Network/kpi_container_network_transmit_packets","Network/kpi_container_network_transmit_MB"],"dtypes":{"timestamp":"int64","CPU/kpi_container_cpu_usage_seconds":"float64","CPU/kpi_container_cpu_user_seconds":"float64","CPU/kpi_container_cpu_system_seconds":"float64","CPU/kpi_container_cpu_cfs_throttled_seconds":"float64","CPU/kpi_container_cpu_cfs_throttled_periods":"float64","Memory/kpi_container_memory_cache":"float64","Memory/kpi_container_memory_mapped_file":"int64","Memory/kpi_container_memory_usage_MB":"float64","Memory/kpi_container_memory_working_set_MB":"float64","Memory/kpi_container_memory_rss":"float64","Disk/kpi_container_fs_inodes":"float64","Disk/kpi_container_fs_reads_MB":"float64","Disk/kpi_container_fs_usage_MB":"float64","Disk/kpi_container_fs_writes_MB":"float64","Thread/kpi_container_threads":"float64","Network/kpi_container_network_receive_packets":"float64","Network/kpi_container_network_receive_MB":"float64","Network/kpi_container_network_transmit_packets":"float64","Network/kpi_container_network_transmit_MB":"float64"},"non_null_non_timestamp_cells":27300,"unit":"CSV records (multiline quoted records parsed by pandas)","dtype_policy":"first chunk inferred dtypes"} |
| service.metric_generator | analysis\metric\common_statistic.json | {"field_path":"","kind":"dict","keys":["node","container","service","istio"],"count":4,"unit":"keys"}<br>{"field_path":"/node","kind":"dict","keys":["node"],"count":1,"unit":"keys"}<br>{"field_path":"/node/node","kind":"dict","keys":["CPU/system.load.1","CPU/system.load.15","CPU/system.load.5","CPU/system.cpu.iowait","CPU/system.cpu.pct_usage","CPU/system.cpu.system","CPU/system.cpu.user","Memory/system.mem.pct_usage","Memory/system.mem.real.pct_useage","Memory/system.mem.real.used","Memory/system.mem.usable","Memory/system.mem.used","Disk/system.io.avg_q_sz","Disk/system.io.await","Disk/system.io.r_await","Disk/system.io.r_s","Disk/system.io.rkb_s","Disk/system.io.svctm","Disk/system.io.util","Disk/system.io.w_await","Disk/system.io.w_s","Disk/system.disk.free","Disk/system.disk.pct_usage","Disk/system.disk.used"],"count":24,"unit":"keys"} |
| dao.trace_dao | analysis\trace\trace_patterns.json | {"field_path":"","kind":"dict","keys":["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","paymentservice","productcatalogservice","recommendationservice","shippingservice"],"count":10,"unit":"keys"}<br>{"field_path":"/adservice","kind":"list","count":10,"unit":"items"}<br>{"field_path":"/adservice","kind":"ndarray","shape":[10],"dtype":"<U16","count":10,"unit":"array elements","nan_count":null,"inf_count":null} |
| service.trace_generator | analysis\trace\statistic.json | {"field_path":"","kind":"dict","keys":["<intensity>; cmdb_id: adservice; type: upstream","<duration>; cmdb_id: adservice; type: upstream","<intensity>; cmdb_id: adservice; type: current","<duration>; cmdb_id: adservice; type: current","<intensity>; cmdb_id: adservice; type: downstream","<duration>; cmdb_id: adservice; type: downstream","<intensity>; cmdb_id: cartservice; type: upstream","<duration>; cmdb_id: cartservice; type: upstream","<intensity>; cmdb_id: cartservice; type: current","<duration>; cmdb_id: cartservice; type: current","<intensity>; cmdb_id: cartservice; type: downstream","<duration>; cmdb_id: cartservice; type: downstream","<intensity>; cmdb_id: checkoutservice; type: upstream","<duration>; cmdb_id: checkoutservice; type: upstream","<intensity>; cmdb_id: checkoutservice; type: current","<duration>; cmdb_id: checkoutservice; type: current","<intensity>; cmdb_id: checkoutservice; type: downstream","<duration>; cmdb_id: checkoutservice; type: downstream","<intensity>; cmdb_id: currencyservice; type: upstream","<duration>; cmdb_id: currencyservice; type: upstream","<intensity>; cmdb_id: currencyservice; type: current","<duration>; cmdb_id: currencyservice; type: current","<intensity>; cmdb_id: currencyservice; type: downstream","<duration>; cmdb_id: currencyservice; type: downstream","<intensity>; cmdb_id: emailservice; type: upstream","<duration>; cmdb_id: emailservice; type: upstream","<intensity>; cmdb_id: emailservice; type: current","<duration>; cmdb_id: emailservice; type: current","<intensity>; cmdb_id: emailservice; type: downstream","<duration>; cmdb_id: emailservice; type: downstream","<intensity>; cmdb_id: frontend; type: upstream","<duration>; cmdb_id: frontend; type: upstream","<intensity>; cmdb_id: frontend; type: current","<duration>; cmdb_id: frontend; type: current","<intensity>; cmdb_id: frontend; type: downstream","<duration>; cmdb_id: frontend; type: downstream","<intensity>; cmdb_id: paymentservice; type: upstream","<duration>; cmdb_id: paymentservice; type: upstream","<intensity>; cmdb_id: paymentservice; type: current","<duration>; cmdb_id: paymentservice; type: current","<intensity>; cmdb_id: paymentservice; type: downstream","<duration>; cmdb_id: paymentservice; type: downstream","<intensity>; cmdb_id: productcatalogservice; type: upstream","<duration>; cmdb_id: productcatalogservice; type: upstream","<intensity>; cmdb_id: productcatalogservice; type: current","<duration>; cmdb_id: productcatalogservice; type: current","<intensity>; cmdb_id: productcatalogservice; type: downstream","<duration>; cmdb_id: productcatalogservice; type: downstream","<intensity>; cmdb_id: recommendationservice; type: upstream","<duration>; cmdb_id: recommendationservice; type: upstream","<intensity>; cmdb_id: recommendationservice; type: current","<duration>; cmdb_id: recommendationservice; type: current","<intensity>; cmdb_id: recommendationservice; type: downstream","<duration>; cmdb_id: recommendationservice; type: downstream","<intensity>; cmdb_id: shippingservice; type: upstream","<duration>; cmdb_id: shippingservice; type: upstream","<intensity>; cmdb_id: shippingservice; type: current","<duration>; cmdb_id: shippingservice; type: current","<intensity>; cmdb_id: shippingservice; type: downstream","<duration>; cmdb_id: shippingservice; type: downstream"],"count":60,"unit":"keys"}<br>{"field_path":"/<intensity>; cmdb_id: adservice; type: upstream","kind":"dict","keys":["mean","std","percentile_1","q1","median","q3","percentile_99","valid_ratio"],"count":8,"unit":"keys"}<br>{"field_path":"/<intensity>; cmdb_id: adservice; type: upstream/mean","kind":"float","unit":"scalar"} |
| dao.log_dao | analysis\log\istio_words.json | {"field_path":"","kind":"dict","keys":["word_set"],"count":1,"unit":"keys"}<br>{"field_path":"/word_set","kind":"list","count":1368,"unit":"items"}<br>{"field_path":"/word_set","kind":"ndarray","shape":[1368],"dtype":"<U65","count":1368,"unit":"array elements","nan_count":null,"inf_count":null} |
| service.log_generator | analysis\log\container_log_selected_patterns.json | {"field_path":"","kind":"dict","keys":["C#","Java","Python","Node.js","Go"],"count":5,"unit":"keys"}<br>{"field_path":"/C#","kind":"list","count":2,"unit":"items"}<br>{"field_path":"/C#","kind":"ndarray","shape":[2],"dtype":"int32","count":2,"unit":"array elements","nan_count":0,"inf_count":0} |
| service.dataset_generator | dataset\final\metric_trace_log.pkl | {"field_path":"","kind":"dict","keys":["meta_data","data","raw_data"],"count":3,"unit":"keys"}<br>{"field_path":"/meta_data","kind":"dict","keys":["modal_types","ent_types","ent_names","ent_type_index","ent_fault_type_index","ent_feature_num","o11y_names","fault_type_list","en_fault_type_list","ent_edge_index"],"count":10,"unit":"keys"}<br>{"field_path":"/meta_data/modal_types","kind":"list","count":3,"unit":"items"} |

## 附錄F：Encoder seed406 loss curve

Seed406來源：[loss.csv](../runs/lasrca/encoder_public_recheck_20261005/ts2vec_seed406/loss.csv)。以下列epoch1、每50epochs及末epoch的loss，完整600點保留在CSV。若未渲染折線圖，這些點只是曲線摘要，不能宣稱已顯示完整loss curve。

| Epoch | Loss | elapsed秒 |
|---|---:|---:|
| 1 | 245.771042 | 6.282 |
| 50 | 3.859110 | 238.891 |
| 100 | 3.535454 | 488.157 |
| 150 | 3.012374 | 810.250 |
| 200 | 2.509987 | 1172.250 |
| 250 | 2.559512 | 1454.579 |
| 300 | 2.155071 | 1704.625 |
| 350 | 2.336432 | 2108.188 |
| 400 | 1.665111 | 2393.329 |
| 450 | 1.670046 | 2647.110 |
| 500 | 1.661207 | 2928.172 |
| 550 | 1.315717 | 3140.407 |
| 600 | 1.307805 | 3526.813 |
