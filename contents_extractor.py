# 删除和检测目录、
def detect_directory(marking_path):
    with open(marking_path, "r", encoding="utf-8") as f:
        content = f.readlines()
        
