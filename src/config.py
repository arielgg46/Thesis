import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAST_DOWNWARD_PATH = r"D:\fast-downward-24.06.1"
VAL_PATH = r"C:\Tools\Val-20211204.1-win64\bin\Validate.exe"
RESULT_ROOT = os.path.join(BASE_DIR, "results")
INSIGHTS_LIMIT = 10
OPERATIONS_LIMIT = 4
EXP_TRAINING_TRIALS = 3
LLM_DEFAULT_MODEL = "accounts/fireworks/models/deepseek-v3"
EXP_FEWSHOTS = 2
LLM_QUERY_TRY_LIMIT_PER_KEY = 3
TRAINING_SUBSET = "train4"
TESTING_SUBSET = "test4"