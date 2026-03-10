import os
path = os.path.join("fuentes", "PAGTOTAL_202603101502.csv")
size = os.path.getsize(path)
print(f"Size: {size/1024/1024:.1f} MB")
