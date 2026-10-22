# Smart Contract Analyser — Legal-BERT Experiment & Evaluation Report

**Document Version**: 1.0.0 (Dataset v3.3.0 Frozen Cycle)  
**Experiment Date**: October 22, 2026  
**Target Model**: `nlpaueb/legal-bert-base-uncased` (Multi-Label Operational Hazard Classifier)  
**Dataset Version**: `v3.3.0`  
**Dataset SHA-256**: `74464fd132e9268220549adc8e5cfb31d4ca69b9fae203b31ae2924c1500e456`  
**Model Output Directory**: [`analysis/models/legal_bert_v3.3.0/`](file:///c:/ARO/Projects/Smart_Contract_Analyser/analysis/models/legal_bert_v3.3.0/)  
**Evaluation Status**: Completed — Full Honest Disclosure of Small-Data Limitations  

---

## 1. Experiment Overview & Environment

This report documents the official training and evaluation experiment for the **Legal-BERT Multi-Label Operational Hazard Classifier** using the frozen canonical dataset version `v3.3.0`.

### 1.1 Training Environment
- **Platform**: Windows 11 / Python 3.14.3
- **Execution Device**: CPU (Intel multi-core execution)
- **Frameworks**: PyTorch 2.11.0+cpu, HuggingFace Transformers 5.5.3, Scikit-Learn 1.6.1
- **Base Checkpoint**: `nlpaueb/legal-bert-base-uncased` (Pre-trained on legal text; 110M parameters)
- **Target Problem Type**: Multi-label sequence classification (5 binary heads with `BCEWithLogitsLoss`)

### 1.2 Training Configuration & Reproducibility Parameters
From [`analysis/training_config.json`](file:///c:/ARO/Projects/Smart_Contract_Analyser/analysis/training_config.json):
- **Random Seed**: `42`
- **Number of Epochs**: 3
- **Batch Size**: 4
- **Learning Rate**: `3e-5` (AdamW optimizer, weight decay = 0.01)
- **Warmup Schedule**: Linear warmup across first 10% of training steps
- **Sequence Length**: 512 tokens (truncated, padded to `max_length`)
- **Input Field**: `model_text` (Dual-stream natural-language contract representation observable at submission time)

### 1.3 Exact Execution Command
```bash
python analysis/train_legal_bert.py --output-dir analysis/models/legal_bert_v3.3.0
```

---

## 2. Dataset Splits & Category Balance

The frozen `v3.3.0` dataset enforces deterministic project-level group isolation (`seed=42`, `GroupShuffleSplit`). Cross-split leakage between Train, Validation, and Test is **0.0%**.

### 2.1 Split Composition
- **Train ($N=44$)**: 24 real-source records + 20 synthetic records across 19 distinct project families.
- **Validation ($N=7$)**: 100% real-source records across 4 projects (`coinbase_base_bridge`, `spectral_image_vaults`, `the_compact`, `very_liquid_vaults`).
- **Test ($N=7$)**: 100% real-source records across 4 projects (`anvil_protocol`, `aragon_vault`, `crytic_not_so_smart_contracts`, `virtuals_genesis`).
- **Excluded ($N=14$)**: Real-source records excluded due to license restrictions (7) or excerpt defects (7); assigned to `split: "unassigned"`.

### 2.2 Category Distribution Across Splits
```
+---------------------+------------------------+-------------------+-------------------+
| Category            | Train (N=44)           | Validation (N=7)  | Test (N=7)        |
|                     | [24 Real / 20 Synth]   | [7 Real / 0 Synth]| [7 Real / 0 Synth]|
+---------------------+------------------------+-------------------+-------------------+
| Privacy             | 5 Pos (1 Real, 4 Synth)|  0 Pos / 7 Neg    |  0 Pos / 7 Neg    |
| Termination         | 3 Pos (3 Real, 0 Synth)|  0 Pos / 7 Neg    |  3 Pos / 4 Neg    |
| Legal Compliance    | 5 Pos (5 Real, 0 Synth)|  0 Pos / 7 Neg    |  4 Pos / 3 Neg    |
| Liability           | 5 Pos (1 Real, 4 Synth)|  0 Pos / 7 Neg    |  0 Pos / 7 Neg    |
| Payment / Financial | 6 Pos (4 Real, 2 Synth)|  0 Pos / 7 Neg    |  0 Pos / 7 Neg    |
+---------------------+------------------------+-------------------+-------------------+
```

---

## 3. Training Execution & Loss Trajectory

Training completed cleanly across all 3 epochs without errors:
- **Total Training Steps**: 33 steps (11 batches per epoch $\times$ 3 epochs)
- **Epoch 1 Average Loss**: `0.5764`
- **Epoch 2 Average Loss**: `0.4358`
- **Epoch 3 Average Loss**: `0.3945`
- **CPU Time**: ~3,000 CPU-seconds total execution time.

---

## 4. Threshold Calibration & Evaluation Results

### 4.1 Validation Threshold Selection (Validation Split Only)
In accordance with evaluation integrity rules, threshold selection was evaluated strictly on the 7 real-source validation records without inspecting test data.
- **Validation Positive Support**: 0 positive examples across all five categories.
- **Outcome**: Because validation data contains zero positive ground-truth examples, empirical threshold calibration is mathematically unfeasible (calibrating on pure negatives would collapse probability thresholds). All five categories retained the default threshold of **0.50** (`default_uncalibrated`).

### 4.2 Legal-BERT Evaluation on Untouched Real-Source Test Split ($N=7$)

```
+---------------------+--------+-----+-----+----+----+----+----+--------+--------+--------+------------------------------------+
| Category            | Thresh | Pos | Neg | TP | FP | FN | TN | Prec   | Recall | F1     | Support Status                     |
+---------------------+--------+-----+-----+----+----+----+----+--------+--------+--------+------------------------------------+
| Privacy             |  0.50  |  0  |  7  |  0 |  0 |  0 |  7 | 0.0000 | 0.0000 | 0.0000 | inconclusive_zero_positive_support |
| Termination         |  0.50  |  3  |  4  |  0 |  0 |  3 |  4 | 0.0000 | 0.0000 | 0.0000 | sufficient_support (N=3)           |
| Legal Compliance    |  0.50  |  4  |  3  |  0 |  0 |  4 |  3 | 0.0000 | 0.0000 | 0.0000 | sufficient_support (N=4)           |
| Liability           |  0.50  |  0  |  7  |  0 |  0 |  0 |  7 | 0.0000 | 0.0000 | 0.0000 | inconclusive_zero_positive_support |
| Payment / Financial |  0.50  |  0  |  7  |  0 |  0 |  0 |  7 | 0.0000 | 0.0000 | 0.0000 | inconclusive_zero_positive_support |
+---------------------+--------+-----+-----+----+----+----+----+--------+--------+--------+------------------------------------+
```

- **Macro F1 (All Categories)**: `0.0000` (Unweighted mean across all 5 categories; zero-support categories contribute 0.0).
- **Macro F1 (Evaluable Categories: Termination & Legal Compliance)**: `0.0000`.
- **Micro F1**: `0.0000`.
- **Hamming Loss**: `0.2000` (7 errors out of 35 binary decisions).
- **Specificity (True Negative Rate)**: **100.0%** (28 / 28 negative decisions across all categories were correctly predicted negative; zero false alarms).

### 4.3 Baseline Model Comparison (TF-IDF + Logistic Regression)
On the exact same test split, the deterministic TF-IDF baseline yielded:
- **Baseline Macro F1 (All Categories)**: `0.1600`
- **Baseline Macro F1 (Evaluable Categories)**: `0.4000`
- **Baseline Micro F1**: `0.4444`
- **Baseline True Positives**: Detected 2 positives in Legal Compliance (`CAN-030`, `CAN-031`) with 2 false positives.

### 4.4 Comparison with Prior Model Artifact
The prior model artifact located in `analysis/models/legal_bert_model/` was trained against dataset snapshot `0048f456...` (pre-freeze v3.0). On the same 7 test records, it likewise produced 0 true positives at threshold 0.50, demonstrating that the small training volume ($N=44$, with 3–5 positives per class) is insufficient for BERT-base to cross the default 0.50 decision boundary without calibrated thresholds.

---

## 5. Honest Interpretation & Small-Data Evaluation Boundaries

1. **Pipeline Verification vs. Model Capability**:
   - The training pipeline **runs reliably, deterministically, and end-to-end**.
   - However, the trained model **cannot be claimed accurate or production-ready** based on this experiment.
2. **Inconclusive Categories**:
   - **Privacy**, **Liability**, and **Payment / Financial** contain **zero positive ground-truth examples** in the held-out test split.
   - For these three categories, true positive recall and F1 are mathematically undefined. The 0.0000 score reflects the absence of test positives, not necessarily a total lack of model capability.
3. **Evaluable Categories**:
   - **Termination** ($N=3$ positives) and **Legal Compliance** ($N=4$ positives) have sufficient ground-truth support for empirical evaluation.
   - At threshold 0.50, the model favored conservative predictions (0 false positives, 100% specificity), resulting in false negatives on these classes.
4. **Validation Calibration Gap**:
   - Because the validation split contains only negative examples, empirical threshold calibration cannot be performed without degenerate overfitting to an all-negative distribution.

---

## 6. Implementation Changes & Saved Artifacts

### 6.1 Changes Made
1. **Added `--output-dir` Option**: Enhanced [`analysis/train_legal_bert.py`](file:///c:/ARO/Projects/Smart_Contract_Analyser/analysis/train_legal_bert.py) with a dedicated `--output-dir` CLI argument to support versioned artifact saving.
2. **Preserved Prior Model Checkpoint**: Preserved [`analysis/models/legal_bert_model/`](file:///c:/ARO/Projects/Smart_Contract_Analyser/analysis/models/legal_bert_model/) intact as an older, pre-freeze artifact.
3. **Updated Configuration**: Set `output_dir` to `analysis/models/legal_bert_v3.3.0` in [`analysis/training_config.json`](file:///c:/ARO/Projects/Smart_Contract_Analyser/analysis/training_config.json).

### 6.2 Saved Artifacts in `analysis/models/legal_bert_v3.3.0/`
- `model.safetensors` (438 MB fine-tuned Legal-BERT weights)
- `config.json` (model architecture with multi-label configuration and category mappings)
- `tokenizer.json` & `tokenizer_config.json` (HuggingFace tokenizer files)
- `training_metrics.json` (complete record of dataset SHA-256, seed, split sample IDs, thresholds, and metrics)
- `training_log.txt` (execution log and summary)
- `baseline_metrics.json` (TF-IDF baseline evaluation metrics)

---

## 7. Quality Assurance & Validation Verification

1. **Dataset Integrity Check**:
   ```bash
   python -m analysis.ml_dataset_validator data/ml_candidates/final_dataset.jsonl
   ```
   **Result**: `Is Valid: True`, `Split Ready: True (Split criteria met.)`.
2. **Validator Unit Tests**:
   ```bash
   python -m pytest tests/test_ml_dataset_validator.py
   ```
   **Result**: `18 passed in 0.64s`.
3. **Canonical Hash Verification**:
   - Dataset hash `74464fd132e9268220549adc8e5cfb31d4ca69b9fae203b31ae2924c1500e456` verified intact.
