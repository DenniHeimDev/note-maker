from config_helpers import ENV_PATH, USER_CONFIG_DIR
import os

print(f"User Config Dir: {USER_CONFIG_DIR}")
print(f"Env Path: {ENV_PATH}")

# Check if directory exists (it should have been created by the module import)
if USER_CONFIG_DIR.exists():
    print("User Config Dir exists.")
else:
    print("User Config Dir does NOT exist.")

# Simulate writing to it
try:
    test_file = USER_CONFIG_DIR / "test_write.txt"
    test_file.write_text("test")
    print("Write permission confirmed.")
    test_file.unlink()
except Exception as e:
    print(f"Write failed: {e}")
