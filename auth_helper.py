import os
import sys
import json
import subprocess
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets'
]

def print_instructions():
    print("=" * 80)
    print("📢 建立個人 Google API 憑證導引 (無痛破解 0MB 雲端空間限制)")
    print("=" * 80)
    print("由於 Google 的最新安全政策，任何「服務帳戶 (Service Account)」本身的儲存空間上限皆為 0MB。")
    print("為了解鎖無限容量的檔案建立功能，助理必須以您的「個人 Google 帳號」身分來執行 API 呼叫。")
    print("\n請跟隨以下 5 個簡單步驟下載您的 credentials.json：")
    print("-" * 80)
    print("1. 請打開瀏覽器並登入 Google Cloud Console：")
    print("   👉 https://console.cloud.google.com/apis/credentials?project=logical-contact-496003-p1")
    print("2. 點擊上方的 「+ 建立憑證」 (Create Credentials) ➡️ 選擇 「OAuth 用戶端 ID」 (OAuth client ID)。")
    print("3. 設定「應用程式類型」 (Application type) 為：【電腦應用程式】 (Desktop app)。")
    print("4. 名稱可以自由輸入 (例如：Gemma Bot)，然後點擊「建立」。")
    print("5. 建立完成後，點擊該憑證右側的 ⬇️「下載 JSON」 按鈕，並將下載下來的檔案：")
    print("   重新命名為: credentials.json")
    print("   並移動/儲存到此專案根目錄下：")
    print(f"   📂 {os.getcwd()}")
    print("-" * 80)
    print("完成下載後，請重新執行此腳本 (python auth_helper.py)，我將為您自動啟動瀏覽器驗證！")
    print("=" * 80)

def main():
    credentials_path = "credentials.json"
    token_path = "token.json"
    
    if not os.path.exists(credentials_path):
        print_instructions()
        return

    print("🔑 偵測到 credentials.json，正在啟動本地瀏覽器驗證流程...")
    try:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)
        
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            
        print("\n" + "=" * 80)
        print("🎉 驗證成功！本地 token.json 已順利產生！")
        print("=" * 80)
        print(f"檔案位置: {os.path.abspath(token_path)}")
        
        print("\n正在自動將您的權限憑證上傳至 Google Secret Manager 進行安全保護...")
        # 建立或更新 Secret Manager 中的憑證
        secret_name = "GOOGLE_DRIVE_TOKEN"
        project_id = "logical-contact-496003-p1"
        
        # 檢查 Secret 是否已存在
        check_cmd = f"gcloud secrets describe {secret_name} --project={project_id}"
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            # 存在，新增版本
            upload_cmd = f"gcloud secrets versions add {secret_name} --data-file={token_path} --project={project_id}"
            print("🔄 偵測到已有存在的 Secret，正在新增安全版本...")
        else:
            # 不存在，建立並上傳
            create_cmd = f"gcloud secrets create {secret_name} --replication-policy=automatic --project={project_id}"
            subprocess.run(create_cmd, shell=True, capture_output=True)
            upload_cmd = f"gcloud secrets versions add {secret_name} --data-file={token_path} --project={project_id}"
            print("🆕 正在 Secret Manager 中建立 GOOGLE_DRIVE_TOKEN 密鑰並安全上傳...")
            
        upload_result = subprocess.run(upload_cmd, shell=True, capture_output=True, text=True)
        if upload_result.returncode == 0:
            print("\n" + "★" * 80)
            print("🚀 完美成功！個人憑證 GOOGLE_DRIVE_TOKEN 已安全儲存於 Google 雲端密鑰庫！")
            print("★" * 80)
            print("下一步：我將會自動修改 Cloud Run 設定以安全載入此個人憑證！")
        else:
            print(f"❌ 上傳 Secret 失敗: {upload_result.stderr}")
            
    except Exception as e:
        print(f"❌ 驗證過程中發生錯誤: {e}")

if __name__ == '__main__':
    main()
