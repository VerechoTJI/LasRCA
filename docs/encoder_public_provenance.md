# TS2Vec 公開產物、自訓來源與追加對照

## 作者提供什麼

已直接檢查下載的`model.zip`及`temp_data.zip`目錄，而非依檔名猜測。`model.zip`包含LasRCA、fine-tune、fix_match下游模型，沒有pretrain／TS2Vec encoder權重。`temp_data.zip`包含`temp_data/A/embeddings/embedding_600.pkl`，是作者已算好的embedding，不是TS2Vec的model.pkl。公開`pretrain/train.py`及`data_encoder.py`提供從資料訓練與編碼的程式；不能因程式會讀model/pretrain就說下載包也提供該模型。

因此本次比較的兩邊是「作者提供的embedding」與「我們以公開資料自行訓練後產生的embedding」。本次自訓model.pkl是我們產生的權重，不能與公開下游classifier checkpoint混為一談。舊文件引用的原始0C-11「released checkpoint」文字不構成作者有提供TS2Vec權重的證據；原始文件保持唯讀。

## 上一輪自訓已經使用公開資料

seed405 encoder的實際輸入為`temp_data/2022_CCF_AIOps_challenge/dataset/final/metric_trace_log.pkl`，SHA256 `c594cdf9ba66c5ff493985a98ff9fdc258e6a3e45fc52d5b69051e8b54b0795b`，是released processed資料；不是`runs/lasrca/raw_full_20261004/generated/...`的新重建資料。因此前次encoder效果有升有降，不能歸因於新重建raw資料或其六個Istio特徵差異。

service實際為8個Metric、沒有Trace／Log輸入。`pretrain.sh`的service命令與`pretrain/train.py` defaults為600epochs、batch32、lr0.001、repr320、max_train_length3000，上一輪沿用。TS2Vec source實作、normal＋train_valid fit範圍、causal=True／sliding_length1／padding10 encoding均沿用公開程式。seed405是本次明確固定的實驗條件；公開train.py未固定可還原作者產物的seed，作者實際初始化／訓練順序與完整歷史不可確認。Windows／Torch／GPU環境與README作者環境不同，也不能宣稱逐位重現。

## 本次追加的可解釋對照

使用相同released processed資料，重新訓練service encoder，固定seed406，沿用同一組作者service參數，全部150序列重新編碼。下游仍固定seed405、500epochs，兩邊同split／GT／設定；node及pod維持作者embedding。只變更encoder隨機seed，避免把encoder差異與下游seed變更混在一起。原seed405產物及原比較全部保留。

追加run在`runs/lasrca/encoder_public_recheck_20261005`：`public_input_provenance.json`核對下載包中的原始資料entry與實際輸入SHA256；`protocol.json`保存來源腳本hash及設定；`execution`保存訓練、編碼、下游各次command／exit／logs；`status.json`表示當前stage及完成／失敗。成功後可比較同一個下游seed405下，作者embedding、自訓encoder seed405、自訓encoder seed406的結果。兩個encoder seed仍不足以宣稱普遍更好或更差。

若要驗證「raw重建資料是否導致encoder變差」，必須另外在同encoder seed／下游seed／feature順序下配對released與重建資料；本次公開資料重訓本身無法證明該因果關係。先釐清既有結果已排除新raw資料的直接使用，不擅自將raw差異歸為此結果的原因。

以上來源核對、hash、隔離輸出、恢復及執行紀錄與論文演算法無關；公開embedding對照、自訓service部分替換及明確seed屬本次實驗設定，限制需隨結果報告。

## 2026-10-05 07:53實際啟動紀錄

資料entry從temp_data.zip直接串流計算SHA256，與實際訓練檔及上一輪seed405輸入均為`c594cdf9ba66c5ff493985a98ff9fdc258e6a3e45fc52d5b69051e8b54b0795b`；input_matches_download及input_matches_previous_trial皆true。model.zip完整非MACOSX檔名清單已保存，ts2vec_weight_entries為空。追加seed406訓練已進入600epochs流程，尚未完成，不把啟動當結果。controller之後自動接150序列encoding、兩組固定下游seed405比較；原產物不覆寫。

來源說明commit3e7a9a8；控制器與來源檢查commit870970e，6項相關測試通過。每小時提醒已改為監控本run，完成或失敗才通知，完成後停止。

## 2026-10-05追加結果：09:45完成，09:56核對

service encoder seed406完成600epochs，checkpoint SHA256與summary一致；150段編碼皆finite。released／self-service兩組下游seed405各500epochs，兩份checkpoint hash一致；split／labels與同組及上一輪皆相同。重新跑的公開embedding基準36項指標與上一輪完全一致，沒有因新run改動基準。

以下為百分比數值，所有下游均固定seed405；encoder seed是唯一有意變更的訓練設定，node／pod embedding沿用作者公開產物。AC@k是正確根因在前k名內的比例。

| Entity／指標 | 作者embedding | 自訓encoder seed405 | 自訓encoder seed406 |
|---|---:|---:|---:|
| service AC@1 | 34.09% | 35.23% | 34.09% |
| service AC@3 | 56.82% | 55.68% | 55.68% |
| service AC@5 | 68.18% | 72.73% | 70.45% |
| service MacroF1 | 1.6335% | 1.6073% | 1.6930% |
| node AC@1 | 35.82% | 32.84% | 37.31% |
| node AC@5 | 79.10% | 70.15% | 76.12% |
| pod AC@1 | 29.07% | 27.91% | 30.23% |
| pod AC@5 | 60.47% | 55.81% | 54.65% |

**可得結論：**相同公開資料與公開service參數下，encoder換seed會改變下游效果；本次node／pod AC@1相對公開基準的方向從下降變為提升，service AC@1提升則消失，service MacroF1由略降變略升。兩個自訓encoder的service AC@5均提高，但node／pod AC@5均下降。因此不能說自訓全面變差或更好，也不能以單次下降判定資料有問題。已直接確認兩輪都沒有使用新raw重建資料，故新raw資料不是這兩輪結果的實際輸入來源。

**因果與限制：**資料來源、下游split／labels／seed保持相同，公开embedding基準重跑一致，這支持差異與重新學得的service embedding及其下游互動有關；不是對作者encoder歷史的完整重建。只有兩個encoder seeds、單一固定下游seed，沒有統計顯著性／多seed穩定性結論。不能因此證明新raw資料沒有問題；該問題需要另外做released／raw-rebuilt同seed對照。公開基準與自訓的MacroF1皆很低，微小增加也不能稱為良好分類能力；此路線不等同Luna補標的端到端k0／k1實驗。

原始36指標及各run protocol在`encoder_public_recheck_20261005/downstream/comparison.json/.csv/.md`。新增`three_variant_comparison.csv`及`verification_and_three_variants.json`保存全部三個版本、逐指標百分點差、checkpoint／coverage／基準一致核對；數值精度沿用原evaluator六位小數輸出。原六項第一輪結果保持，不覆寫seed405模型／embedding；原始reproduction status SHA256保持不變。
