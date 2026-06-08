"""논문용 평가 지표 + Figure 생성"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib; matplotlib.rcParams["axes.unicode_minus"]=False
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score,classification_report

def compute_metrics(y_true,y_pred,label="Test")->dict:
    mae=mean_absolute_error(y_true,y_pred)
    rmse=np.sqrt(mean_squared_error(y_true,y_pred))
    r2=r2_score(y_true,y_pred)
    mape=float(np.mean(np.abs((y_true-y_pred)/(np.abs(y_true)+1e-8)))*100)
    print(f"[{label}] MAE={mae:.4f}  RMSE={rmse:.4f}  R²={r2:.4f}  MAPE={mape:.2f}%")
    return {"mae":mae,"rmse":rmse,"r2":r2,"mape":mape}

def print_comparison_table(results:dict):
    """논문 Table 1 형식 출력"""
    print(f"\n{'Model':22s}{'MAE':>9}{'RMSE':>9}{'R²':>9}{'MAPE':>9}")
    print("-"*50)
    for name,m in results.items():
        print(f"{name:22s}{m['mae']:9.4f}{m['rmse']:9.4f}{m['r2']:9.4f}{m['mape']:8.2f}%")

def plot_prediction(y_true,y_pred,title="예측 vs 실제",save_path=None):
    """Figure 2: 시계열 비교 + 산점도"""
    fig,axes=plt.subplots(1,2,figsize=(14,5))
    n=min(200,len(y_true))
    axes[0].plot(y_true[:n],label="실제",alpha=0.8,color="#065A82")
    axes[0].plot(y_pred[:n],label="예측",alpha=0.8,color="#F96167",ls="--")
    axes[0].set_title(f"{title} (앞 {n}포인트)"); axes[0].legend(); axes[0].grid(alpha=0.3)
    lo,hi=min(y_true.min(),y_pred.min()),max(y_true.max(),y_pred.max())
    axes[1].scatter(y_true,y_pred,alpha=0.3,s=8,color="#028090")
    axes[1].plot([lo,hi],[lo,hi],"r--",label="완벽 예측")
    axes[1].set_xlabel("실제값"); axes[1].set_ylabel("예측값"); axes[1].legend()
    plt.tight_layout()
    if save_path: plt.savefig(save_path,dpi=300,bbox_inches="tight"); print(f"저장: {save_path}")
    plt.show()

def plot_ablation(ablation_results:dict,metric="mae",save_path=None):
    """Figure 3: Ablation Study 막대그래프"""
    names=list(ablation_results.keys()); vals=[ablation_results[n][metric] for n in names]
    colors=["#028090" if n=="Full model" else "#A8DADC" for n in names]
    plt.figure(figsize=(10,5))
    bars=plt.bar(names,vals,color=colors,edgecolor="white")
    plt.bar_label(bars,fmt="%.4f",padding=3)
    plt.ylabel(metric.upper()); plt.title("Ablation Study"); plt.xticks(rotation=15)
    plt.tight_layout()
    if save_path: plt.savefig(save_path,dpi=300,bbox_inches="tight")
    plt.show()

def plot_feature_importance(model,feature_names,top_n=15,save_path=None):
    """Figure 4: Feature Importance"""
    imp=model.feature_importances_; idx=imp.argsort()[-top_n:][::-1]
    plt.figure(figsize=(10,6))
    plt.barh(range(top_n),imp[idx],color="#028090")
    plt.yticks(range(top_n),[feature_names[i] for i in idx])
    plt.xlabel("중요도"); plt.title(f"Top {top_n} Feature Importance")
    plt.tight_layout()
    if save_path: plt.savefig(save_path,dpi=300,bbox_inches="tight")
    plt.show()
