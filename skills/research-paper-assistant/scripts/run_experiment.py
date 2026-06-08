"""
논문 실험 파이프라인 — 재현성 보장
Train:Test = 7:3 시간 분리 + Train 내 TimeSeriesSplit 5-fold CV
"""
import random, os, json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit, cross_validate
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ─── 재현성 ──────────────────────────────────────────────────────────────────
def set_seed(seed: int = 42):
    random.seed(seed); np.random.seed(seed)
    try:
        import torch; torch.manual_seed(seed)
        if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    except ImportError: pass

set_seed(42)  # ← 실험 최상단에서 반드시 1회 호출

# ─── 시간 기준 7:3 분리 ───────────────────────────────────────────────────────
def time_based_split(df: pd.DataFrame, train_ratio: float = 0.70):
    """random split 절대 금지 → 시간 순서 기반 7:3"""
    n = len(df); split = int(n * train_ratio)
    return df.iloc[:split], df.iloc[split:]

# ─── 평가 지표 ────────────────────────────────────────────────────────────────
def compute_metrics(y_true, y_pred, label="Test") -> dict:
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    mape = float(np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + 1e-8))) * 100)
    print(f"[{label:10s}] MAE={mae:.4f}  RMSE={rmse:.4f}  R²={r2:.4f}  MAPE={mape:.2f}%")
    return {"label": label, "mae": mae, "rmse": rmse, "r2": r2, "mape": mape}

# ─── 실험 파이프라인 ──────────────────────────────────────────────────────────
def run_regression_experiment(
    filepath: str,
    target_col: str,
    feat_cols: list,
    freq: str = "5min",
    n_cv_folds: int = 5,
) -> dict:
    """
    회귀 모델 비교 실험 — 논문 Table 1 생성용
    - Train:Test = 7:3 시간 기준 고정 분리
    - Train 내 TimeSeriesSplit 5-fold CV → 모델 선택 및 하이퍼파라미터 탐색
    - 최종 성능은 Test 세트로 보고
    """
    df = pd.read_csv(filepath, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    df = df.resample(freq).mean().interpolate(method="linear", limit=5).dropna()

    train_df, test_df = time_based_split(df, train_ratio=0.70)
    print(f"\nTrain: {len(train_df):,}행  |  Test: {len(test_df):,}행  (7:3 시간 분리)")

    # Train 기준 정규화 (leakage 방지)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(train_df[feat_cols].values)
    X_test  = scaler.transform(test_df[feat_cols].values)
    y_train = train_df[target_col].values
    y_test  = test_df[target_col].values

    tscv = TimeSeriesSplit(n_splits=n_cv_folds)

    def cv_then_test(model, name):
        """5-fold CV 평균(Val) + 최종 Test 성능"""
        cv_res = cross_validate(
            model, X_train, y_train, cv=tscv,
            scoring=["neg_mean_absolute_error", "neg_root_mean_squared_error", "r2"],
            return_train_score=False,
        )
        cv_mae  = -cv_res["test_neg_mean_absolute_error"].mean()
        cv_rmse = -cv_res["test_neg_root_mean_squared_error"].mean()
        cv_r2   =  cv_res["test_r2"].mean()
        print(f"[{name} CV-5fold] MAE={cv_mae:.4f}  RMSE={cv_rmse:.4f}  R²={cv_r2:.4f}")

        model.fit(X_train, y_train)
        test_m = compute_metrics(y_test, model.predict(X_test), f"{name} Test")
        return {
            "cv_mae": cv_mae, "cv_rmse": cv_rmse, "cv_r2": cv_r2,
            **{f"test_{k}": v for k, v in test_m.items() if k != "label"},
        }

    results = {}

    print("\n[Model] Ridge Regression")
    results["Ridge"] = cv_then_test(Ridge(alpha=1.0, random_state=42), "Ridge")

    print("\n[Model] Random Forest")
    results["RandomForest"] = cv_then_test(
        RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1), "RandomForest"
    )

    # Feature Importance (Ablation용)
    rf_final = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf_final.fit(X_train, y_train)
    importance_df = pd.DataFrame({
        "feature": feat_cols, "importance": rf_final.feature_importances_,
    }).sort_values("importance", ascending=False)

    out = {
        "experiment_config": {
            "seed": 42, "target": target_col, "freq": freq,
            "train_ratio": 0.70, "test_ratio": 0.30,
            "cv_strategy": f"TimeSeriesSplit(n_splits={n_cv_folds})",
        },
        "results": results,
        "feature_importance": importance_df.to_dict("records"),
    }
    os.makedirs("results", exist_ok=True)
    with open("results/regression_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # 논문용 결과 테이블
    print("\n" + "="*70)
    print("  논문 Table 1: 모델 비교 결과")
    print("="*70)
    print(f"  {'Model':20s} {'CV MAE':>9} {'CV RMSE':>9} {'CV R²':>8} {'Test MAE':>9} {'Test R²':>8}")
    print("  " + "-"*66)
    for name, m in results.items():
        print(f"  {name:20s} {m['cv_mae']:9.4f} {m['cv_rmse']:9.4f} {m['cv_r2']:8.4f} "
              f"{m['test_mae']:9.4f} {m['test_r2']:8.4f}")
    print("="*70)
    print("  CV: TimeSeriesSplit 5-fold on Train (70%)  |  최종 평가: Test (30%)")

    return out


def run_ablation_study(
    train_df, test_df, target_col: str,
    feat_groups: dict,
    n_cv_folds: int = 5,
) -> dict:
    """
    Ablation Study — 피처 그룹 제거 실험
    각 구성마다 5-fold CV 수행 후 Test 보고
    feat_groups: {"Full": [전체 피처], "w/o lag": [lag 제외 피처], ...}
    """
    tscv = TimeSeriesSplit(n_splits=n_cv_folds)
    results = {}
    for name, feats in feat_groups.items():
        scaler = StandardScaler()
        X_tr = scaler.fit_transform(train_df[feats].values)
        X_te = scaler.transform(test_df[feats].values)
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        cv_res = cross_validate(rf, X_tr, train_df[target_col].values, cv=tscv,
                                scoring=["neg_mean_absolute_error"])
        cv_mae = -cv_res["test_neg_mean_absolute_error"].mean()
        rf.fit(X_tr, train_df[target_col].values)
        m = compute_metrics(test_df[target_col].values, rf.predict(X_te), name)
        results[name] = {**m, "cv_mae": cv_mae}

    print("\n  논문 Table 2: Ablation Study")
    print(f"  {'Config':25s} {'CV MAE':>9} {'Test MAE':>9} {'Test MAPE':>10}")
    print("  " + "-"*56)
    for name, m in results.items():
        print(f"  {name:25s} {m['cv_mae']:9.4f} {m['mae']:9.4f} {m['mape']:9.2f}%")
    return results
