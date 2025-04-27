import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAST_DOWNWARD_PATH = r"D:\fast-downward-24.06.1"
VAL_PATH = r"C:\Tools\Val-20211204.1-win64\bin\Validate.exe"
RESULT_ROOT = os.path.join(BASE_DIR, "results")
API_KEY = os.getenv("FIREWORKS_API_KEY", "fw_3Zi3HreZrSk69MEpu78Wa7kP")
