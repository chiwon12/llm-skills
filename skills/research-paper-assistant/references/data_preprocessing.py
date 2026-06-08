"""스마트팜 센서 데이터 전처리 — 결측·클리핑·피처·분리·정규화"""
import pandas as pd, numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit

SENSOR_RANGES = {
    "indoor_temp":(-10,60),"outdoor_temp":(-30,45),"indoor_humidity":(0,100),
    "outdoor_humidity":(0,100),"co2":(300,5000),"solar_radiation":(0,1200),
    "soil_moisture":(0,100),"soil_ec":(0,5),"soil_temp":(0,50),"wind_speed":(0,50),
}

def load_sensor_data(filepath:str, freq:str="5min")->pd.DataFrame:
    df=pd.read_csv(filepath,parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    df=df[~df.index.duplicated(keep="first")]
    return df.resample(freq).mean()

def handle_missing_values(df:pd.DataFrame, short_gap:int=5)->pd.DataFrame:
    """점 결측(≤short_gap) → 선형보간 / 구간 결측(>short_gap) → 제거"""
    for col in df.columns:
        mask=df[col].isna()
        if not mask.any(): continue
        groups=(mask!=mask.shift()).cumsum()
        run_len=mask.groupby(groups).transform("sum")
        df[col]=df[col].interpolate(method="linear",limit=short_gap)
        df.loc[mask&(run_len>short_gap),col]=np.nan
    return df.dropna()

def clip_sensor_outliers(df:pd.DataFrame)->pd.DataFrame:
    df=df.copy()
    for col,(lo,hi) in SENSOR_RANGES.items():
        if col in df.columns: df[col]=df[col].clip(lo,hi)
    return df

def add_time_features(df:pd.DataFrame)->pd.DataFrame:
    df=df.copy(); hour=df.index.hour; doy=df.index.dayofyear
    df["hour_sin"]=np.sin(2*np.pi*hour/24); df["hour_cos"]=np.cos(2*np.pi*hour/24)
    df["doy_sin"] =np.sin(2*np.pi*doy/365); df["doy_cos"] =np.cos(2*np.pi*doy/365)
    df["is_daytime"]=((hour>=6)&(hour<=20)).astype(int)
    return df

def add_lag_features(df,target_col,lags=None):
    if lags is None: lags=[1,6,12,24,48,288]
    df=df.copy()
    for l in lags: df[f"{target_col}_lag{l}"]=df[target_col].shift(l)
    return df.dropna()

def add_rolling_features(df,target_col,windows=None):
    if windows is None: windows=[6,12,24,48]
    df=df.copy()
    for w in windows:
        df[f"{target_col}_rmean_{w}"]=df[target_col].rolling(w).mean()
        df[f"{target_col}_rstd_{w}"] =df[target_col].rolling(w).std()
    return df.dropna()

def time_based_split(df: pd.DataFrame, train_ratio: float = 0.70):
    """
    Train:Test = 7:3 시간 기준 분리 (random split 절대 금지)
    Val은 별도 고정 분리 없이 Train 내 5-fold CV로 대체
    """
    n = len(df)
    split = int(n * train_ratio)
    train_df, test_df = df.iloc[:split], df.iloc[split:]
    print(f"Train: {train_df.index[0].date()} ~ {train_df.index[-1].date()} ({len(train_df):,}행)")
    print(f"Test:  {test_df.index[0].date()}  ~ {test_df.index[-1].date()}  ({len(test_df):,}행)")
    return train_df, test_df

def get_timeseries_cv(n_splits: int = 5) -> TimeSeriesSplit:
    """
    TimeSeriesSplit(n_splits=5) — 시계열 순서를 보존하는 5-fold CV
    fold i: train = 처음부터 i번째 구간 / val = i+1번째 구간 (미래 누수 없음)
    """
    return TimeSeriesSplit(n_splits=n_splits)

def preprocess_pipeline(filepath, target_col, freq="5min"):
    df=load_sensor_data(filepath,freq)
    df=handle_missing_values(df); df=clip_sensor_outliers(df)
    df=add_time_features(df); df=add_lag_features(df,target_col)
    df=add_rolling_features(df,target_col)
    feat_cols=[c for c in df.columns if c!=target_col]
    full=pd.DataFrame(np.c_[df[feat_cols].values,df[target_col].values],
                      index=df.index,columns=feat_cols+[target_col])

    train_df, test_df = time_based_split(full, train_ratio=0.70)

    # Scaler는 Train 전용 fit (leakage 방지)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(train_df[feat_cols].values)
    X_test  = scaler.transform(test_df[feat_cols].values)

    return {
        "X_train": X_train, "X_test": X_test,
        "y_train": train_df[target_col].values,
        "y_test":  test_df[target_col].values,
        "train_df": train_df, "test_df": test_df,
        "scaler": scaler, "feature_names": feat_cols,
        "cv": get_timeseries_cv(n_splits=5),
    }
