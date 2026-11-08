from huggingface_hub import hf_hub_download
from pathlib import Path
import shutil
p=Path(__file__).parent/"model"
p.mkdir(exist_ok=True)
f=hf_hub_download("rasbt/ai-text-detector-logreg", "logreg-ai-detector.joblib")
shutil.copy2(f, p/"logreg-ai-detector.joblib")
print("Model downloaded for server-side inference:", p/"logreg-ai-detector.joblib")
