# LasRCA 後六項任務介紹草稿

2026-10-11。依 [簡報歸納原則](task_introduction_principles_20261011.md) 撰寫，涵蓋0C-06～11。每項「介紹正文」對應任務介紹頁，「講稿備註」保留必要性、名詞及來源。這是完整文字草稿，尚未決定一頁放多少內容，也未將技術細節從正文刪除。實驗已按核准範圍完成，以下目標與要求用於介紹工作，不代表要再執行一輪。

沿用公開程式的100 cases／subgraphs；LLM採使用者核准的GPT-6 Luna OAuth，原07／08的GPT-4條件因此有替代設定差異。原始進度文件與PPTX均未修改。OAuth與新增紀錄／恢復功能屬與論文演算法無關的執行支援。

## 0C-06 Labeling Method Verification｜LLM標註流程驗證

### 介紹正文

**目標**

- 確認所選故障案例能完成四階段LLM分析，取得可供分類器使用的entity故障類型標籤。
- 檢查回答能否解析、名稱與故障類型是否合法，並保存模型判斷的實際理由。
- 記錄執行錯誤、模型版本、token用量及成本，說明此次標註的完成範圍。

**要求**

- 沿用已選出的100個cases／subgraphs，逐案例保存first、second、third及summarization的完整prompt與response。
- first按node／pod的觀測類別分析，second整合同一entity的判斷，third結合子圖關係分析，summarization整理為entity名稱與`exact_fault_type`。
- 保存解析標籤及stage-3的實際explanation，分別統計案例完成率、格式異常及合法entity labels數。
- 記錄每個請求的requested／returned model、usage與API／路徑錯誤。成本估算須標明計算依據，OAuth實付不可得時明列不可得。

**程式變更**

- 以OAuth接入GPT-6 Luna，保持公開程式四階段流程與prompt語義。這是模型與呼叫方式的替代設定，不代表原GPT-4結果重現。
- 新增請求與案例／階段的關聯、原文保存、格式驗證及中斷恢復，讓錯誤與成功產物可追查。上述功能屬執行支援，與論文演算法無關。

### 講稿備註

頁面目的：交代LLM回答如何成為下一項訓練的輸入。entity是待判斷的node、pod或service；subgraph是該案例選取的entities及其關係。prompt是實際送給模型的提示內容，response是模型回答；`exact_fault_type`是摘要中待解析的故障名稱。OAuth是帳號授權呼叫方式，token是服務回報的輸入／輸出文字計量單位。

因為一句自然語言判斷還不能直接填入訓練資料，流程先按觀測類別分析node／pod，再合併同一entity的判斷。第三階段才結合子圖中的entities及關係，形成案例層級的判斷與理由，可涵蓋service。摘要階段將回答整理成固定格式，程式再檢查entity是否存在、故障名稱是否在合法集合內。不同stage請求數並不相同，不能用100 cases推定只有400次請求。GT不新增至prompt，也不用來修正回答。

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
- 回報絕對差與相對差，標明百分點或相對百分比；基準為0時相對差列不可計算。
- 保存逐entity probability、GT及案例ranking以供重算，與論文對應表格逐項比較方向及條件。

**程式變更**

- 新增輸入配對核對、checkpoint重評估與逐案例預測匯出，確認比較使用實際完成的模型。
- 新增逐seed／統計摘要及論文方向表。以上是與論文演算法無關的評估與保存功能。

### 講稿備註

AC@u衡量實際故障entity是否進入模型前u名定位結果。Precision衡量預測某故障類型的結果中有多少正確，Recall衡量該故障類型中有多少被找出，F1是兩者的調和平均。Micro先合併類別計數再算指標，Macro先按類別計算再平均。公開程式的Macro F1是逐類F1平均，與論文文字及舊簡報notes所述的Macro P／R調和平均須分開。GT是評估用參考標籤，probability是類別機率，ranking是定位排序。

為了避免把資料或前處理變動誤當成補標效果，兩組除新增LLM labels外保持相同條件。各seed先配對，再彙整五組平均與母體std。百分點差為100×(k1−k0)，相對百分比為100×(k1−k0)/k0，不能混用。

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

**要求**

- 固定normal／train_valid／test的日期、cloudbed、原始檔與GT來源，在獨立目錄保存重建結果。
- 完成topology、entity edge index、time windows／labels，以及Metric／Trace／Log擷取與轉換，最後組裝dataset，共10個scripts。
- 各script保存輸入／輸出內容數量、計數單位、schema、duration、exit status及失敗／中斷證據，建立final manifest。
- 抽樣對照shape、timestamps、三模態feature名稱／數值；另核對覆蓋範圍內labels與topology，明列差異及比較範圍。

**程式變更**

- 補齊test GT JSON至CSV的無損格式轉換，啟用原入口漏跑的Istio擷取及四類Metric標準化，處理重跑目錄已存在的情況。
- 修正全NaN／零變異Metric分支沿用前一特徵值的問題，明確產生零值。此為數值行為差異，須記錄對released比較的影響。
- 新增逐script數量與產物歸屬核對，分開觀測列、feature cells、時間窗、label values與edges。上述補齊、修正與紀錄不列為論文提出的演算法。

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

### 講稿備註

TS2Vec是將觀測時間序列轉成向量的encoder。checkpoint保存模型參數，embedding保存模型算出的向量，兩者不能互稱。作者下載包的 `model.zip` 提供下游模型，沒有TS2Vec權重；`embedding_600.pkl` 是作者已算好的embedding。因此公開基準使用作者向量，自訓路線訓練我們的encoder再產生向量。下游程式直接讀入固定embedding，沒有在此次下游訓練中端到端更新TS2Vec。

本輪只自訓service的8個Metric，沒有把Trace／Log加入service輸入。先固定資料與特徵順序，使用作者公開設定訓練600 epochs，再以相同encoding設定生成150段序列的1440×320向量。coverage表示預期序列皆有輸出，NaN／Inf是非有限值；loss顯示訓練目標的變化，不能直接當RCA accuracy。batch、lr與最大訓練長度分別指每次訓練的序列數、參數更新步幅及訓練序列長度上限。

為了比較下游效果，只替換service embedding，保持node／pod作者向量、split、labels與下游seed相同。隔離cache讓程式讀入正確版本。service向量可經圖模型與下游重訓影響node／pod結果，所以「只替換service」不代表只有service指標會變。

seed405及追加406的encoder都使用同一作者公開processed input，其SHA與archive entry一致，均未使用本次raw重建資料。公開基準在同下游seed重跑的36指標一致；兩個自訓encoder的下游結果仍有升有降。這支持encoder隨機性與重新學得的embedding影響結果，不能推定新raw資料導致下降，也不能因此證明新raw沒有問題。作者encoder seed未知，兩個encoder seeds加單一下游seed不足以宣稱穩定性或精確還原作者模型。

證據：`ts2vec_20261004/{input_manifest.json,loss.csv,loss_curve.png,timing.json,model.pkl}`、`ts2vec_downstream/{encoding_manifest.json,service_replaced.pkl}`、`encoder_pair_20261004/comparison.json`；追加run `encoder_public_recheck_20261005/{protocol.json,public_input_provenance.json,status.json}` 、`downstream/comparison.json`、run根目錄的 `three_variant_comparison.csv` 與 `verification_and_three_variants.json`。公開設定來源為 `code/pretrain.sh` 與 `code/pretrain/train.py`，下載包與實際輸入的核對見 [encoder來源報告](encoder_public_provenance.md)。未獨立量測的歷史耗時保持null，不把載入／樣本encoding總耗時全稱純訓練時間。

銜接至結論：六項完成代表既定流程與保存／比較要求完成。Luna替代設定、錯標、raw特徵差異及encoder對照範圍，仍是解讀實驗結果時必須保留的界線。

## 後續製作結果頁時的素材

此草稿先固定介紹邏輯。結果頁可從 [六項結案報告](six_tasks_closure_20261005.md)、[第一輪結果](one_round_results_20261004.md) 與 [encoder來源／追加結果](encoder_public_provenance.md) 取用數值與來源。LLM標註率、五seed重訓表、k0／k1比較、真實錯誤案例、raw對照與encoder三版本比較應分開呈現，避免用一張「全部完成」表取代必要的結果及限制。
